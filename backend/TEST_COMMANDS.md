# SRM Backend API - Test Commands

## 🧪 Test with cURL

### 1. Health Check
```powershell
curl http://localhost:5000/api/health
```

### 2. Chat - Simple Hello
```powershell
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d "@test_chat_hello.json"
```

### 3. Chat - With CIL (Paid Customer)
```powershell
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d "@test_chat_with_cil.json"
```

### 4. Chat - CIL Only (Ahmed Sabil)
```powershell
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d "@test_chat_cil_only.json"
```

### 5. Chat - Unpaid Customer
```powershell
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d "@test_chat_unpaid.json"
```

### 6. OCR - Extract CIL from Image
```powershell
curl -X POST http://localhost:5000/api/ocr/extract-cil `
  -F "file=@path/to/bill.jpg"
```

### 7. OCR - Extract Full Bill Info
```powershell
curl -X POST http://localhost:5000/api/ocr/extract-full `
  -F "file=@path/to/bill.jpg"
```

### 8. Reset Chat
```powershell
curl -X POST http://localhost:5000/api/chat/reset
```

---

## 🧪 Test with PowerShell Invoke-RestMethod

### Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method Get
```

### Chat with JSON Body
```powershell
$body = @{
    message = "1071324-101"
    chat_history = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### OCR Extract CIL
```powershell
$form = @{
    file = Get-Item "path\to\bill.jpg"
}

Invoke-RestMethod -Uri "http://localhost:5000/api/ocr/extract-cil" `
  -Method Post `
  -Form $form
```

---

## 📋 Expected Responses

### Health Check Response
```json
{
  "status": "healthy",
  "service": "SRM AI Customer Service",
  "version": "1.0.0"
}
```

### Chat Response (Paid Customer)
```json
{
  "response": "معلومات العميل Abdenbi EL MARZOUKI:\n- نوع الخدمة: ماء وكهرباء\n- حالة الدفع: ✅ مدفوع\n- آخر دفعة: 2024-11-15\n- الرصيد المستحق: 0.0 درهم\n- حالة الخدمة: نشط\n\nالدفعات محدثة. إذا كانت الخدمة مقطوعة، قد يكون السبب صيانة في المنطقة.",
  "status": "success"
}
```

### Chat Response (Unpaid Customer)
```json
{
  "response": "معلومات العميل يوسف السباعي:\n- نوع الخدمة: ماء وكهرباء\n- حالة الدفع: ⚠️ غير مدفوع\n- آخر دفعة: 2024-08-15\n- الرصيد المستحق: 890.0 درهم\n- حالة الخدمة: مقطوع\n\nيوجد رصيد مستحق بقيمة 890.0 درهم. الرجاء سداد المبلغ لاستعادة الخدمة...",
  "status": "success"
}
```

### OCR Extract CIL Response
```json
{
  "cil": "1071324-101",
  "status": "success"
}
```

### OCR Extract Full Response
```json
{
  "bill_info": {
    "cil": "1071324-101",
    "name": "Abdenbi EL MARZOUKI",
    "amount_due": 351.48,
    "service_type": "ماء وكهرباء",
    "breakdown": {
      "water": 160.59,
      "electricity": 190.89
    }
  },
  "formatted_ar": "📄 **المعلومات المستخرجة من الفاتورة:**\n\n🔢 رقم CIL: **1071324-101**\n👤 الاسم: Abdenbi EL MARZOUKI...",
  "status": "success"
}
```

---

## 🎯 Test CIL Numbers

| CIL | Customer | Status | Expected Response |
|-----|----------|--------|-------------------|
| `1071324-101` | Abdenbi EL MARZOUKI | Paid, Maintenance | Shows maintenance info |
| `1300994-101` | Ahmed Sabil | Paid | Service active |
| `5029012-505` | يوسف السباعي | Unpaid 890 DH | Payment required |
| `3095678-303` | محمد الإدريسي | Paid | Service active |
| `4017890-404` | خديجة العلوي | Paid | Service active |
