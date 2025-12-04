"""
SRM - Water & Electricity Utility Customer Service AI Assistant
Main application entry point using Streamlit.
"""
import streamlit as st
from config.settings import settings
from ui.layout import inject_rtl_css, render_header, render_sidebar, render_footer
from ui.chat_interface import render_chat_interface, clear_chat_history, display_conversation_stats
from services.ai_service import initialize_agent


def main():
    """Main application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title=settings.APP_TITLE,
        page_icon=settings.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject RTL CSS for Arabic support
    inject_rtl_css()
    
    # Validate configuration
    is_valid, missing_keys = settings.validate()
    
    if not is_valid:
        st.error(settings.get_error_message(missing_keys))
        st.stop()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Initialize agent (with caching)
    @st.cache_resource
    def get_agent():
        """Get or create agent executor with caching."""
        return initialize_agent()
    
    agent_executor = get_agent()
    
    if agent_executor is None:
        st.error("❌ فشل في تهيئة المساعد الذكي. الرجاء التحقق من الإعدادات.")
        st.stop()
    
    # Main chat interface
    render_chat_interface(agent_executor)
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("---")
        clear_chat_history()
        display_conversation_stats()
    
    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
