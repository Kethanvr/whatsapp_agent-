"""
Streamlit Dashboard for WhatsApp AI Assistant
"""
import streamlit as st
import time
import requests
from datetime import datetime, timedelta
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# Import core modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.whatsapp_client import whatsapp_client
from core.ai_agent import ai_agent
from core.message_processor import message_processor
from config.settings import settings

# Page config
st.set_page_config(
    page_title="WhatsApp AI Assistant Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main dashboard application"""
    st.title("🤖 WhatsApp AI Assistant Dashboard")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Status
        st.subheader("📊 Status")
        
        # Check MCP server status
        mcp_status = whatsapp_client.health_check()
        status_color = "green" if mcp_status else "red"
        status_text = "Online" if mcp_status else "Offline"
        st.markdown(f"**MCP Server:** :{status_color}[{status_text}]")
        
        # Processor status
        processor_status = message_processor.is_running
        proc_color = "green" if processor_status else "red"
        proc_text = "Running" if processor_status else "Stopped"
        st.markdown(f"**Message Processor:** :{proc_color}[{proc_text}]")
        
        st.markdown("---")
        
        # Settings
        st.subheader("⚙️ Settings")
        st.text(f"Bot Name: {settings.bot_name}")
        st.text(f"Model: {settings.agent_model}")
        st.text(f"Poll Interval: {settings.mcp_poll_interval}s")
        st.text(f"Triggers: {', '.join(settings.trigger_list)}")
        
        # Auto-refresh toggle
        st.markdown("---")
        auto_refresh = st.checkbox("🔄 Auto-refresh (5s)", value=True)
        
    # Auto-refresh
    if auto_refresh:
        st_autorefresh(interval=5000, limit=None, key="main_refresh")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "💬 Recent Messages", "🧪 Test Agent", "📋 Logs"])
    
    with tab1:
        show_overview()
    
    with tab2:
        show_recent_messages()
    
    with tab3:
        show_test_interface()
    
    with tab4:
        show_logs()

def show_overview():
    """Show overview dashboard"""
    st.header("📈 System Overview")
    
    # Get stats
    stats = message_processor.get_stats()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Messages Processed", stats.get("total_messages_processed", 0))
    
    with col2:
        st.metric("Responses Sent", stats.get("total_responses_sent", 0))
    
    with col3:
        st.metric("Errors", stats.get("errors", 0))
    
    with col4:
        uptime = stats.get("uptime_seconds", 0)
        uptime_str = str(timedelta(seconds=int(uptime))) if uptime > 0 else "Not running"
        st.metric("Uptime", uptime_str)
    
    # Charts
    st.subheader("📊 Activity Charts")
    
    # Get recent interactions
    interactions = message_processor.get_recent_interactions(50)
    
    if interactions:
        # Create DataFrame
        df = pd.DataFrame(interactions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Messages over time
        st.subheader("Messages Over Time")
        df_hourly = df.groupby(df['timestamp'].dt.floor('H')).size().reset_index()
        df_hourly.columns = ['Hour', 'Message Count']
        st.line_chart(df_hourly.set_index('Hour'))
        
        # Response time distribution
        st.subheader("Response Time Distribution")
        st.histogram_chart(df['processing_time'])
        
        # Top senders
        st.subheader("Top Senders")
        sender_counts = df['sender'].value_counts().head(10)
        st.bar_chart(sender_counts)
    else:
        st.info("No message interactions yet. Start chatting with the bot!")

def show_recent_messages():
    """Show recent message interactions"""
    st.header("💬 Recent Messages")
    
    # Get recent interactions
    interactions = message_processor.get_recent_interactions(20)
    
    if not interactions:
        st.info("No recent messages. The bot is waiting for conversations!")
        return
    
    # Display messages
    for interaction in reversed(interactions):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Message header
                timestamp = datetime.fromisoformat(interaction['timestamp'])
                st.markdown(f"**{interaction['sender']}** - {timestamp.strftime('%H:%M:%S')}")
                
                # Query and response
                st.markdown(f"🙋 **Query:** {interaction['query']}")
                st.markdown(f"🤖 **Response:** {interaction['response']}")
            
            with col2:
                # Metadata
                st.text(f"⏱️ {interaction['processing_time']:.2f}s")
                status = "✅" if interaction['success'] else "❌"
                st.text(f"Status: {status}")
            
            st.markdown("---")

def show_test_interface():
    """Show AI agent testing interface"""
    st.header("🧪 Test AI Agent")
    
    st.markdown("Test your AI agent responses without sending to WhatsApp:")
    
    # Test form
    with st.form("test_form"):
        test_query = st.text_area(
            "Enter your test message:",
            placeholder="Type a message to test the AI response...",
            height=100
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit = st.form_submit_button("🚀 Test", type="primary")
        
        with col2:
            sender_name = st.text_input("Sender Name (optional)", value="Test User")
    
    # Process test
    if submit and test_query.strip():
        with st.spinner("🤖 Generating response..."):
            start_time = time.time()
            response = message_processor.test_ai_response(test_query)
            processing_time = time.time() - start_time
        
        # Display result
        st.success("✅ Response generated!")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 🤖 AI Response:")
            st.info(response)
        
        with col2:
            st.metric("Processing Time", f"{processing_time:.2f}s")
    
    # Quick test buttons
    st.markdown("### 🎯 Quick Tests")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("❓ Ask a Question"):
            test_query = "What is artificial intelligence?"
            st.session_state.quick_test = test_query
    
    with col2:
        if st.button("👋 Test Greeting"):
            test_query = "Hello! How are you?"
            st.session_state.quick_test = test_query
    
    with col3:
        if st.button("🧮 Test Math"):
            test_query = "What is 15 * 23?"
            st.session_state.quick_test = test_query
    
    # Process quick test
    if hasattr(st.session_state, 'quick_test'):
        query = st.session_state.quick_test
        delattr(st.session_state, 'quick_test')
        
        with st.spinner("🤖 Processing quick test..."):
            response = message_processor.test_ai_response(query)
        
        st.markdown(f"**Query:** {query}")
        st.markdown(f"**Response:** {response}")

def show_logs():
    """Show system logs and debugging info"""
    st.header("📋 System Logs & Debug Info")
    
    # Configuration
    st.subheader("⚙️ Current Configuration")
    config_data = {
        "MCP Server URL": settings.mcp_server_url,
        "Poll Interval": f"{settings.mcp_poll_interval}s",
        "Bot Name": settings.bot_name,
        "Agent Model": settings.agent_model,
        "Max Response Length": settings.max_response_length,
        "Temperature": settings.agent_temperature,
        "Triggers": ", ".join(settings.trigger_list),
        "Group Chats Enabled": settings.enable_group_chats,
        "Personal Chats Enabled": settings.enable_personal_chats,
    }
    
    for key, value in config_data.items():
        st.text(f"{key}: {value}")
    
    st.markdown("---")
    
    # Connection tests
    st.subheader("🔗 Connection Tests")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Test MCP Server"):
            with st.spinner("Testing MCP connection..."):
                status = whatsapp_client.health_check()
            if status:
                st.success("✅ MCP Server is reachable")
            else:
                st.error("❌ Cannot reach MCP Server")
    
    with col2:
        if st.button("Test AI Agent"):
            with st.spinner("Testing AI agent..."):
                try:
                    response = ai_agent.get_simple_response("Test message")
                    st.success("✅ AI Agent is working")
                    st.text(f"Test response: {response[:100]}...")
                except Exception as e:
                    st.error(f"❌ AI Agent error: {str(e)}")
    
    st.markdown("---")
    
    # Chat list
    st.subheader("💬 Available Chats")
    
    if st.button("Refresh Chat List"):
        with st.spinner("Fetching chats..."):
            chats = whatsapp_client.get_chats()
        
        if chats:
            chat_data = []
            for chat in chats:
                chat_data.append({
                    "ID": chat.id,
                    "Name": chat.name,
                    "Type": "Group" if chat.is_group else "Personal",
                    "Participants": chat.participant_count or "N/A"
                })
            
            st.dataframe(pd.DataFrame(chat_data))
        else:
            st.warning("No chats found or unable to fetch chats")

if __name__ == "__main__":
    main() 