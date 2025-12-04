# SRM Flask Backend API

## 🚀 Quick Start

### Install Backend Dependencies
```powershell
pip install -r requirements-backend.txt
```

### Run Flask Server
```powershell
python backend/app.py
```

Server runs at: `http://localhost:5000`

---

## 📡 API Endpoints

### **1. Health Check**
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "SRM AI Customer Service",
  "version": "1.0.0"
}
```

---

### **2. Chat with AI Agent**
```http
POST /api/chat
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "رقم CIL الخاص بي هو: 1071324-101",
  "chat_history": [
    {"role": "user", "content": "مرحبا"},
    {"role": "assistant", "content": "مرحباً بك!"}
  ]
}
```

**Response:**
```json
{
  "response": "معلومات العميل Abdenbi EL MARZOUKI:\n- حالة الدفع: ✅ مدفوع...",
  "status": "success"
}
```

---

### **3. Extract CIL from Bill Image**
```http
POST /api/ocr/extract-cil
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Image file (JPG, PNG, PDF)

**Response:**
```json
{
  "cil": "1071324-101",
  "status": "success"
}
```

---

### **4. Extract Full Bill Information**
```http
POST /api/ocr/extract-full
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Image file

**Response:**
```json
{
  "bill_info": {
    "cil": "1071324-101",
    "name": "Abdenbi EL MARZOUKI",
    "amount_due": 351.48,
    "service_type": "ماء وكهرباء"
  },
  "formatted_ar": "📄 **المعلومات المستخرجة...**",
  "status": "success"
}
```

---

### **5. Reset Chat Session**
```http
POST /api/chat/reset
```

**Response:**
```json
{
  "message": "Chat session reset",
  "message_ar": "تم إعادة تعيين المحادثة",
  "status": "success"
}
```

---

## 🧪 Testing with cURL

### Chat Example
```powershell
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"1071324-101\"}'
```

### OCR Example
```powershell
curl -X POST http://localhost:5000/api/ocr/extract-cil `
  -F "file=@path/to/bill.jpg"
```

---

## 🏗️ Backend Architecture

```
/backend
├── app.py                  # Flask application entry point
├── routes/
│   ├── health.py          # Health check endpoint
│   ├── chat.py            # Chat API endpoints
│   └── ocr.py             # OCR API endpoints
└── middleware/            # Future: Auth, logging, etc.
```

---

## 🔗 Integration with Streamlit

The Streamlit frontend (app.py) continues to work independently. The Flask backend provides REST API access for:
- Mobile apps
- Web frontends
- Third-party integrations
- Testing with Postman/cURL

---

## 🚀 Production Deployment

### Using Gunicorn
```powershell
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Environment Variables
Same `.env` file is used by both Streamlit and Flask backend.

---

## ✅ CORS Configuration

The backend allows requests from:
- `http://localhost:3000` (React/Next.js)
- `http://localhost:8501` (Streamlit)

Modify in `backend/app.py` for production URLs.
