"""
Chat interface components for SRM application.
Handles chat display, message history, and user interactions.
"""
import streamlit as st
from typing import Optional
from services.ocr_service import extract_cil_from_image
from services.ai_service import run_agent


def render_chat_interface(agent_executor):
    """
    Render the chat interface with message history and input.
    
    Args:
        agent_executor: The LangChain agent executor
    """
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "مرحباً بك في خدمة عملاء SRM! 👋\n\nأنا هنا لمساعدتك في فهم سبب انقطاع الماء أو الكهرباء.\n\nالرجاء تقديم رقم CIL الخاص بك (8 أرقام) أو رفع صورة الفاتورة."
        })
    
    # Image upload section
    st.markdown("### 📤 رفع صورة الفاتورة (اختياري)")
    uploaded_file = st.file_uploader(
        "اختر صورة الفاتورة لاستخراج رقم CIL تلقائياً",
        type=["png", "jpg", "jpeg", "pdf"],
        help="قم برفع صورة واضحة للفاتورة تحتوي على رقم CIL"
    )
    
    if uploaded_file is not None:
        # Display the uploaded image
        if uploaded_file.type.startswith('image'):
            st.image(uploaded_file, caption="الصورة المرفوعة", use_container_width=True)
        
        # Extract CIL button
        if st.button("🔍 استخراج رقم CIL من الصورة"):
            with st.spinner("جاري معالجة الصورة..."):
                image_bytes = uploaded_file.getvalue()
                extracted_cil = extract_cil_from_image(image_bytes)
                
                if extracted_cil:
                    st.success(f"✅ تم استخراج رقم CIL: {extracted_cil}")
                    # Add extracted CIL to chat
                    user_message = f"رقم CIL الخاص بي هو: {extracted_cil}"
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_message
                    })
                    
                    # Get agent response
                    with st.spinner("جاري المعالجة..."):
                        response = run_agent(
                            agent_executor,
                            user_message,
                            st.session_state.messages[:-1]
                        )
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response
                        })
                    st.rerun()
                else:
                    st.error("❌ لم يتم العثور على رقم CIL في الصورة. الرجاء إدخاله يدوياً.")
    
    st.markdown("---")
    st.markdown("### 💬 المحادثة")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("اكتب رسالتك هنا..."):
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("جاري التفكير..."):
                response = run_agent(
                    agent_executor,
                    prompt,
                    st.session_state.messages[:-1]
                )
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
        
        st.rerun()


def clear_chat_history():
    """Clear the chat history."""
    if st.sidebar.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.rerun()


def display_conversation_stats():
    """Display conversation statistics in sidebar."""
    if "messages" in st.session_state:
        num_messages = len(st.session_state.messages)
        st.sidebar.markdown(f"**عدد الرسائل:** {num_messages}")
