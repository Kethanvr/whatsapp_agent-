"""
Web Search Specialist Agent - Sub-Agent for Information Retrieval
- Real-time Web Search
- News & Current Events
- Fact Checking
- Information Aggregation
"""

import asyncio
import requests
import json
from typing import Dict, List, Optional, Any
from loguru import logger
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    import google.generativeai as genai
except ImportError:
    logger.warning("google-generativeai not installed")
    genai = None

from ..base_agent import BaseAgent, AgentResponse, AgentRequest
from config.settings import settings

@dataclass
class SearchQuery:
    """Represents a search query"""
    query: str
    search_type: str  # 'general', 'news', 'academic', 'local', 'images'
    time_filter: Optional[str] = None  # 'day', 'week', 'month', 'year'
    region: Optional[str] = None
    max_results: int = 5

class WebSearchAgent(BaseAgent):
    """Specialized agent for web search and information retrieval"""
    
    def __init__(self, agent_config=None):
        config = agent_config or {
            "id": "web_search",
            "name": "Web Search Specialist",
            "description": "Expert in real-time information retrieval and web search",
            "capabilities": ["web_search", "news", "current_events", "fact_checking"],
            "enabled": True
        }
        super().__init__(config)
        self.setup_search_apis()
        
    def setup_search_apis(self):
        """Setup search API configurations"""
        # Google Search API (requires API key)
        self.google_api_key = getattr(settings, 'google_search_api_key', None)
        self.google_cx = getattr(settings, 'google_search_cx', None)
        
        # SerpAPI (alternative)
        self.serpapi_key = getattr(settings, 'serpapi_key', None)
        
        # Search configuration
        self.search_enabled = bool(self.google_api_key or self.serpapi_key)
        
        if genai and settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.search_model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config={
                    'temperature': 0.3,  # Lower for factual accuracy
                    'top_p': 0.8,
                    'max_output_tokens': 1024,
                },
                # Enable Google Search grounding
                tools=[genai.protos.Tool(google_search_retrieval=genai.protos.GoogleSearchRetrieval())]
            )
        
        logger.info(f"🔍 Web Search configured - APIs available: {self.search_enabled}")
    
    async def process_message(self, query: str, session_id: str, **kwargs) -> AgentResponse:
        """Process search requests"""
        try:
            # Parse search request
            search_query = self._parse_search_request(query, kwargs)
            
            # Perform search
            if search_query.search_type == 'news':
                results = await self._search_news(search_query)
            elif search_query.search_type == 'academic':
                results = await self._search_academic(search_query)
            elif search_query.search_type == 'local':
                results = await self._search_local(search_query)
            else:
                results = await self._search_general(search_query)
            
            # Format response
            formatted_response = self._format_search_results(results, query)
            
            return AgentResponse(
                success=True,
                response=formatted_response,
                agent_id=self.agent_id,
                confidence=0.9,
                metadata={
                    "search_type": search_query.search_type,
                    "results_count": len(results.get('items', [])),
                    "search_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Web Search error: {e}")
            return AgentResponse(
                success=False,
                response="I encountered an error searching for information. Please try again.",
                agent_id=self.agent_id,
                error=str(e)
            )
    
    def _parse_search_request(self, query: str, kwargs: Dict) -> SearchQuery:
        """Parse request to determine search parameters"""
        query_lower = query.lower()
        
        # Determine search type
        if any(word in query_lower for word in ['news', 'latest', 'recent', 'breaking', 'headlines']):
            search_type = 'news'
            time_filter = 'week'
        elif any(word in query_lower for word in ['research', 'study', 'academic', 'paper', 'journal']):
            search_type = 'academic'
            time_filter = 'year'
        elif any(word in query_lower for word in ['near me', 'local', 'nearby', 'location']):
            search_type = 'local'
            time_filter = None
        else:
            search_type = 'general'
            time_filter = 'month'
        
        # Extract time filter from query
        if 'today' in query_lower or 'today\'s' in query_lower:
            time_filter = 'day'
        elif 'this week' in query_lower:
            time_filter = 'week'
        elif 'this month' in query_lower:
            time_filter = 'month'
        
        return SearchQuery(
            query=query,
            search_type=search_type,
            time_filter=time_filter,
            max_results=kwargs.get('max_results', 5)
        )
    
    async def _search_general(self, search_query: SearchQuery) -> Dict:
        """Perform general web search"""
        try:
            # Use Gemini with Google Search grounding if available
            if hasattr(self, 'search_model'):
                return await self._search_with_gemini(search_query)
            
            # Fallback to Google Custom Search API
            if self.google_api_key and self.google_cx:
                return await self._search_with_google_api(search_query)
            
            # Fallback to SerpAPI
            if self.serpapi_key:
                return await self._search_with_serpapi(search_query)
            
            # Last resort: simulated search with knowledge cutoff warning
            return self._simulate_search(search_query)
            
        except Exception as e:
            logger.error(f"General search error: {e}")
            return {"items": [], "error": str(e)}
    
    async def _search_with_gemini(self, search_query: SearchQuery) -> Dict:
        """Search using Gemini with Google Search grounding"""
        try:
            enhanced_prompt = f"""Search for current information about: {search_query.query}

Please provide:
1. 🔍 **Key Information**: Most important facts and details
2. 📊 **Current Data**: Latest statistics, numbers, or updates
3. 🗓️ **Recent Developments**: What's new or changed recently
4. 🔗 **Sources**: Where this information comes from
5. 💡 **Summary**: Brief overview of findings

Focus on accuracy and cite recent sources when possible."""

            response = self.search_model.generate_content(enhanced_prompt)
            
            if response and response.text:
                return {
                    "items": [{
                        "title": "Real-time Search Results",
                        "snippet": response.text.strip(),
                        "source": "Google Search via Gemini",
                        "displayLink": "gemini-search"
                    }]
                }
            
            return {"items": []}
            
        except Exception as e:
            logger.error(f"Gemini search error: {e}")
            return {"items": [], "error": str(e)}
    
    async def _search_with_google_api(self, search_query: SearchQuery) -> Dict:
        """Search using Google Custom Search API"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': search_query.query,
                'num': search_query.max_results
            }
            
            # Add time filter if specified
            if search_query.time_filter:
                if search_query.time_filter == 'day':
                    params['dateRestrict'] = 'd1'
                elif search_query.time_filter == 'week':
                    params['dateRestrict'] = 'w1'
                elif search_query.time_filter == 'month':
                    params['dateRestrict'] = 'm1'
                elif search_query.time_filter == 'year':
                    params['dateRestrict'] = 'y1'
            
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else {"items": []}
            
        except Exception as e:
            logger.error(f"Google API search error: {e}")
            return {"items": [], "error": str(e)}
    
    async def _search_with_serpapi(self, search_query: SearchQuery) -> Dict:
        """Search using SerpAPI"""
        try:
            url = "https://serpapi.com/search"
            params = {
                'api_key': self.serpapi_key,
                'engine': 'google',
                'q': search_query.query,
                'num': search_query.max_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json() if response.status_code == 200 else {}
            
            # Convert SerpAPI format to Google format
            items = []
            for result in data.get('organic_results', [])[:search_query.max_results]:
                items.append({
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'link': result.get('link', ''),
                    'displayLink': result.get('displayed_link', '')
                })
            
            return {"items": items}
            
        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
            return {"items": [], "error": str(e)}
    
    async def _search_news(self, search_query: SearchQuery) -> Dict:
        """Search for news articles"""
        # Add "news" to query and set recent time filter
        modified_query = SearchQuery(
            query=f"{search_query.query} news",
            search_type='news',
            time_filter='day',
            max_results=search_query.max_results
        )
        return await self._search_general(modified_query)
    
    async def _search_academic(self, search_query: SearchQuery) -> Dict:
        """Search for academic content"""
        # Add academic terms to query
        modified_query = SearchQuery(
            query=f"{search_query.query} research study academic",
            search_type='academic',
            time_filter='year',
            max_results=search_query.max_results
        )
        return await self._search_general(modified_query)
    
    async def _search_local(self, search_query: SearchQuery) -> Dict:
        """Search for local information"""
        # Add location context to query
        modified_query = SearchQuery(
            query=f"{search_query.query} local near me",
            search_type='local',
            time_filter=None,
            max_results=search_query.max_results
        )
        return await self._search_general(modified_query)
    
    def _simulate_search(self, search_query: SearchQuery) -> Dict:
        """Simulate search results when APIs are not available"""
        return {
            "items": [{
                "title": f"Search: {search_query.query}",
                "snippet": f"🔍 I would search for current information about '{search_query.query}', but search APIs are not configured. Please provide Google Search API credentials for real-time results.",
                "source": "Simulated Search",
                "displayLink": "search-unavailable"
            }]
        }
    
    def _format_search_results(self, results: Dict, original_query: str) -> str:
        """Format search results into readable response"""
        items = results.get('items', [])
        
        if not items:
            return f"🔍 I couldn't find current information about '{original_query}'. This might be because:\n• Search APIs are not configured\n• No recent results available\n• Query needs refinement\n\nTry rephrasing your question or ask about something else!"
        
        formatted = f"🔍 **Search Results for:** {original_query}\n\n"
        
        for i, item in enumerate(items[:5], 1):
            title = item.get('title', 'No title')
            snippet = item.get('snippet', 'No description available')
            source = item.get('displayLink', item.get('source', 'Unknown'))
            
            formatted += f"**{i}. {title}**\n"
            formatted += f"📝 {snippet}\n"
            formatted += f"🔗 *Source: {source}*\n\n"
        
        formatted += f"⏰ *Search performed: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        
        return formatted
    
    def can_handle(self, message: str) -> float:
        """Determine if this agent can handle the message"""
        message_lower = message.lower()
        # High confidence for search-related queries
        if any(word in message_lower for word in ['search', 'find', 'latest', 'news', 'current', 'today']):
            return 0.9
        # Medium confidence for information queries
        if any(word in message_lower for word in ['what is', 'who is', 'when', 'where', 'how']):
            return 0.7
        return 0.3
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process agent request (BaseAgent compatibility)"""
        return await self.process_message(request.message, request.session_id)
    
    def get_capabilities(self) -> List[str]:
        """Return search capabilities"""
        return [
            "Real-time Web Search",
            "News & Current Events", 
            "Academic Research",
            "Local Information",
            "Fact Checking",
            "Information Aggregation",
            "Source Verification"
        ] 