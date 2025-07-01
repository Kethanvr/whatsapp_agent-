#!/usr/bin/env python3
"""
Test script for the multi-agent orchestrator
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import AgentOrchestrator

async def test_orchestrator():
    """Test the orchestrator with various queries"""
    
    print("🎯 Testing Agent Orchestrator...")
    
    try:
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        print(f"✅ Orchestrator initialized with {len(orchestrator.agents)} agents")
        
        # Test queries
        test_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?", 
            "Hello! How are you?",
            "Explain quantum computing",
            "What's 2 + 2?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {query} ---")
            
            try:
                response = await orchestrator.process_message(query, f"test_session_{i}")
                
                print(f"🤖 Agent: {response.agent_id}")
                print(f"✅ Success: {response.success}")
                print(f"📊 Confidence: {response.confidence:.2f}")
                print(f"💬 Response: {response.response[:150]}...")
                
                if response.metadata:
                    print(f"📋 Metadata: {response.metadata}")
                    
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        print("\n🎯 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Run the test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(test_orchestrator())
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
    finally:
        loop.close()