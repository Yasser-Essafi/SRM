"""
Layout components for SRM application.
Provides header, sidebar, and RTL (Right-to-Left) CSS support for Arabic.
"""
import streamlit as st
from config.settings import settings


def inject_rtl_css():
    """
    Inject custom CSS for Right-to-Left (RTL) support and Arabic styling.
    """
    st.markdown("""
    <style>
        /* RTL Support for Arabic */
        .stApp {
            direction: rtl;
            text-align: right;
        }
        
        /* Chat messages */
        .stChatMessage {
            direction: rtl;
            text-align: right;
        }
        
        /* Text inputs */
        .stTextInput > div > div > input {
            direction: rtl;
            text-align: right;
        }
        
        /* Text areas */
        .stTextArea > div > div > textarea {
            direction: rtl;
            text-align: right;
        }
        
        /* Markdown content */
        .stMarkdown {
            direction: rtl;
            text-align: right;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            direction: rtl;
            text-align: right;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            direction: rtl;
            text-align: right;
        }
        
        /* Lists */
        ul, ol {
            direction: rtl;
            text-align: right;
            padding-right: 20px;
            padding-left: 0;
        }
        
        /* Custom styling for better Arabic font rendering */
        * {
            font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif;
        }
        
        /* Chat input */
        .stChatInputContainer {
            direction: rtl;
        }
        
        /* File uploader */
        [data-testid="stFileUploader"] {
            direction: rtl;
            text-align: right;
        }
        
        /* Success/Error/Warning boxes */
        .stSuccess, .stError, .stWarning, .stInfo {
            direction: rtl;
            text-align: right;
        }
        
        /* Custom header styling */
        .main-header {
            background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            color: white;
            text-align: center;
        }
        
        .main-header h1 {
            margin: 0;
            color: white;
            text-align: center;
        }
        
        /* Sidebar styling */
        .sidebar-info {
            background-color: #f0f9ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-right: 4px solid #3b82f6;
        }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """
    Render the main application header with branding.
    """
    st.markdown(f"""
    <div class="main-header">
        <h1>{settings.APP_ICON} {settings.APP_TITLE}</h1>
        <p style="margin: 5px 0 0 0; font-size: 14px;">مساعدك الذكي لخدمات المياه والكهرباء</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """
    Render the sidebar with information and instructions.
    """
    with st.sidebar:
        st.markdown("### 📋 معلومات النظام")
        
        st.markdown("""
        <div class="sidebar-info">
            <h4>🎯 كيفية الاستخدام</h4>
            <ol>
                <li>ابدأ المحادثة مع المساعد</li>
                <li>أخبر المساعد عن المشكلة (ماء أو كهرباء)</li>
                <li>قدم رقم العقد المناسب:
                    <ul>
                        <li>رقم عقد الماء: 3701XXXXXX / XXXXXXX</li>
                        <li>رقم عقد الكهرباء: 4801XXXXXX / XXXXXXX</li>
                    </ul>
                </li>
                <li>يمكنك رفع صورة الفاتورة لاستخراج الرقم تلقائياً</li>
                <li>سيساعدك المساعد في فهم سبب الانقطاع</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="sidebar-info">
            <h4>💡 الخدمات المتوفرة</h4>
            <ul>
                <li>التحقق من حالة الدفع</li>
                <li>معرفة سبب انقطاع الخدمة</li>
                <li>معلومات عن الصيانة في منطقتك</li>
                <li>إرشادات للدفع</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="sidebar-info">
            <h4>📞 للمساعدة</h4>
            <p>رقم الطوارئ: <strong>0800-000-000</strong></p>
            <p>البريد الإلكتروني: <strong>support@srm.ma</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Testing Contract numbers
        with st.expander("🔢 أرقام العقود للاختبار"):
            st.markdown("""
            **عقود الماء (تبدأ بـ 3701):**
            - **3701455886 / 1014871** - Abdenbi (مدفوع، صيانة ماء)
            - **3701455887 / 1014872** - Ahmed (مدفوع، لا صيانة)
            - **3701455888 / 1014873** - محمد (مدفوع، لا صيانة)
            - **3701455890 / 1014875** - يوسف (غير مدفوع، مقطوع)
            
            **عقود الكهرباء (تبدأ بـ 4801):**
            - **4801566997 / 2025982** - Abdenbi (مدفوع، لا صيانة)
            - **4801566998 / 2025983** - محمد (مدفوع، لا صيانة)
            - **4801566999 / 2025984** - خديجة (مدفوع، صيانة كهرباء)
            - **4801567001 / 2025986** - يوسف (غير مدفوع، مقطوع)
            """)


def render_footer():
    """
    Render the application footer.
    """
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px; padding: 10px;">
        © 2024 SRM - نظام إدارة المياه والكهرباء | جميع الحقوق محفوظة
    </div>
    """, unsafe_allow_html=True)
