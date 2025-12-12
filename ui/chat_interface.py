"""
Chat interface components for SRM application.
Handles chat display, message history, and user interactions.
"""
import streamlit as st
from typing import Optional
from services.ocr_service import extract_contract_from_image, extract_bill_information, format_extracted_info_arabic
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
            "content": "مرحباً بك في خدمة عملاء SRM! 👋\n\nأنا هنا لمساعدتك في فهم سبب انقطاع الماء أو الكهرباء.\n\n**أرقام العقود:**\n- رقم عقد الماء يبدأ بـ 3701 (مثال: 3701455886 / 1014871)\n- رقم عقد الكهرباء يبدأ بـ 4801 (مثال: 4801566997 / 2025982)\n\nيمكنك تقديم رقم العقد أو رفع صورة الفاتورة."
        })
    
    # Image upload section
    st.markdown("### 📤 رفع صورة الفاتورة (اختياري)")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "اختر صورة الفاتورة لاستخراج المعلومات تلقائياً",
            type=["png", "jpg", "jpeg", "pdf"],
            help="قم برفع صورة واضحة للفاتورة تحتوي على رقم العقد والمعلومات الأخرى"
        )
    
    with col2:
        extract_full = st.checkbox("استخراج كامل المعلومات", value=True, help="استخراج جميع المعلومات من الفاتورة")
    
    if uploaded_file is not None:
        # Display the uploaded image
        if uploaded_file.type.startswith('image'):
            st.image(uploaded_file, caption="الصورة المرفوعة", use_container_width=True)
        
        # Extract information button
        button_label = "🔍 استخراج المعلومات من الفاتورة" if extract_full else "🔍 استخراج رقم العقد فقط"
        
        if st.button(button_label):
            with st.spinner("جاري معالجة الصورة..."):
                image_bytes = uploaded_file.getvalue()
                
                if extract_full:
                    # Extract all bill information
                    bill_info = extract_bill_information(image_bytes)
                    
                    if "error" in bill_info:
                        st.error(f"❌ {bill_info['error']}")
                    else:
                        # Display extracted information
                        formatted_info = format_extracted_info_arabic(bill_info)
                        st.success("✅ تم استخراج المعلومات بنجاح!")
                        st.markdown(formatted_info)
                        
                        # If contract found, add to chat
                        if bill_info.get("contract"):
                            user_message = f"رقم العقد الخاص بي هو: {bill_info['contract']}"
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
                            st.warning("⚠️ لم يتم العثور على رقم العقد. يمكنك إدخاله يدوياً.")
                else:
                    # Extract only Contract Numbers
                    extracted_contracts = extract_contract_from_image(image_bytes)
                    
                    if extracted_contracts and extracted_contracts.get('status') != 'not_found':
                        water_contract = extracted_contracts.get('water_contract')
                        electricity_contract = extracted_contracts.get('electricity_contract')
                        
                        contract_info = []
                        if water_contract:
                            contract_info.append(f"رقم عقد الماء: {water_contract}")
                        if electricity_contract:
                            contract_info.append(f"رقم عقد الكهرباء: {electricity_contract}")
                        
                        if contract_info:
                            st.success("✅ تم استخراج أرقام العقود:\n" + "\n".join(contract_info))
                            
                            # Add extracted contracts to chat
                            user_message = "\n".join(contract_info)
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
                            st.warning("⚠️ " + extracted_contracts.get('message', 'لم يتم العثور على أرقام عقود في الصورة'))
                    else:
                        # Show OCR failure message
                        error_message = extracted_contracts.get('message', 'لم أتمكن من استخراج رقم العقد من الصورة. الرجاء التأكد من أن الصورة واضحة وتحتوي على رقم العقد، أو يمكنك كتابة الرقم مباشرة.')
                        st.warning("⚠️ " + error_message)
    
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
