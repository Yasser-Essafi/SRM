# 🏗️ SRM Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER (Web Browser)                          │
│                    Streamlit UI - Arabic RTL                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ├─────────────────────────────┐
                                 │                             │
                                 ▼                             ▼
                    ┌─────────────────────┐      ┌─────────────────────┐
                    │   Image Upload      │      │   Text Chat Input   │
                    │   (Bill/Document)   │      │   (CIL/Question)    │
                    └──────────┬──────────┘      └──────────┬──────────┘
                               │                            │
                               ▼                            │
                    ┌─────────────────────┐                │
                    │  OCR Service        │                │
                    │  (Azure Doc Intel)  │                │
                    │  Extract CIL        │                │
                    └──────────┬──────────┘                │
                               │                            │
                               └──────────┬─────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │   AI Service           │
                              │   (LangChain Agent)    │
                              │   Azure OpenAI GPT-4o  │
                              └──────────┬─────────────┘
                                         │
                        ┌────────────────┼────────────────┐
                        │                │                │
                        ▼                ▼                ▼
              ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
              │ check_payment   │  │ check_       │  │ [Future]     │
              │ Tool            │  │ maintenance  │  │ Tools        │
              │                 │  │ Tool         │  │              │
              └────────┬────────┘  └──────┬───────┘  └──────────────┘
                       │                  │
                       └────────┬─────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │   Data Layer             │
                    │   (Mock Database)        │
                    │   - users_table (Pandas) │
                    │   - zones_table (Pandas) │
                    └──────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │   [Future: Azure SQL]    │
                    │   Real production DB     │
                    └──────────────────────────┘
```

---

## Module Dependencies

```
app.py (Entry Point)
    │
    ├─→ config.settings
    │       └─→ .env (Environment Variables)
    │
    ├─→ ui.layout
    │       ├─→ inject_rtl_css()
    │       ├─→ render_header()
    │       ├─→ render_sidebar()
    │       └─→ render_footer()
    │
    ├─→ ui.chat_interface
    │       ├─→ render_chat_interface()
    │       ├─→ clear_chat_history()
    │       └─→ display_conversation_stats()
    │
    └─→ services.ai_service
            ├─→ initialize_agent()
            ├─→ run_agent()
            │
            ├─→ Tools:
            │   ├─→ check_payment()
            │   │       └─→ data.get_user_by_cil()
            │   │
            │   └─→ check_maintenance()
            │           ├─→ data.get_user_by_cil()
            │           └─→ data.get_zone_by_id()
            │
            └─→ services.ocr_service
                    └─→ extract_cil_from_image()
```

---

## Data Flow: User Query → Response

```
1. USER INPUT
   ↓
   User types: "رقم CIL الخاص بي: 12345678"
   
2. UI LAYER (ui/chat_interface.py)
   ↓
   - Capture user input
   - Add to session_state.messages
   - Display in chat
   
3. AI SERVICE (services/ai_service.py)
   ↓
   - Agent receives: "رقم CIL الخاص بي: 12345678"
   - Agent decides to use: check_payment tool
   
4. TOOL EXECUTION (services/ai_service.py)
   ↓
   check_payment("12345678")
   
5. DATA ACCESS (data/mock_db.py)
   ↓
   get_user_by_cil("12345678")
   - Returns: {name: "أحمد", payment_status: "مدفوع", ...}
   
6. TOOL RESPONSE
   ↓
   "حالة الدفع: مدفوع. إذا كانت الخدمة مقطوعة، قد يكون السبب صيانة..."
   
7. AGENT DECISION
   ↓
   - Payment is OK
   - Agent decides to use: check_maintenance tool
   
8. MAINTENANCE CHECK
   ↓
   check_maintenance("12345678")
   - get_user_by_cil → zone_id: 1
   - get_zone_by_id(1) → maintenance: "جاري الصيانة"
   
9. FINAL RESPONSE
   ↓
   Agent synthesizes Arabic response:
   "يوجد صيانة في منطقتك. سبب الانقطاع: إصلاح أنابيب المياه..."
   
10. UI DISPLAY
    ↓
    - Add response to session_state.messages
    - Display in chat with RTL formatting
```

---

## OCR Flow: Image → CIL Extraction

```
1. USER UPLOADS IMAGE
   ↓
   User uploads bill image (PNG/JPG/PDF)
   
2. UI CAPTURE (ui/chat_interface.py)
   ↓
   - uploaded_file = st.file_uploader(...)
   - image_bytes = uploaded_file.getvalue()
   
3. OCR SERVICE (services/ocr_service.py)
   ↓
   extract_cil_from_image(image_bytes)
   
4. AZURE DOCUMENT INTELLIGENCE
   ↓
   - Initialize client with endpoint + key
   - Call: begin_analyze_document("prebuilt-read")
   - Wait for result (poller.result())
   
5. TEXT EXTRACTION
   ↓
   - Extract: result.content
   - Example: "فاتورة الماء\nCIL: 12345678\nالمبلغ: 150 درهم"
   
6. PATTERN MATCHING
   ↓
   - Regex: r'\b\d{8}\b'
   - Find: "12345678"
   
7. RETURN CIL
   ↓
   - Return: "12345678"
   
8. AUTO-INJECT TO CHAT
   ↓
   - Create message: "رقم CIL الخاص بي هو: 12345678"
   - Add to chat history
   - Trigger agent response
```

---

## Agent Decision Tree

```
Agent receives user message
    │
    ├─ Does message contain CIL (1071324-101)?
    │   ├─ YES → Store CIL, proceed
    │   └─ NO → Ask user for CIL
    │
    ├─ CIL provided?
    │   └─ YES → Use check_payment(CIL) tool
    │
    ├─ Payment status?
    │   ├─ UNPAID
    │   │   └─ Respond: Balance due + payment methods
    │   │       └─ END
    │   │
    │   └─ PAID
    │       └─ Use check_maintenance(CIL) tool
    │
    └─ Maintenance status?
        ├─ MAINTENANCE IN PROGRESS
        │   └─ Respond: Outage reason + ETA
        │       └─ END
        │
        └─ NO MAINTENANCE
            └─ Respond: No issues found
                └─ END
```

---

## Configuration Flow

```
Application Startup
    │
    ├─→ Load .env file (python-dotenv)
    │       ├─ AZURE_OPENAI_API_KEY
    │       ├─ AZURE_OPENAI_ENDPOINT
    │       ├─ AZURE_OPENAI_DEPLOYMENT_NAME
    │       ├─ AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
    │       └─ AZURE_DOCUMENT_INTELLIGENCE_KEY
    │
    ├─→ Settings.validate()
    │       ├─ Check each required key
    │       ├─ Missing keys?
    │       │   ├─ YES → Show error in Arabic
    │       │   │         Stop application
    │       │   └─ NO → Continue
    │
    ├─→ Initialize Azure OpenAI client
    │       └─→ Create LangChain agent
    │
    └─→ Initialize Document Intelligence client
            └─→ Ready for OCR
```

---

## Session State Management

```
Streamlit Session State
    │
    ├─→ messages: list[dict]
    │       ├─ {role: "assistant", content: "مرحباً..."}
    │       ├─ {role: "user", content: "12345678"}
    │       ├─ {role: "assistant", content: "حالة الدفع..."}
    │       └─ ...
    │
    ├─→ chat_history: list (for agent)
    │       └─ Converted from messages for LangChain
    │
    └─→ agent_executor: AgentExecutor (cached)
            └─ Created once, reused across reruns
```

---

## Technology Stack Layers

```
┌────────────────────────────────────────────┐
│         PRESENTATION LAYER                  │
│  Streamlit + Custom RTL CSS                 │
│  - Arabic UI                                │
│  - RTL text direction                       │
│  - Chat interface                           │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│         BUSINESS LOGIC LAYER                │
│  LangChain + Azure OpenAI                   │
│  - Agent orchestration                      │
│  - Tool execution                           │
│  - Arabic prompt engineering                │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│         INTEGRATION LAYER                   │
│  Azure Services                             │
│  - Azure OpenAI (GPT-4o)                    │
│  - Azure Document Intelligence              │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│         DATA ACCESS LAYER                   │
│  Pandas DataFrames (Mock)                   │
│  - users_table                              │
│  - zones_table                              │
│  [Future: Azure SQL Database]               │
└─────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
Error Occurs
    │
    ├─→ Missing .env configuration
    │       └─→ settings.validate() fails
    │           └─→ Display Arabic error message
    │               └─→ st.stop()
    │
    ├─→ Agent initialization fails
    │       └─→ initialize_agent() returns None
    │           └─→ Display error
    │               └─→ st.stop()
    │
    ├─→ OCR extraction fails
    │       └─→ extract_cil_from_image() returns None
    │           └─→ Display "لم يتم العثور على رقم CIL"
    │               └─→ Suggest manual input
    │
    └─→ Tool execution fails
            └─→ Agent handles with error message
                └─→ "عذراً، حدث خطأ..."
```

---

## Future Extensions

```
Current PoC
    │
    ├─→ Add Azure SQL Database
    │       └─→ Replace mock_db.py
    │           └─→ SQLAlchemy ORM
    │
    ├─→ Add Authentication
    │       └─→ Azure AD B2C
    │           └─→ User login/logout
    │
    ├─→ Add Analytics
    │       └─→ Azure Application Insights
    │           ├─→ Conversation logs
    │           ├─→ User behavior
    │           └─→ Performance metrics
    │
    ├─→ Add Payment Integration
    │       └─→ Payment gateway API
    │           └─→ Direct payment from chat
    │
    └─→ Add Multi-language
            └─→ French support
                └─→ Language selector
```

---

This architecture diagram shows:
- ✅ Clean separation of concerns
- ✅ Modular, testable components
- ✅ Clear data flow
- ✅ Scalable design
- ✅ Production-ready patterns
