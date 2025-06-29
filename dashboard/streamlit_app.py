"""
Streamlit Dashboard for WhatsApp AI Assistant
"""
import streamlit as st
import time
import requests
from datetime import datetime, timedelta
import pandas as pd
# from streamlit_autorefresh import st_autorefresh  # Removed for better UX

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
        
        # Auto-refresh toggle removed for better UX
        st.markdown("---")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "💬 Recent Messages", "🚀 Send AI Message", "🧪 Test Agent", "📋 Logs"])
    
    with tab1:
        show_overview()
    
    with tab2:
        show_recent_messages()
    
    with tab3:
        show_send_ai_message()
    
    with tab4:
        show_test_interface()
    
    with tab5:
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

def show_send_ai_message():
    """Send AI-generated messages to WhatsApp contacts"""
    st.header("🚀 Send AI Message to WhatsApp")
    
    st.markdown("""
    Enter a prompt for the AI and send the response directly to any WhatsApp contact or group.
    Perfect for getting AI insights and sharing them instantly!
    """)
    
    # Get available chats for dropdown
    with st.spinner("Loading contacts..."):
        chats = whatsapp_client.get_chats()
    
    # Create chat options with names instead of IDs
    chat_options = {}
    if chats:
        for chat in chats:
            # Use contact name with appropriate icon
            if chat.is_group:
                chat_label = f"🏘️ {chat.name}"
            else:
                # For personal chats, show the contact name (not phone number)
                contact_name = chat.name if chat.name and chat.name != chat.id else f"Contact {chat.id[-4:]}"
                chat_label = f"👤 {contact_name}"
            
            chat_options[chat_label] = chat.id
    
    # Main form
    with st.form("send_ai_message_form"):
        st.subheader("💭 AI Message Setup")
        
        # AI Prompt input
        default_prompt = ""
        if hasattr(st.session_state, 'quick_prompt'):
            default_prompt = st.session_state.quick_prompt
            delattr(st.session_state, 'quick_prompt')
        
        ai_prompt = st.text_area(
            "🤖 Enter your prompt for the AI:",
            value=default_prompt,
            placeholder="Example: What is artificial intelligence and how does it work?",
            height=120,
            help="Ask the AI anything - science, tech, math, creative writing, advice, etc."
        )
        
        # Recipient selection
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if chat_options:
                # Ensure we have a default selection
                chat_keys = list(chat_options.keys())
                selected_chat = st.selectbox(
                    "📱 Choose recipient:",
                    options=chat_keys,
                    index=0,  # Default to first contact
                    help="Select from your WhatsApp contacts and groups"
                )
                
                # Show selected contact info
                if selected_chat:
                    selected_id = chat_options[selected_chat]
                    st.caption(f"Selected: {selected_chat} → {selected_id}")
            else:
                st.warning("⚠️ No chats available. Make sure WhatsApp bridge is connected.")
                selected_chat = None
        
        with col2:
            # Option for manual phone number entry
            manual_mode = st.checkbox("📝 Manual phone", help="Enter phone number manually")
        
        # Manual phone number input (if enabled)
        manual_phone = None
        if manual_mode:
            manual_phone = st.text_input(
                "📞 Phone number:",
                placeholder="+1234567890",
                help="Include country code (e.g., +1234567890)"
            )
        
        # Preview section
        st.subheader("👁️ Preview")
        if ai_prompt:
            with st.expander("📝 AI will process this prompt:", expanded=True):
                st.write(ai_prompt)
        
        # Send button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            send_button = st.form_submit_button(
                "🚀 Generate & Send",
                type="primary",
                use_container_width=True
            )
    
    # Process the form submission
    if send_button:
        # Validation
        if not ai_prompt.strip():
            st.error("❌ Please enter a prompt for the AI!")
            return
        
        # Determine recipient
        recipient_id = None
        recipient_name = None
        if manual_mode and manual_phone:
            # Use manual phone number
            recipient_id = manual_phone.strip()
            recipient_name = f"📱 {manual_phone}"
        elif not manual_mode and selected_chat and chat_options:
            # Use selected chat
            recipient_id = chat_options[selected_chat]
            recipient_name = selected_chat  # This already contains the formatted name with icon
        else:
            st.error("❌ Please select a recipient or enter a phone number!")
            return
        
        # Debug info to show what recipient is selected
        st.info(f"🎯 **Selected Recipient:** {recipient_name}")
        st.info(f"📱 **Recipient ID:** {recipient_id}")
        st.info(f"🔧 **Manual Mode:** {manual_mode}")
        st.info(f"📋 **Available Options:** {len(chat_options) if chat_options else 0} contacts")
        
        # Process the AI request
        st.subheader("🔄 Processing...")
        
        # Step 1: Generate AI response
        with st.spinner("🤖 AI is thinking..."):
            start_time = time.time()
            try:
                ai_response = ai_agent.get_simple_response(ai_prompt)
                ai_time = time.time() - start_time
                
                if not ai_response:
                    st.error("❌ AI failed to generate a response. Please try again.")
                    return
                
                st.success(f"✅ AI response generated in {ai_time:.2f}s")
                
            except Exception as e:
                st.error(f"❌ AI Error: {str(e)}")
                return
        
        # Show AI response
        with st.expander("🤖 AI Response Preview", expanded=True):
            st.info(ai_response)
        
        # Step 2: Send to WhatsApp
        with st.spinner("📱 Sending to WhatsApp..."):
            send_start = time.time()
            try:
                success = whatsapp_client.send_message(recipient_id, ai_response)
                send_time = time.time() - send_start
                
                if success:
                    st.success(f"✅ Message sent successfully in {send_time:.2f}s!")
                    
                    # Show summary
                    st.subheader("📊 Delivery Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("👤 Recipient", recipient_name)
                    with col2:
                        st.metric("⏱️ AI Time", f"{ai_time:.2f}s")
                    with col3:
                        st.metric("📤 Send Time", f"{send_time:.2f}s")
                    
                    # Success message with action suggestion
                    st.info("💡 **Tip:** Check your WhatsApp to see the message delivered!")
                    
                else:
                    st.error("❌ Failed to send message to WhatsApp. Please check your connection.")
                    
            except Exception as e:
                st.error(f"❌ WhatsApp Send Error: {str(e)}")
    
    # Quick action examples
    st.markdown("---")
    st.subheader("💡 Quick Examples")
    
    example_col1, example_col2, example_col3 = st.columns(3)
    
    with example_col1:
        if st.button("🧠 Explain AI", key="example_ai"):
            st.session_state.quick_prompt = "Explain artificial intelligence in simple terms that anyone can understand"
    
    with example_col2:
        if st.button("🌍 Fun Fact", key="example_fact"):
            st.session_state.quick_prompt = "Share an interesting scientific fact about space or the ocean"
    
    with example_col3:
        if st.button("💡 Daily Tip", key="example_tip"):
            st.session_state.quick_prompt = "Give me a useful productivity tip for today"

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
                # Show readable name instead of just ID
                display_name = chat.name if chat.name and chat.name != chat.id else f"Contact {chat.id[-4:]}"
                chat_data.append({
                    "Name": display_name,
                    "Type": "Group" if chat.is_group else "Personal", 
                    "Participants": chat.participant_count or "N/A",
                    "ID": chat.id[:15] + "..." if len(chat.id) > 15 else chat.id  # Shortened ID for reference
                })
            
            st.dataframe(pd.DataFrame(chat_data))
        else:
            st.warning("No chats found or unable to fetch chats")

if __name__ == "__main__":
    main() 