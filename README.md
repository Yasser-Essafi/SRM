# SRM - نظام خدمة العملاء الذكي
## Water & Electricity Utility AI Customer Service Assistant

مساعد ذكي باللغة العربية لمساعدة المواطنين في فهم أسباب انقطاع الماء والكهرباء.

---

## 📋 نظرة عامة / Overview

This is a modular Proof of Concept (PoC) for SRM (Water & Electricity Utility) customer service. The AI agent helps citizens understand why their water/electricity service is interrupted, entirely in **Arabic**.

### ✨ المميزات الرئيسية / Key Features

- 🤖 **مساعد ذكي بالعربية** - AI Assistant in Arabic using Azure OpenAI (GPT-4o)
- 📄 **استخراج تلقائي لرقم CIL** - Automatic CIL extraction from bill images using Azure Document Intelligence
- 💳 **التحقق من حالة الدفع** - Payment status verification
- 🔧 **معلومات الصيانة** - Maintenance and outage information
- 🌐 **واجهة عربية كاملة** - Full RTL (Right-to-Left) Arabic UI support
- 📊 **بيانات تجريبية** - Mock data simulating Azure SQL database

---

## 🏗️ البنية المعمارية / Architecture

```
/srm
├── .env.example              # Template for environment variables
├── .env                      # Your environment variables (create this)
├── app.py                    # Main entry point (minimal, clean)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── /config                   # Configuration module
│   ├── __init__.py
│   └── settings.py           # Environment variables, Azure configs, constants
│
├── /data                     # Data layer
│   ├── __init__.py
│   └── mock_db.py            # Mock database using Pandas (simulates Azure SQL)
│
├── /services                 # Business logic layer
│   ├── __init__.py
│   ├── ai_service.py         # LangChain agent, tools, Arabic prompts
│   └── ocr_service.py        # Azure Document Intelligence integration
│
└── /ui                       # Presentation layer
    ├── __init__.py
    ├── layout.py             # Header, sidebar, RTL CSS
    └── chat_interface.py     # Chat components and message handling
```

---

## 🚀 التثبيت والإعداد / Installation & Setup

### المتطلبات / Prerequisites

- Python 3.9+
- Azure OpenAI account with GPT-4o deployment
- Azure Document Intelligence (Form Recognizer) resource

### 1️⃣ استنساخ المشروع / Clone the Project

```powershell
cd "c:\Users\TahaELMARZOUKI\OneDrive - ALEXSYS SOLUTIONS\Desktop\srm"
```

### 2️⃣ إنشاء بيئة افتراضية / Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3️⃣ تثبيت المكتبات / Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4️⃣ إعداد المتغيرات البيئية / Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Azure credentials:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your credentials:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_actual_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Azure Document Intelligence Configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_actual_key_here
```

### 5️⃣ تشغيل التطبيق / Run the Application

```powershell
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

---

## 🧪 اختبار النظام / Testing the System

### Test CIL Numbers

Use these CIL numbers to test different scenarios:

| CIL Number | Name | Payment Status | Maintenance | Service Status |
|------------|------|----------------|-------------|----------------|
| `12345678` | أحمد المرزوقي | ✅ Paid | ⚙️ Yes | Active |
| `87654321` | فاطمة الزهراء | ❌ Unpaid (450 DH) | No | Disconnected |
| `11223344` | محمد الإدريسي | ✅ Paid | No | Active |
| `55667788` | خديجة العلوي | ✅ Paid | No | Active |
| `99887766` | يوسف السباعي | ❌ Unpaid (890 DH) | No | Disconnected |

### Example Conversation Flow

1. **User**: مرحبا
2. **Agent**: مرحباً بك! الرجاء تقديم رقم CIL
3. **User**: 87654321
4. **Agent**: [Checks payment] يوجد رصيد مستحق 450 درهم...
5. **User**: 12345678
6. **Agent**: [Checks payment - paid, then checks maintenance] جاري صيانة في منطقتك...

---

## 📦 المكونات الرئيسية / Main Components

### 🔧 config/settings.py
- Loads environment variables using `python-dotenv`
- Validates configuration on startup
- Provides Arabic error messages for missing keys

### 💾 data/mock_db.py
- Contains `users_table` and `zones_table` as Pandas DataFrames
- Simulates Azure SQL database
- Provides lookup functions: `get_user_by_cil()`, `get_zone_by_id()`

### 🤖 services/ai_service.py
- **Tools**: `check_payment()`, `check_maintenance()`
- **Agent**: LangChain agent with Azure OpenAI (GPT-4o)
- **System Prompt**: Strictly enforces Arabic language responses
- **Integration**: Uses LangChain's `create_openai_tools_agent`

### 📄 services/ocr_service.py
- `extract_cil_from_image()`: Extracts CIL from uploaded bill images
- Uses Azure Document Intelligence (prebuilt-read model)
- Regex pattern matching for CIL numbers (format: 1071324-101)

### 🎨 ui/layout.py
- `inject_rtl_css()`: Injects RTL (Right-to-Left) CSS for Arabic
- `render_header()`: Application header with branding
- `render_sidebar()`: Information, instructions, test CIL numbers

### 💬 ui/chat_interface.py
- `render_chat_interface()`: Main chat UI
- Handles message history in `st.session_state`
- Image upload and OCR integration
- Chat input and response display

### 🚪 app.py
- Main entry point (minimal and clean)
- Configuration validation
- Agent initialization with caching
- Component orchestration

---

## 🛠️ التقنيات المستخدمة / Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit |
| **AI Framework** | LangChain |
| **LLM** | Azure OpenAI (GPT-4o) |
| **OCR** | Azure Document Intelligence |
| **Data** | Pandas (mock Azure SQL) |
| **Language** | Python 3.9+ |

---

## 🌍 الدعم العربي / Arabic Support

### RTL (Right-to-Left) Implementation

The UI fully supports Arabic with:
- ✅ RTL text direction for all components
- ✅ Right-aligned text inputs and chat messages
- ✅ Arabic fonts optimized for readability
- ✅ Culturally appropriate greetings and responses

### Arabic System Prompt

The AI agent is strictly instructed to:
- Respond **only in Arabic**
- Use professional, formal Arabic (Fusha)
- Provide clear, actionable information
- Follow Moroccan cultural context

---

## 📝 الخطوات التالية / Next Steps

### للإنتاج / For Production

1. **قاعدة البيانات** - Replace Pandas mock data with Azure SQL Database
2. **المصادقة** - Add user authentication and authorization
3. **السجلات** - Implement comprehensive logging (Azure Application Insights)
4. **التحليلات** - Add conversation analytics and reporting
5. **التوسع** - Containerize with Docker for Azure deployment
6. **الأمان** - Implement data encryption and PII protection

### ميزات إضافية / Additional Features

- 📧 Email/SMS notifications for payment reminders
- 📊 Admin dashboard for monitoring conversations
- 🔔 Real-time outage alerts
- 💳 Integrated payment gateway
- 📱 Mobile app version

---

## 🤝 المساهمة / Contributing

This is a Proof of Concept. For production use:
1. Review and update security configurations
2. Implement proper error handling and monitoring
3. Add comprehensive unit and integration tests
4. Follow Azure best practices for scalability

---

## 📄 الترخيص / License

© 2024 SRM - نظام إدارة المياه والكهرباء

---

## 📞 الدعم / Support

- **Emergency**: 0800-000-000
- **Email**: support@srm.ma
- **Documentation**: This README

---

## ⚠️ ملاحظات مهمة / Important Notes

1. **Mock Data**: Currently using Pandas DataFrames. Replace with Azure SQL for production.
2. **API Keys**: Never commit `.env` file to version control
3. **Costs**: Monitor Azure OpenAI and Document Intelligence usage
4. **Testing**: Use provided test CIL numbers during development
5. **Arabic**: All user-facing text must remain in Arabic

---

Built with ❤️ for Moroccan citizens
