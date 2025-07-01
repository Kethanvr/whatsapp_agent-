"""
Streamlit Dashboard for WhatsApp AI Assistant
"""
import streamlit as st
import time
import requests
from datetime import datetime, timedelta
import pandas as pd
import importlib
import sys
# from streamlit_autorefresh import st_autorefresh  # Removed for better UX

# Clear Streamlit cache on each reload to fix update issues
st.cache_data.clear()
st.cache_resource.clear()

# Import core modules with proper reloading
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force reload environment variables
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv('.env', override=True)

# Import and ensure fresh module loading
from config.settings import settings

# Force reload of modules to pick up new methods
try:
    from core import whatsapp_client as wc_module
    from core import message_processor as mp_module
    from core import ai_agent as ai_module
    
    # Reload modules to ensure fresh imports
    importlib.reload(wc_module)
    importlib.reload(mp_module)
    importlib.reload(ai_module)
    
    # Import the actual objects
    from core.whatsapp_client import whatsapp_client
    from core.message_processor import message_processor
    from core.ai_agent import ai_agent
    
    logger = None  # We'll use st.write for logging in streamlit
    
except Exception as e:
    st.error(f"Module import/reload failed: {e}")
    # Fallback imports
    from core.whatsapp_client import whatsapp_client
    from core.message_processor import message_processor
    from core.ai_agent import ai_agent

# Page config
st.set_page_config(
    page_title="WhatsApp AI Assistant Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add auto-refresh controls in sidebar
with st.sidebar:
    st.header("🔄 Dashboard Controls")
    
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        time.sleep(0.1)  # Small delay for smooth refresh
        st.rerun()
    
    manual_refresh = st.button("🔄 Manual Refresh", use_container_width=True)
    if manual_refresh:
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
    
    st.divider()
    
    # Quick connection check
    st.subheader("⚡ Quick Status")
    bridge_status = whatsapp_client.health_check()
    wa_status = whatsapp_client.connection_status()
    
    if bridge_status:
        st.success("🌉 Bridge: Online")
    else:
        st.error("🌉 Bridge: Offline")
    
    if wa_status.get("connected", False):
        st.success("📱 WhatsApp: Connected")
    else:
        st.error("📱 WhatsApp: Disconnected")
        
    # Add refresh timer for auto-refresh
    if auto_refresh:
        with st.container():
            placeholder = st.empty()
            for i in range(30, 0, -1):
                placeholder.metric("⏰ Next refresh", f"{i}s")
                time.sleep(1)
            placeholder.empty()
            st.rerun()

def main():
    """Main Streamlit application"""
    
    # Quick status check at top
    bridge_status = whatsapp_client.health_check()
    wa_status = whatsapp_client.connection_status()
    
    # Show quick start if nothing is connected
    if not bridge_status:
        st.error("🚫 **WhatsApp Bridge Not Running**")
        show_quick_start()
        return
    elif not wa_status.get("connected", False):
        st.warning("📱 **WhatsApp Not Connected** - Bridge is running but WhatsApp needs connection")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", 
        "💬 Recent Messages", 
        "🚀 Send AI Message", 
        "🧪 Test Agent", 
        "📋 Logs",
        "🔗 Connection Help"
    ])
    
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
    
    with tab6:
        show_connection_help()

def show_quick_start():
    """Show quick start guide when bridge is not running"""
    st.header("🚀 Quick Start Guide")
    
    st.markdown("""
    ### Step 1: Start the WhatsApp Bridge
    
    **Choose your operating system:**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🪟 Windows")
        st.code("./start_whatsapp_bridge.bat")
        st.markdown("*Run this in your project folder*")
        
    with col2:
        st.subheader("🐧 Linux/Mac")  
        st.code("./start_whatsapp_bridge.sh")
        st.markdown("*Run this in your project folder*")
    
    st.markdown("""
    ### Step 2: Connect WhatsApp
    
    1. **After starting bridge**, a QR code will appear in your terminal
    2. **Open WhatsApp** on your phone
    3. **Go to:** Settings → Linked Devices → Link a Device  
    4. **Scan the QR code** from your terminal
    5. **Wait for connection** - you'll see "✓ Connected!" message
    
    ### Step 3: Test the System
    
    1. **Refresh this dashboard** - you should see connected status
    2. **Go to "Send AI Message" tab**
    3. **Select a contact** and enter an AI prompt
    4. **Send your first AI message!**
    """)
    
    # Add refresh button
    if st.button("🔄 Check Bridge Status", type="primary", use_container_width=True):
        st.rerun()
    
    # Manual bridge start option (if Go is available)
    with st.expander("🔧 Manual Bridge Start"):
        st.markdown("""
        If the startup scripts don't work, try starting manually:
        
        ```bash
        cd whatsapp-mcp/whatsapp-bridge
        go run main.go
        ```
        
        The bridge should start on port **3334**.
        """)
        
    # Troubleshooting section
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Common Issues:**
        
        1. **"Port already in use"**
           ```bash
           # Windows
           netstat -ano | findstr :3334
           
           # Linux/Mac  
           lsof -ti:3334 | xargs kill
           ```
        
        2. **CGO compilation errors (Windows)**
           - Install TDM-GCC from https://jmeubank.github.io/tdm-gcc/
           - Or set `CGO_ENABLED=0` (may lose some features)
        
        3. **Go not installed**
           - Download from https://golang.org/dl/
           - Follow installation guide for your OS
                 """)

def show_overview():
    """Main dashboard overview"""
    st.header("🤖 WhatsApp AI Agent Dashboard")
    
    # Force refresh connection status every time
    whatsapp_client.session = requests.Session()  # Reset session
    
    # Connection Status Check
    st.subheader("🔗 Connection Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔧 MCP Bridge Status**")
        bridge_healthy = whatsapp_client.health_check()
        if bridge_healthy:
            st.success("✅ Bridge is running")
        else:
            st.error("❌ Bridge is down")
            st.warning("🚨 **Action Required:** Start the WhatsApp bridge")
            with st.expander("🚀 How to start bridge"):
                st.code("./start_whatsapp_bridge.sh  # Linux/Mac")
                st.code("./start_whatsapp_bridge.bat  # Windows")
    
    with col2:
        st.markdown("**📱 WhatsApp Connection**")
        status = whatsapp_client.connection_status()
        
        if status.get("connected", False):
            st.success("✅ Connected to WhatsApp")
            # Show additional connection info if available
            if "phone" in status:
                st.info(f"📞 Phone: {status['phone']}")
        else:
            st.error("❌ Not connected to WhatsApp")
            st.warning("🚨 **Action Required:** Scan QR code to reconnect")
            
            # Enhanced reconnection guide
            with st.expander("📱 **How to Connect WhatsApp**", expanded=True):
                st.markdown("""
                ### Step-by-step connection:
                
                1. **Go to your bridge terminal** (where you started the bridge)
                2. **Look for QR code** in the terminal output
                3. **Open WhatsApp** on your phone
                4. **Go to:** Settings → Linked Devices → Link a Device
                5. **Scan the QR code** shown in your terminal
                6. **Wait for connection** - you'll see "✓ Connected!" message
                7. **Refresh this dashboard** to see updated status
                """)
                
                st.info("💡 **Tip:** The QR code appears when you first start the bridge or after disconnection")
                
                # Add a connection test button
                if st.button("🔄 Test Connection Now"):
                    st.rerun()
    
    # Show connection troubleshooting if both are having issues
    if not bridge_healthy:
        st.error("🔧 **Bridge Connection Required**")
        st.markdown("""
        ### 🚀 Start the WhatsApp Bridge:
        
        **Option 1: Using startup scripts**
        ```bash
        # Windows
        ./start_whatsapp_bridge.bat
        
        # Linux/Mac  
        ./start_whatsapp_bridge.sh
        ```
        
        **Option 2: Manual start**
        ```bash
        cd whatsapp-mcp/whatsapp-bridge
        go run main.go
        ```
        """)
    
    # Module Status Check (Debug Info)
    with st.expander("🔧 **Debug Info** - Module Status", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**WhatsApp Client**")
            if hasattr(whatsapp_client, 'parse_mention_message'):
                st.success("✅ parse_mention_message available")
            else:
                st.error("❌ parse_mention_message missing")
            
            if hasattr(whatsapp_client, 'find_contact_by_name'):
                st.success("✅ find_contact_by_name available")
            else:
                st.error("❌ find_contact_by_name missing")
        
        with col2:
            st.markdown("**Message Processor**")
            if hasattr(message_processor, 'get_recent_interactions'):
                st.success("✅ get_recent_interactions available")
            else:
                st.error("❌ get_recent_interactions missing")
                
            if hasattr(message_processor, 'test_ai_response'):
                st.success("✅ test_ai_response available")
            else:
                st.error("❌ test_ai_response missing")
        
        with col3:
            st.markdown("**AI Agent**")
            if hasattr(ai_agent, 'get_simple_response'):
                st.success("✅ get_simple_response available")
            else:
                st.error("❌ get_simple_response missing")
                
            st.text(f"Model: {getattr(ai_agent, 'model_name', 'Unknown')}")
    
    # Multi-Agent System Status
    st.subheader("🎯 Multi-Agent System")
    
    try:
        agent_info = message_processor.get_agent_info()
        orchestrator_enabled = agent_info.get("orchestrator_enabled", False)
        agents = agent_info.get("agents", [])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if orchestrator_enabled:
                st.success("🎯 **Orchestrator: Active**")
                st.caption("Multi-agent routing enabled")
            else:
                st.warning("🔄 **Orchestrator: Fallback Mode**")
                st.caption("Using single agent")
        
        with col2:
            st.metric("🤖 Active Agents", len(agents))
            if agents:
                agent_names = [agent.get("name", "Unknown") for agent in agents]
                st.caption(", ".join(agent_names))
            else:
                st.caption("Fallback agent only")
        
        with col3:
            processor_stats = message_processor.get_stats()
            orchestrator_responses = processor_stats.get("orchestrator_responses", 0)
            fallback_responses = processor_stats.get("fallback_responses", 0)
            total_ai_responses = orchestrator_responses + fallback_responses
            
            if total_ai_responses > 0:
                orchestrator_percentage = (orchestrator_responses / total_ai_responses) * 100
                st.metric("🎯 Orchestrator Usage", f"{orchestrator_percentage:.1f}%")
                st.caption(f"{orchestrator_responses}/{total_ai_responses} responses")
            else:
                st.metric("🎯 Orchestrator Usage", "0%")
                st.caption("No AI responses yet")
        
        # Show agent details in expandable section
        if agents:
            with st.expander("🤖 **Agent Details**", expanded=False):
                for agent in agents:
                    st.markdown(f"**{agent.get('name', 'Unknown Agent')}**")
                    st.caption(f"ID: {agent.get('id', 'unknown')}")
                    st.caption(f"Description: {agent.get('description', 'No description')}")
                    
                    capabilities = agent.get('capabilities', [])
                    if capabilities:
                        st.caption(f"Capabilities: {', '.join(capabilities)}")
                    
                    st.markdown("---")
        
    except Exception as e:
        st.error(f"❌ **Orchestrator Status Error:** {str(e)}")
        st.caption("Using fallback mode")
    
    # Quick Stats (optimized)
    st.subheader("📊 Chat Stats")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            # Only fetch if connected
            if status.get("connected", False):
                chats = whatsapp_client.get_chats(limit=20)
                st.metric("Total Chats", len(chats))
            else:
                st.metric("Total Chats", "0", help="Connect WhatsApp to see chats")
        except Exception as e:         
            st.metric("Total Chats", "Error", e)
    
    with col2:
        try:
            if status.get("connected", False) and 'chats' in locals():
                personal_chats = [c for c in chats if not c.is_group]
                st.metric("Personal Chats", len(personal_chats))
            else:
                st.metric("Personal Chats", "0", help="Connect WhatsApp to see chats")
        except Exception as e:
            st.metric("Personal Chats", "Error", e)
    
    with col3:
        try:
            if status.get("connected", False) and 'chats' in locals():
                group_chats = [c for c in chats if c.is_group]
                st.metric("Group Chats", len(group_chats))
            else:
                st.metric("Group Chats", "0", help="Connect WhatsApp to see chats")
        except Exception as e:
            st.metric("Group Chats", "Error", e)
    
    with col4:
        bridge_status_text = "🟢 Online" if bridge_healthy else "🔴 Offline"
        wa_status_text = "🟢 Connected" if status.get("connected", False) else "🔴 Disconnected"
        st.metric("Bridge Status", bridge_status_text)
        st.caption(f"WhatsApp: {wa_status_text}")

def show_recent_messages():
    """Show recent message interactions"""
    st.header("💬 Recent Messages")
    
    try:
        # Try to get recent interactions with error handling
        if hasattr(message_processor, 'get_recent_interactions'):
            interactions = message_processor.get_recent_interactions(20)
        else:
            st.error("❌ **Method Error:** get_recent_interactions not available")
            st.warning("🔄 **Try refreshing the page** - the module may need to reload")
            st.info("💡 This might happen after code updates. The method should be available after refresh.")
            return
    except AttributeError as e:
        st.error(f"❌ **AttributeError:** {str(e)}")
        st.warning("🔄 **Module reload needed** - Please refresh the page")
        st.info("💡 **Alternative:** Use the Test Agent tab to test AI responses")
        return
    except Exception as e:
        st.error(f"❌ **Unexpected Error:** {str(e)}")
        st.warning("🔧 **Debug Info:** Check if the message processor is properly initialized")
        return
    
    if not interactions:
        st.info("🤖 **No recent messages yet!**")
        st.markdown("""
        ### 💡 **How to generate interactions:**
        
        1. **Use the 🚀 Send AI Message tab** to send messages to contacts
        2. **Send WhatsApp messages** with triggers like `/ask` or `!ai`
        3. **Test the AI** using the 🧪 Test Agent tab
        
        Messages will appear here once the bot starts processing conversations!
        """)
        return
    
    st.success(f"📊 **Found {len(interactions)} recent interactions**")
    
    # Display messages
    for i, interaction in enumerate(reversed(interactions)):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Message header
                try:
                    timestamp = datetime.fromisoformat(interaction['timestamp'])
                    formatted_time = timestamp.strftime('%H:%M:%S')
                except:
                    formatted_time = "Unknown time"
                
                st.markdown(f"**👤 {interaction.get('sender', 'Unknown')}** - {formatted_time}")
                
                # Query and response
                query = interaction.get('query', 'No query')
                response = interaction.get('response', 'No response')
                
                st.markdown(f"🙋 **Query:** {query}")
                st.markdown(f"🤖 **Response:** {response[:200]}{'...' if len(response) > 200 else ''}")
            
            with col2:
                # Metadata
                processing_time = interaction.get('processing_time', 0)
                st.text(f"⏱️ {processing_time:.2f}s")
                
                success = interaction.get('success', False)
                status = "✅ Sent" if success else "❌ Failed"
                st.text(f"{status}")
                
                # Chat ID for reference
                chat_id = interaction.get('chat_id', 'Unknown')
                st.caption(f"Chat: {chat_id[-10:]}...")
            
            st.markdown("---")
    
    # Show refresh button
    if st.button("🔄 Refresh Messages"):
        st.rerun()

def show_send_ai_message():
    """Send AI-generated messages to WhatsApp contacts"""
    st.header("🚀 Send AI Message to WhatsApp")
    
    # Real-time connection check with auto-refresh
    status = whatsapp_client.connection_status()
    bridge_healthy = whatsapp_client.health_check()
    
    # Connection status banner
    if not bridge_healthy:
        st.error("🔧 **Bridge is not running!**")
        st.warning("Please start the WhatsApp bridge first")
        with st.expander("How to start bridge"):
            st.code("./start_whatsapp_bridge.sh  # Linux/Mac")
            st.code("./start_whatsapp_bridge.bat  # Windows")
        return
    elif not status.get("connected", False):
        st.warning("📱 **WhatsApp is not connected**")
        st.info("Bridge is running, but WhatsApp needs to be connected")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Check Connection Again", type="primary"):
                st.rerun()
        with col2:
            st.button("📱 How to Connect", help="See connection guide in sidebar")
        
        # Show connection guide
        with st.expander("📱 **WhatsApp Connection Guide**", expanded=True):
            st.markdown("""
            ### Quick connection steps:
            1. **Check your bridge terminal** for QR code
            2. **Open WhatsApp** on your phone
            3. **Settings** → **Linked Devices** → **Link a Device**
            4. **Scan the QR code** from terminal
            5. **Wait for "Connected!"** message
            6. **Click "Check Connection Again"** above
            """)
        return
    else:
        # Connected successfully
        st.success("✅ **Ready to send messages!**")
        if "phone" in status:
            st.caption(f"📞 Connected as: {status['phone']}")
    
    # Create tabs for different sending methods
    tab1, tab2 = st.tabs(["📋 Select Recipient", "💬 Mention-Based Messaging"])
    
    with tab1:
        show_traditional_send_message()
    
    with tab2:
        show_mention_based_messaging()

def show_traditional_send_message():
    """Traditional recipient selection method"""
    st.markdown("""
    Enter a prompt for the AI and send the response directly to any WhatsApp contact or group.
    Perfect for getting AI insights and sharing them instantly!
    """)
    
    # Double-check connection (should be connected if we reach here)
    status = whatsapp_client.connection_status()
    if not status.get("connected", False):
        st.error("❌ **Connection lost!**")
        if st.button("🔄 Refresh Page"):
            st.rerun()
        return
    
    # Load contacts with recent recipients prioritized (optimized)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("👥 Recent Contacts")
        with st.spinner("Loading recent contacts..."):
            # Limit to 10 recent contacts for performance
            recent_chats = whatsapp_client.get_recent_recipients(limit=10)
        
        recent_options = {}
        if recent_chats:
            for chat in recent_chats:
                phone = chat.id.split('@')[0]
                if chat.is_group:
                    label = f"👥 {chat.name} ({phone[-4:]}) | {phone}"
                else:
                    if chat.name and not chat.name.isdigit() and chat.name != phone:
                        label = f"👤 {chat.name} ({phone[-4:]}) | {phone}"
                    else:
                        label = f"📞 {phone}"

                recent_options[label] = chat.id
    
    with col2:
        st.subheader("📋 All Contacts")
        with st.spinner("Loading contacts..."):
            # Limit to 30 contacts for performance
            all_chats = whatsapp_client.get_chats(limit=30)
        
        all_options = {}
        if all_chats:
            for chat in all_chats:
                phone = chat.id.split('@')[0]
                if chat.is_group:
                    chat_label = f"👥 {chat.name} ({phone[-4:]}) | {phone}"
                else:
                    if chat.name and not chat.name.isdigit() and chat.name != phone:
                        chat_label = f"👤 {chat.name} ({phone[-4:]}) | {phone}"
                    else:
                        chat_label = f"📞 {phone}"
                
                all_options[chat_label] = chat.id
    
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
        
        # Show helpful examples if no input (but NO buttons inside form)
        if not ai_prompt.strip():
            st.info("💡 **Example prompts to try:**")
            st.markdown("""
            - "Explain artificial intelligence in simple terms"
            - "Share an interesting scientific fact about space"
            - "Give me a useful productivity tip for today"
            - "What is machine learning and how does it work?"
            """)
            st.caption("👆 Copy and paste any of these examples above")
        
        # Recipient selection with tabs for recent vs all contacts
        st.subheader("📱 Select Recipient")
        
        contact_tab1, contact_tab2, contact_tab3 = st.tabs(["🕒 Recent", "📋 All Contacts", "📝 Manual"])
        
        selected_chat = None
        selected_id = None
        
        with contact_tab1:
            if recent_options:
                recent_keys = list(recent_options.keys())
                selected_recent = st.selectbox(
                    "Choose from recent conversations:",
                    options=recent_keys,
                    index=None,
                    placeholder="Select a recent contact",
                    help="Contacts you've messaged recently",
                    key="recent_select"
                )
                if selected_recent:
                    selected_chat = selected_recent
                    selected_id = recent_options[selected_recent]
            else:
                st.info("📭 No recent conversations found")
        
        with contact_tab2:
            if all_options:
                all_keys = list(all_options.keys())
                selected_all = st.selectbox(
                    "Choose from all contacts:",
                    options=all_keys,
                    index=None,
                    placeholder="Select a contact",
                    help="All available WhatsApp contacts and groups",
                    key="all_select"
                )
                if selected_all:
                    selected_chat = selected_all
                    selected_id = all_options[selected_all]
            else:
                st.warning("⚠️ No contacts available. Make sure WhatsApp bridge is connected.")
        
        with contact_tab3:
            manual_phone = st.text_input(
                "📞 Phone number:",
                placeholder="+919876543210 or 919876543210@s.whatsapp.net",
                help="Enter phone number with country code"
            )
            if manual_phone:
                if '@' not in manual_phone:
                    # Auto-format phone number
                    clean_phone = manual_phone.replace('+', '').replace('-', '').replace(' ', '')
                    manual_phone = f"{clean_phone}@s.whatsapp.net"
                selected_chat = f"📱 Manual: {manual_phone}"
                selected_id = manual_phone
        
        # Show selection preview
        if selected_chat and selected_id:
            is_group = selected_id.endswith('@g.us')
            contact_type = "👥 WhatsApp Group" if is_group else "👤 Individual Contact"
            
            st.success(f"✅ **Selected:** {selected_chat}")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.caption(f"📱 **WhatsApp ID:** {selected_id}")
            with col2:
                if is_group:
                    st.warning(f"{contact_type}")
                else:
                    st.info(f"{contact_type}")
        
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
        # Better validation with specific error messages
        if not ai_prompt.strip():
            st.error("❌ **AI Prompt is required!** Please enter what you want the AI to respond about.")
            st.info("💡 **Example:** 'What is artificial intelligence and how does it work?'")
            return
        
        if not selected_chat or not selected_id:
            st.error("❌ **Recipient is required!** Please select a contact from one of the tabs above.")
            st.info("💡 **Tip:** Use the Recent, All Contacts, or Manual tab to choose someone")
            return
        
        process_traditional_send(ai_prompt, selected_chat, selected_id, recent_options, all_options)

def show_mention_based_messaging():
    """Mention-based messaging where users type @name followed by message"""
    st.markdown("""
    🎯 **Mention-Based Messaging**
    
    Type your message starting with `@ContactName` followed by your prompt. The AI will generate a response and send it to that contact.
    
    **Examples:**
    - `@John What's the weather like today?`
    - `@Mom Can you explain quantum physics in simple terms?`
    - `@Sarah Send me a motivational quote`
    """)
    
    # Double-check connection (should be connected if we reach here)
    status = whatsapp_client.connection_status()
    if not status.get("connected", False):
        st.error("❌ **Connection lost!**")
        if st.button("🔄 Refresh Page", key="mention_refresh"):
            st.rerun()
        return
    
    with st.form("mention_message_form"):
        st.subheader("💬 Compose Message")
        
        message_input = st.text_area(
            "📝 Type your message:",
            placeholder="@ContactName Ask the AI about artificial intelligence and how it works",
            height=150,
            help="Start with @ContactName followed by your AI prompt"
        )
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            parse_button = st.form_submit_button(
                "🔍 Parse & Preview",
                type="primary",
                use_container_width=True
            )
    
    # Parse the message
    if parse_button and message_input.strip():
        try:
            # Parse the mention message using the global whatsapp_client
            mentioned_name, clean_message = whatsapp_client.parse_mention_message(message_input)
            
            if not mentioned_name:
                st.error("❌ No mention found! Please start your message with @ContactName")
                st.info("💡 **Example:** `@John Tell me about AI`")
                return
            
            if not clean_message.strip():
                st.error("❌ No message content found! Please add your prompt after the mention.")
                st.info("💡 **Example:** `@John Tell me about AI`")
                return
            
            # Find matching contacts
            st.subheader(f"🔍 Finding contacts matching: '{mentioned_name}'")
            
            with st.spinner("Searching contacts..."):
                matches = whatsapp_client.find_contact_by_name(mentioned_name)
            
            if not matches:
                st.error(f"❌ No contacts found matching '{mentioned_name}'")
                st.info("💡 Try a different name or check your contact list")
                return
            
            if len(matches) == 1:
                # Single match - show confirmation
                contact = matches[0]
                show_send_confirmation(contact, clean_message, mentioned_name)
            else:
                # Multiple matches - let user choose
                st.warning(f"🤔 Found {len(matches)} contacts matching '{mentioned_name}'. Please choose:")
                
                for i, contact in enumerate(matches):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{contact.name}**")
                        st.caption(f"ID: {contact.id}")
                    
                    with col2:
                        if st.button(f"Select", key=f"select_{i}"):
                            st.session_state.selected_contact = contact
                            st.session_state.clean_message = clean_message
                            st.session_state.mentioned_name = mentioned_name
                            st.rerun()
            
            # Handle session state for selected contact
            if hasattr(st.session_state, 'selected_contact'):
                contact = st.session_state.selected_contact
                clean_msg = st.session_state.clean_message
                mention = st.session_state.mentioned_name
                
                # Clear session state
                del st.session_state.selected_contact
                del st.session_state.clean_message
                del st.session_state.mentioned_name
                
                show_send_confirmation(contact, clean_msg, mention)
                
        except AttributeError as e:
            st.error(f"❌ **Method Error:** {str(e)}")
            st.warning("🔄 **Try refreshing the page** - the module may need to reload")
            st.info("💡 If the error persists, restart the dashboard")
        except Exception as e:
            st.error(f"❌ **Unexpected Error:** {str(e)}")

def show_send_confirmation(contact, message, mentioned_name):
    """Show confirmation dialog before sending message"""
    st.subheader("✅ Confirmation Required")
    
    # Check connection status again before sending
    status = whatsapp_client.connection_status()
    if not status.get("connected", False):
        st.error("❌ **WhatsApp connection lost!**")
        st.warning("🚨 Please reconnect to WhatsApp before sending")
        return
    
    # Extract phone number for verification
    phone = contact.id.split('@')[0]
    
    # Show confirmation details
    st.success(f"🎯 **Ready to send to:** {contact.name}")
    st.info(f"📱 **Phone Number:** {phone}")
    st.info(f"💬 **Message:** {message}")
    
    # Confirmation form
    with st.form("confirmation_form"):
        st.warning("⚠️ **Please verify the phone number above before sending!**")
        
        confirm_checkbox = st.checkbox(
            f"I confirm sending to {phone}",
            help="Check this box to confirm the recipient phone number"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            send_confirmed = st.form_submit_button(
                "✅ Confirm & Send",
                type="primary",
                disabled=not confirm_checkbox
            )
        
        with col2:
            cancel_send = st.form_submit_button("❌ Cancel")
    
    # Process confirmation
    if send_confirmed and confirm_checkbox:
        # Double-check connection before proceeding
        current_status = whatsapp_client.connection_status()
        if not current_status.get("connected", False):
            st.error("❌ **Connection lost during confirmation!**")
            st.warning("🚨 WhatsApp disconnected. Please reconnect and try again.")
            return
        
        # Generate AI response and send
        st.subheader("🔄 Processing...")
        
        with st.spinner("🤖 AI is generating response..."):
            start_time = time.time()
            try:
                ai_response = ai_agent.get_simple_response(message)
                ai_time = time.time() - start_time
                
                if not ai_response:
                    st.error("❌ AI failed to generate a response. Please try again.")
                    return
                
                st.success(f"✅ AI response generated in {ai_time:.2f}s")
                
            except Exception as e:
                st.error(f"❌ AI Error: {str(e)}")
                return
        
        # Show AI response preview
        with st.expander("🤖 AI Response Preview", expanded=True):
            st.info(ai_response)
        
        # Send to WhatsApp with better error handling
        with st.spinner("📱 Sending to WhatsApp..."):
            send_start = time.time()
            try:
                success = whatsapp_client.send_message(contact.id, ai_response)
                send_time = time.time() - send_start
                
                if success:
                    st.success(f"✅ Message sent successfully to {contact.name} in {send_time:.2f}s!")
                    
                    # Show delivery summary
                    st.subheader("📊 Delivery Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("👤 Recipient", contact.name)
                    with col2:
                        st.metric("⏱️ AI Time", f"{ai_time:.2f}s")
                    with col3:
                        st.metric("📤 Send Time", f"{send_time:.2f}s")
                    
                    st.balloons()
                    st.info("💡 **Success!** Check your WhatsApp to see the message delivered!")
                    
                else:
                    st.error("❌ Failed to send message to WhatsApp.")
                    st.warning("🔧 **Possible Issues:**")
                    st.write("• WhatsApp connection may have been lost")
                    st.write("• Bridge server error occurred")
                    st.write("• Invalid recipient ID")
                    st.info("💡 **Solution:** Check connection status and try again")
                    
            except Exception as e:
                st.error(f"❌ WhatsApp Send Error: {str(e)}")
                if "500 Server Error" in str(e):
                    st.warning("🚨 **Server Error Detected**")
                    st.write("• WhatsApp bridge encountered an internal error")
                    st.write("• Connection to WhatsApp may be lost")
                    st.info("💡 **Solution:** Reconnect to WhatsApp and try again")
    
    elif cancel_send:
        st.info("❌ Send cancelled by user")

def process_traditional_send(ai_prompt, selected_chat, selected_id, recent_options, all_options):
    """Process traditional send form submission"""
    
    recipient_id = selected_id
    recipient_name = selected_chat
    
    # Determine if this is a group or individual
    is_group = recipient_id.endswith('@g.us')
    recipient_type = "WhatsApp Group" if is_group else "Individual Contact"
    
    # Show what's being sent
    st.subheader("📤 Sending Message")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(f"🎯 **To:** {recipient_name}")
        st.info(f"📱 **Type:** {recipient_type}")
        st.caption(f"**ID:** {recipient_id}")
    
    with col2:
        if is_group:
            st.warning("👥 **Group Message**")
            st.caption("Message will be sent to group chat")
        else:
            st.success("👤 **Personal Message**")
            st.caption("Message will be sent privately")
    
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
    
    # Show completion message
    st.markdown("---")
    st.info("✅ **Message sent successfully!** You can send another message using the form above.")

def show_test_interface():
    """Show AI agent testing interface with orchestrator support"""
    st.header("🧪 Test Multi-Agent System")
    
    # Show current system status
    try:
        agent_info = message_processor.get_agent_info()
        orchestrator_enabled = agent_info.get("orchestrator_enabled", False)
        agents = agent_info.get("agents", [])
        
        col1, col2 = st.columns(2)
        with col1:
            if orchestrator_enabled:
                st.success("🎯 **Orchestrator Active** - Testing multi-agent routing")
            else:
                st.warning("🔄 **Fallback Mode** - Using single agent")
        
        with col2:
            if agents:
                st.info(f"🤖 **{len(agents)} Agent(s) Available**")
                for agent in agents:
                    st.caption(f"• {agent.get('name', 'Unknown')}")
            else:
                st.caption("• Fallback Agent Only")
    except:
        st.warning("⚠️ Unable to load agent information")
    
    st.markdown("---")
    st.markdown("Test your AI system responses without sending to WhatsApp:")
    
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
            
            # Enhanced testing with orchestrator
            try:
                if hasattr(message_processor, 'process_web_message'):
                    # Use async web processing for better orchestrator testing
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            message_processor.process_web_message(test_query, "test_session")
                        )
                        response = result.get("response", "No response")
                        agent_used = result.get("agent_id", "unknown")
                        confidence = result.get("confidence", 0.0)
                        success = result.get("success", False)
                        metadata = result.get("metadata", {})
                    finally:
                        loop.close()
                else:
                    # Fallback to original test method
                    response = message_processor.test_ai_response(test_query)
                    agent_used = "fallback"
                    confidence = 0.5
                    success = bool(response)
                    metadata = {}
                    
            except Exception as e:
                response = f"Error: {str(e)}"
                agent_used = "error"
                confidence = 0.0
                success = False
                metadata = {"error": str(e)}
            
            processing_time = time.time() - start_time
        
        # Display enhanced result
        if success:
            st.success("✅ Response generated!")
        else:
            st.error("❌ Response generation failed!")
        
        # Show detailed results
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### 🤖 AI Response:")
            if success:
                st.info(response)
            else:
                st.error(response)
        
        with col2:
            st.metric("Processing Time", f"{processing_time:.2f}s")
            st.metric("Confidence", f"{confidence:.2f}")
        
        with col3:
            st.metric("Agent Used", agent_used)
            if metadata:
                with st.expander("📊 Metadata"):
                    st.json(metadata)
    
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

def show_connection_help():
    """Show WhatsApp connection troubleshooting guide"""
    st.header("🔗 WhatsApp Connection Help")
    
    # Current status
    st.subheader("📊 Current Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if whatsapp_client.health_check():
            st.success("✅ **Bridge Server:** Running")
        else:
            st.error("❌ **Bridge Server:** Not running")
    
    with col2:
        status = whatsapp_client.connection_status()
        if status.get("connected", False):
            st.success("✅ **WhatsApp:** Connected")
        else:
            st.error("❌ **WhatsApp:** Disconnected")
    
    # Troubleshooting steps
    st.subheader("🛠️ Troubleshooting Steps")
    
    st.markdown("""
    ### 📱 If WhatsApp is Disconnected:
    
    1. **Open your WhatsApp Bridge terminal**
       - Look for the window running `go run .` in the `whatsapp-bridge` folder
    
    2. **Look for QR Code**
       - The terminal should show a QR code
       - If no QR code appears, restart the bridge: `Ctrl+C` then `go run .`
    
    3. **Scan QR Code**
       - Open WhatsApp on your phone
       - Go to **Settings > Linked Devices**
       - Tap **Link a Device**
       - Scan the QR code from your terminal
    
    4. **Wait for Connection**
       - After scanning, wait 10-15 seconds
       - Check this dashboard for green "Connected" status
    
    ### 🔧 If Bridge Server is Down:
    
    1. **Navigate to bridge folder:**
       ```bash
       cd whatsapp-mcp/whatsapp-bridge
       ```
    
    2. **Start the bridge:**
       ```bash
       go run .
       ```
    
    3. **Check the port:**
       - Bridge should run on `localhost:3334`
       - Look for message: `Server listening on :3334`
    """)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Status", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("🧪 Test Connection"):
            with st.spinner("Testing..."):
                bridge_ok = whatsapp_client.health_check()
                wa_status = whatsapp_client.connection_status()
                
            if bridge_ok and wa_status.get("connected", False):
                st.success("🎉 All systems working!")
            elif bridge_ok:
                st.warning("⚠️ Bridge OK, but WhatsApp disconnected")
            else:
                st.error("❌ Bridge server not responding")
    
    with col3:
        if st.button("📋 Show Bridge Logs"):
            st.info("💡 Check your terminal running the WhatsApp bridge for detailed logs")

if __name__ == "__main__":
    main() 