#!/usr/bin/env python
"""
Simple MVP WhatsApp Message Sender - No fancy UI, just working functionality
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.whatsapp_client import whatsapp_client
from core.ai_agent import ai_agent

def main():
    st.set_page_config(
        page_title="WhatsApp AI Sender",
        page_icon="📱",
        layout="wide"
    )
    
    st.title("📱 WhatsApp AI Message Sender - MVP")
    
    # Quick connection check
    bridge_healthy = whatsapp_client.health_check()
    wa_status = whatsapp_client.connection_status()
    
    # Status indicators
    col1, col2 = st.columns(2)
    with col1:
        if bridge_healthy:
            st.success("🟢 Bridge: Online")
        else:
            st.error("🔴 Bridge: Offline")
            st.stop()
    
    with col2:
        if wa_status.get('connected'):
            st.success("🟢 WhatsApp: Connected")
        else:
            st.error("🔴 WhatsApp: Not Connected")
            st.info("💡 Scan QR code in bridge terminal")
            st.stop()
    
    st.markdown("---")
    
    # Simple form - NO nested buttons
    with st.form("send_message_form"):
        st.subheader("🤖 AI Message Setup")
        
        # AI Prompt
        ai_prompt = st.text_area(
            "Enter your AI prompt:",
            placeholder="Example: Explain artificial intelligence in simple terms",
            height=100
        )
        
        # Recipient selection
        st.subheader("📱 Select Recipient")
        
        # Get contacts
        try:
            chats = whatsapp_client.get_chats(limit=20)
            if not chats:
                st.error("No contacts found!")
                st.stop()
            
            # Create simple options
            contact_options = {}
            for chat in chats:
                if chat.is_group:
                    label = f"👥 {chat.name}"
                else:
                    phone = chat.id.split('@')[0]
                    label = f"👤 {chat.name} ({phone[-4:]})"
                contact_options[label] = chat.id
            
            selected_contact = st.selectbox(
                "Choose recipient:",
                options=list(contact_options.keys())
            )
            
        except Exception as e:
            st.error(f"Error loading contacts: {e}")
            st.stop()
        
        # Submit button (this is OK inside form)
        send_button = st.form_submit_button("🚀 Generate & Send", type="primary")
    
    # Process form submission OUTSIDE the form
    if send_button:
        # Validation
        if not ai_prompt.strip():
            st.error("❌ Please enter an AI prompt!")
            st.stop()
        
        if not selected_contact:
            st.error("❌ Please select a recipient!")
            st.stop()
        
        # Get selected contact ID
        recipient_id = contact_options[selected_contact]
        
        # Show what we're doing
        st.subheader("📤 Sending Message")
        st.info(f"🎯 **To:** {selected_contact}")
        st.info(f"📱 **ID:** {recipient_id}")
        
        # Step 1: Generate AI response
        with st.spinner("🤖 AI is thinking..."):
            try:
                ai_response = ai_agent.get_simple_response(ai_prompt)
                if not ai_response:
                    st.error("❌ AI failed to generate response")
                    st.stop()
                st.success("✅ AI response generated!")
            except Exception as e:
                st.error(f"❌ AI Error: {e}")
                st.stop()
        
        # Show AI response
        with st.expander("🤖 AI Response", expanded=True):
            st.write(ai_response)
        
        # Step 2: Send to WhatsApp
        with st.spinner("📱 Sending to WhatsApp..."):
            try:
                success = whatsapp_client.send_message(recipient_id, ai_response)
                if success:
                    st.success("✅ Message sent successfully!")
                    st.balloons()
                    st.info("💡 Check your WhatsApp to confirm delivery")
                else:
                    st.error("❌ Failed to send message")
                    st.info("🔧 Check bridge connection and try again")
            except Exception as e:
                st.error(f"❌ Send Error: {e}")

if __name__ == "__main__":
    main() 