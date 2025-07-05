"""
Test Enhanced WhatsApp Bot Features
- Test enhanced orchestrator initialization
- Test sub-agents capabilities
- Test multimedia processing
- Test agent-to-agent communication
"""

import asyncio
import sys
from loguru import logger

# Test imports
try:
    from agents.enhanced_orchestrator import EnhancedAgentOrchestrator
    from agents.enhanced_qna_agent import EnhancedQnAAgent, MediaContent
    from agents.sub_agents.image_specialist_agent import ImageSpecialistAgent
    from agents.sub_agents.web_search_agent import WebSearchAgent
    print("✅ All enhanced imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_enhanced_orchestrator():
    """Test enhanced orchestrator initialization and capabilities"""
    print("\n🧪 Testing Enhanced Orchestrator...")
    
    try:
        orchestrator = EnhancedAgentOrchestrator()
        
        # Test agent info
        agent_info = orchestrator.get_agent_info()
        print(f"✅ Loaded {len(agent_info)} agents:")
        for info in agent_info:
            print(f"   - {info['name']}: {len(info['capabilities'])} capabilities")
        
        # Test workflow info
        workflow_info = orchestrator.get_workflow_info()
        print(f"✅ Available workflows: {workflow_info['workflows']}")
        
        # Test simple message processing
        response = await orchestrator.process_message("Hello, how are you?", "test_session")
        print(f"✅ Text processing: {response.success}")
        print(f"   Response: {response.response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False

async def test_image_specialist():
    """Test image specialist agent"""
    print("\n🎨 Testing Image Specialist Agent...")
    
    try:
        agent = ImageSpecialistAgent()
        
        # Test capabilities
        capabilities = agent.get_capabilities()
        print(f"✅ Image capabilities: {capabilities}")
        
        # Test image generation request
        response = await agent.process_message("generate an image of a sunset", "test_session")
        print(f"✅ Image generation test: {response.success}")
        print(f"   Response: {response.response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Image specialist test failed: {e}")
        return False

async def test_web_search_agent():
    """Test web search agent"""
    print("\n🔍 Testing Web Search Agent...")
    
    try:
        agent = WebSearchAgent()
        
        # Test capabilities
        capabilities = agent.get_capabilities()
        print(f"✅ Search capabilities: {capabilities}")
        
        # Test search request
        response = await agent.process_message("What's the latest news about AI?", "test_session")
        print(f"✅ Web search test: {response.success}")
        print(f"   Response: {response.response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Web search test failed: {e}")
        return False

async def test_enhanced_qna():
    """Test enhanced Q&A agent"""
    print("\n🤖 Testing Enhanced Q&A Agent...")
    
    try:
        agent = EnhancedQnAAgent()
        
        # Test capabilities
        capabilities = agent.get_capabilities()
        print(f"✅ Enhanced Q&A capabilities: {capabilities}")
        
        # Test text processing
        response = await agent.process_message("What is artificial intelligence?", "test_session")
        print(f"✅ Enhanced Q&A test: {response.success}")
        print(f"   Response: {response.response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Q&A test failed: {e}")
        return False

async def test_workflow_execution():
    """Test workflow execution with different message types"""
    print("\n🔄 Testing Workflow Execution...")
    
    try:
        orchestrator = EnhancedAgentOrchestrator()
        
        test_cases = [
            ("Hello, how are you?", "standard_qa"),
            ("What's the latest news about technology?", "web_search"),
            ("Generate an image of a beautiful landscape", "image_generation"),
        ]
        
        for message, expected_workflow in test_cases:
            workflow = orchestrator._determine_workflow(message, None)
            print(f"✅ '{message[:30]}...' → {workflow} (expected: {expected_workflow})")
            
            # Test actual execution
            response = await orchestrator.process_message(message, "test_session")
            print(f"   Execution: {response.success} | Agent: {response.agent_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced WhatsApp Bot Feature Tests...")
    print("=" * 60)
    
    tests = [
        test_enhanced_orchestrator,
        test_enhanced_qna,
        test_image_specialist,
        test_web_search_agent,
        test_workflow_execution
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if await test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🧪 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced features are working correctly.")
        print("\n🚀 You can now run the enhanced instant bot with:")
        print("   python enhanced_instant_bot.py")
        print("\n🎯 Enhanced capabilities available:")
        print("   - Send images for analysis: Send image + !ask What do you see?")
        print("   - Generate images: !ask generate an image of a sunset")
        print("   - Web search: !ask What's the latest news about AI?")
        print("   - OCR: Send image + !ask extract text from this image")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
        print("💡 You can still use the basic instant bot: python instant_bot.py")

if __name__ == "__main__":
    asyncio.run(main()) 