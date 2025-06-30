#!/usr/bin/env python
"""
Quick test script to verify WhatsApp message sending
"""

import sys
import os
sys.path.append('.')

from core.whatsapp_client import whatsapp_client
from core.ai_agent import ai_agent

def test_whatsapp_setup():
    """Test the WhatsApp connection and message sending capability"""
    print("🧪 Testing WhatsApp Setup...")
    print("=" * 50)
    
    # Test 1: Bridge Health
    print("1. Testing bridge connection...")
    bridge_healthy = whatsapp_client.health_check()
    if bridge_healthy:
        print("   ✅ Bridge is running")
    else:
        print("   ❌ Bridge is not running")
        print("   💡 Start with: ./start_whatsapp_bridge.sh")
        return False
    
    # Test 2: WhatsApp Connection
    print("2. Testing WhatsApp connection...")
    status = whatsapp_client.connection_status()
    if status.get('connected'):
        print(f"   ✅ WhatsApp connected")
        if 'chat_count' in status:
            print(f"   📊 Chats available: {status['chat_count']}")
    else:
        print("   ❌ WhatsApp not connected")
        print("   💡 Scan QR code in bridge terminal")
        return False
    
    # Test 3: Get Contacts
    print("3. Testing contact retrieval...")
    try:
        chats = whatsapp_client.get_chats(limit=5)
        if chats:
            print(f"   ✅ Found {len(chats)} contacts")
            print("   📋 Sample contacts:")
            for i, chat in enumerate(chats[:3]):
                contact_type = "Group" if chat.is_group else "Personal"
                print(f"      {i+1}. {chat.name} ({contact_type})")
        else:
            print("   ⚠️ No contacts found")
    except Exception as e:
        print(f"   ❌ Error getting contacts: {e}")
        return False
    
    # Test 4: AI Agent
    print("4. Testing AI agent...")
    try:
        test_prompt = "Say hello in one sentence"
        ai_response = ai_agent.get_simple_response(test_prompt)
        if ai_response:
            print(f"   ✅ AI working: {ai_response[:50]}...")
        else:
            print("   ❌ AI not responding")
            return False
    except Exception as e:
        print(f"   ❌ AI Error: {e}")
        return False
    
    print("\n✅ All tests passed! Ready to send messages.")
    return True

def test_send_message_to_self():
    """Test sending a message to yourself (safest test)"""
    print("\n🧪 Testing Message Sending...")
    print("=" * 50)
    
    try:
        # Get your own number/contact
        chats = whatsapp_client.get_chats(limit=20)
        personal_chats = [c for c in chats if not c.is_group]
        
        if not personal_chats:
            print("❌ No personal contacts found for testing")
            return False
        
        # Use first personal contact (often yourself)
        test_contact = personal_chats[0]
        print(f"📱 Test recipient: {test_contact.name}")
        print(f"📱 Test ID: {test_contact.id}")
        
        # Generate AI response
        ai_prompt = "Generate a short test message saying this is a test from your AI assistant dashboard"
        print(f"🤖 AI Prompt: {ai_prompt}")
        
        ai_response = ai_agent.get_simple_response(ai_prompt)
        print(f"🤖 AI Response: {ai_response}")
        
        # Send message
        print("📤 Sending message...")
        success = whatsapp_client.send_message(test_contact.id, ai_response)
        
        if success:
            print("✅ Message sent successfully!")
            print("💡 Check your WhatsApp to see the message")
            return True
        else:
            print("❌ Failed to send message")
            return False
            
    except Exception as e:
        print(f"❌ Send test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 WhatsApp AI Dashboard - Quick Test")
    print("=" * 50)
    
    # Run tests
    if test_whatsapp_setup():
        
        # Ask user if they want to test sending
        response = input("\n📤 Do you want to test message sending? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            test_send_message_to_self()
        else:
            print("✅ Setup test complete. Your dashboard should work now!")
    else:
        print("❌ Setup issues found. Please fix them before using the dashboard.") 