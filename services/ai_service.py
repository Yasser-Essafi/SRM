import re


AR_CHARS = re.compile(r"[\u0600-\u06FF]")
ARABIZI_DIGITS = re.compile(r"[23579]")  # 3=ع, 7=ح, 9=ق... etc (heuristique)
DARIJA_TOKENS = re.compile(
    r"\b(salam|slm|3ndi|andi|bghit|baghi|bghina|n9ol|mchkil|mochkil|dial|dyal|lma|ma|daw|dou|dyo|kahraba|kahr|wach|fin|kifach|chno|ch7al)\b",
    re.IGNORECASE
)

def infer_language_from_thread(user_input: str, chat_history: list) -> str:
    # 1) si le thread était déjà en arabe, garde arabe
    last_assistant = ""
    for m in reversed(chat_history or []):
        if m.get("role") == "assistant":
            last_assistant = m.get("content", "")
            break
    if AR_CHARS.search(last_assistant or ""):
        return "ar"

    text = (user_input or "").strip()

    # 2) arabe script
    if AR_CHARS.search(text):
        return "ar"

    # 3) Arabizi/Darija latin => on force "ar"
    if ARABIZI_DIGITS.search(text) or DARIJA_TOKENS.search(text):
        return "ar"

    # 4) FR markers (très simple)
    tl = " " + text.lower() + " "
    fr_markers = [" je ", " vous ", " bonjour", " facture", " électricité", " electricite", " eau", " problème", " coupée", " panne"]
    if any(m in tl for m in fr_markers):
        return "fr"

    return "en"


def detect_service(text: str) -> str:
    tl = (text or "").lower()
    water_kw = ["water", "eau", "ماء", "الماء", "ma2", "lma", "robinet"]
    elec_kw  = ["electricity", "électricité", "electricite", "كهرباء", "الكهرباء", "courant", "prise", "lamp"]
    has_w = any(k in tl for k in water_kw)
    has_e = any(k in tl for k in elec_kw)
    if has_w and has_e:
        return "both"
    if has_w:
        return "water"
    if has_e:
        return "electricity"
    return "unknown"

def mismatch_message(expected: str, got: str, lang: str) -> str:
    if lang == "fr":
        return (f"Je comprends que votre problème concerne {expected}, mais vous avez fourni un numéro de contrat {got}. "
                f"Pouvez-vous m’envoyer le numéro de contrat {expected} ? Si vous ne l’avez pas, envoyez une photo de la facture.")
    if lang == "en":
        return (f"I understand your issue is about {expected}, but you provided a {got} contract number. "
                f"Please send your {expected} contract number. If you don’t have it, upload a photo of the bill.")
    # ar
    exp_ar = "الكهرباء" if expected == "electricity" else "الماء"
    got_ar = "الماء" if got == "water" else "الكهرباء"
    return (f"أفهم أن مشكلتك تخص {exp_ar}، لكن الرقم الذي أرسلته هو رقم عقد {got_ar}. "
            f"من فضلك أرسل رقم عقد {exp_ar}، وإذا لم يكن لديك الرقم يمكنك إرسال صورة واضحة من الفاتورة.")
"""
AI Service using LangChain and Azure OpenAI.
Defines the agent, tools, and Arabic language prompts.
Refactored to support separate water and electricity contracts nice.
"""
from typing import Optional, Union, Dict, Any, List
from datetime import datetime
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnablePassthrough
import json
from config.settings import settings
from data.sql_db import get_user_by_water_contract, get_user_by_electricity_contract, get_zone_by_id
import re
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("Africa/Casablanca")
WINDOW_SECONDS = 2 * 60  # 2 minutes

def _build_reactivation_note(
    payment_timestamp: Optional[datetime],
    service: str,
    seconds_since_payment: Optional[Union[int, float]],
    lang: str = "ar",
    window_seconds: int = WINDOW_SECONDS,
    assume_naive_tz: timezone = timezone.utc,
) -> str:
    """
    Returns a ONE-LINE note to tell the user to wait up to 2 minutes after a recent payment.
    - If seconds_since_payment is None or >= window_seconds => returns "" (no note)
    - If payment_timestamp is naive => assumes UTC by default (assume_naive_tz)
    - service can be: "water"/"electricity" OR Arabic/French labels; we normalize best-effort.
    - lang: "ar" | "fr" | "en"
    """

    # DB seconds is the source of truth
    if seconds_since_payment is None:
        return ""

    try:
        elapsed = float(seconds_since_payment)
    except Exception:
        return ""

    if elapsed < 0:
        elapsed = 0.0

    if elapsed >= float(window_seconds):
        return ""

    # Normalize service
    s = (service or "").strip().lower()
    if s in ("water", "eau", "الماء", "ماء","lma"):
        service_key = "water"
    elif s in ("electricity", "electricite", "électricité", "الكهرباء", "كهرباء","daw"):
        service_key = "electricity"
    else:
        # if caller passes "الماء"/"الكهرباء" or any label, keep it but try to infer
        if "3701" in s or "water" in s or "eau" in s or "ماء" in s or "الماء" in s:
            service_key = "water"
        elif "4801" in s or "electric" in s or "élect" in s or "كهرباء" in s or "الكهرباء" in s:
            service_key = "electricity"
        else:
            service_key = "service"

    labels = {
        "ar": {"water": "الماء", "electricity": "الكهرباء", "service": "الخدمة"},
        "fr": {"water": "eau", "electricity": "électricité", "service": "service"},
        "en": {"water": "water", "electricity": "electricity", "service": "service"},
    }
    lang = (lang or "ar").lower()
    if lang not in labels:
        lang = "ar"

    service_label = labels[lang].get(service_key, labels[lang]["service"])

    # Format payment time in Morocco time (optional)
    paid_at_local_str = ""
    if isinstance(payment_timestamp, datetime):
        ts = payment_timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=assume_naive_tz)
        paid_at_local_str = ts.astimezone(APP_TZ).strftime("%Y-%m-%d %H:%M:%S")

    remaining_seconds = max(0, int(round(float(window_seconds) - elapsed)))
    remaining_minutes = max(1, (remaining_seconds + 59) // 60)  # ceil to minutes, min 1

    if lang == "fr":
        msg = f"Service {service_label} : paiement reçu il y a moins de deux minutes"
        if paid_at_local_str:
            msg += f" (heure du paiement : {paid_at_local_str})"
        msg += f". La remise en service peut prendre jusqu’à deux minutes, merci d’attendre encore environ {remaining_minutes} minute(s) et d’éviter d’ouvrir une nouvelle réclamation pendant ce délai."
        return " ".join(msg.split())

    if lang == "en":
        msg = f"{service_label.capitalize()} service: payment received less than two minutes ago"
        if paid_at_local_str:
            msg += f" (payment time: {paid_at_local_str})"
        msg += f". Reactivation may take up to two minutes, please wait about {remaining_minutes} minute(s) and avoid opening a new ticket during this time."
        return " ".join(msg.split())

    # Default Arabic (MSA)
    msg = f"خدمة {service_label}: تم استقبال الدفع منذ أقل من دقيقتين"
    if paid_at_local_str:
        msg += f" (وقت الدفع: {paid_at_local_str})"
    msg += f". قد تحتاج إعادة التفعيل حوالي دقيقتين، يرجى الانتظار حوالي {remaining_minutes} دقيقة وعدم فتح بلاغ جديد خلال هذه المدة."
    return " ".join(msg.split())
# Tool Functions for Water Service
def _check_water_payment_impl(water_contract: str) -> str:
    """Implementation of water payment check - Returns multilingual data."""
    user = get_user_by_water_contract(water_contract)
    
    if not user:
        return f"WATER_CONTRACT_NOT_FOUND:{water_contract}"
    
    name = user['name']
    is_paid = user['is_paid']
    outstanding_balance = user['outstanding_balance']
    last_payment = user['last_payment_date']
    payment_timestamp = user.get('last_payment_datetime')
    seconds_since = user.get('seconds_since_payment')
    cut_status = user['cut_status']
    cut_reason = user.get('cut_reason')
    reactivation_note = _build_reactivation_note(payment_timestamp, 'الماء', seconds_since)

    if is_paid:
        prefix = (reactivation_note + " ") if reactivation_note else ""
        return f"""{prefix}[WATER_PAYMENT_STATUS: PAID]
Customer: {name}
Service Type: 💧 Water (ماء)
Payment Status: ✅ Paid (مدفوع)
Last Payment: {last_payment}
Outstanding Balance: {outstanding_balance} MAD
Service Status: {cut_status}

Note: Water payment is up to date. If water service is interrupted, it may be due to maintenance in the area.
"""
    else:
        return f"""
[WATER_PAYMENT_STATUS: UNPAID]
Customer: {name}
Service Type: 💧 Water (ماء)
Payment Status: ⚠️ Unpaid (غير مدفوع)
Last Payment: {last_payment}
Outstanding Balance: {outstanding_balance} MAD
Service Status: {cut_status}
Cut Reason: {cut_reason}

Reason: Outstanding balance of {outstanding_balance} MAD. Payment required to restore water service.

Payment Methods:
1. SRM Mobile App
2. Payment agencies (Wafacash, Cash Plus)
3. Bank

Note: Water service is currently interrupted due to non-payment.
"""


def _check_water_maintenance_impl(water_contract: str) -> str:
    """Implementation of water maintenance check - Returns multilingual data."""
    user = get_user_by_water_contract(water_contract)
    
    if not user:
        return f"WATER_CONTRACT_NOT_FOUND:{water_contract}"
    
    zone_id = user['zone_id']
    zone = get_zone_by_id(zone_id)
    
    if not zone:
        return "ZONE_NOT_FOUND"
    
    zone_name = zone['zone_name']
    maintenance_status = zone['maintenance_status']
    affected_services = zone.get('affected_services', '')
    
    if maintenance_status == 'جاري الصيانة' and 'ماء' in str(affected_services):
        outage_reason = zone['outage_reason']
        estimated_restoration = zone['estimated_restoration']
        
        return f"""
[WATER_MAINTENANCE_IN_PROGRESS]
📍 Zone: {zone_name}
⚙️ Maintenance Status: {maintenance_status} (In Progress)

💧 Affected Service: Water (ماء)
Outage Reason: {outage_reason}
Estimated Restoration: {estimated_restoration}

Apologies for the inconvenience. Our teams are working to resolve the issue as soon as possible.
"""
    else:
        return f"""
[NO_WATER_MAINTENANCE]
📍 Zone: {zone_name}
✅ Maintenance Status: No water maintenance

There are no scheduled water maintenance works in your area currently.
If there is a water issue, it may be related to payment or a local problem with the water meter/connections.
"""


# Tool Functions for Electricity Service
def _check_electricity_payment_impl(electricity_contract: str) -> str:
    """Implementation of electricity payment check - Returns multilingual data."""
    user = get_user_by_electricity_contract(electricity_contract)
    
    if not user:
        return f"ELECTRICITY_CONTRACT_NOT_FOUND:{electricity_contract}"
    
    name = user['name']
    is_paid = user['is_paid']
    outstanding_balance = user['outstanding_balance']
    last_payment = user['last_payment_date']
    payment_timestamp = user.get('last_payment_datetime')
    seconds_since = user.get('seconds_since_payment')
    cut_status = user['cut_status']
    cut_reason = user.get('cut_reason')
    reactivation_note = _build_reactivation_note(payment_timestamp, 'الكهرباء', seconds_since)

    if is_paid:
        prefix = (reactivation_note + " ") if reactivation_note else ""
        return f"""{prefix}[ELECTRICITY_PAYMENT_STATUS: PAID]
Customer: {name}
Service Type: ⚡ Electricity (كهرباء)
Payment Status: ✅ Paid (مدفوع)
Last Payment: {last_payment}
Outstanding Balance: {outstanding_balance} MAD
Service Status: {cut_status}

Note: Electricity payment is up to date. If electricity service is interrupted, it may be due to maintenance in the area.
"""
    else:
        return f"""
[ELECTRICITY_PAYMENT_STATUS: UNPAID]
Customer: {name}
Service Type: ⚡ Electricity (كهرباء)
Payment Status: ⚠️ Unpaid (غير مدفوع)
Last Payment: {last_payment}
Outstanding Balance: {outstanding_balance} MAD
Service Status: {cut_status}
Cut Reason: {cut_reason}

Reason: Outstanding balance of {outstanding_balance} MAD. Payment required to restore electricity service.

Payment Methods:
1. SRM Mobile App
2. Payment agencies (Wafacash, Cash Plus)
3. Bank

Note: Electricity service is currently interrupted due to non-payment.
"""


def _check_electricity_maintenance_impl(electricity_contract: str) -> str:
    """Implementation of electricity maintenance check - Returns multilingual data."""
    user = get_user_by_electricity_contract(electricity_contract)
    
    if not user:
        return f"ELECTRICITY_CONTRACT_NOT_FOUND:{electricity_contract}"
    
    zone_id = user['zone_id']
    zone = get_zone_by_id(zone_id)
    
    if not zone:
        return "ZONE_NOT_FOUND"
    
    zone_name = zone['zone_name']
    maintenance_status = zone['maintenance_status']
    affected_services = zone.get('affected_services', '')
    
    if maintenance_status == 'جاري الصيانة' and 'كهرباء' in str(affected_services):
        outage_reason = zone['outage_reason']
        estimated_restoration = zone['estimated_restoration']
        
        return f"""
[ELECTRICITY_MAINTENANCE_IN_PROGRESS]
📍 Zone: {zone_name}
⚙️ Maintenance Status: {maintenance_status} (In Progress)

⚡ Affected Service: Electricity (كهرباء)
Outage Reason: {outage_reason}
Estimated Restoration: {estimated_restoration}

Apologies for the inconvenience. Our teams are working to resolve the issue as soon as possible.
"""
    else:
        return f"""
[NO_ELECTRICITY_MAINTENANCE]
📍 Zone: {zone_name}
✅ Maintenance Status: No electricity maintenance

There are no scheduled electricity maintenance works in your area currently.
If there is an electricity issue, it may be related to payment or a local problem with the electricity meter/connections.
"""


# Create tool wrappers with decorator
@tool
def check_water_payment(water_contract: str) -> str:
    """Check water payment status and outstanding balance for a customer by water contract number.
    Use this to verify if customer has unpaid water bills or water payment is up to date.
    
    Vérifier l'état du paiement de l'eau et le solde impayé d'un client par numéro de contrat eau.
    التحقق من حالة دفع الماء والرصيد المستحق للعميل برقم عقد الماء.
    
    Args:
        water_contract: Water Contract Number (format: 3701455886 / 1014871)
        
    Returns:
        str: Water payment status information that you must translate to customer's language
    """

    return _check_water_payment_impl(water_contract)


@tool
def check_water_maintenance(water_contract: str) -> str:
    """Check for water maintenance and outages in customer's zone. Requires water contract number.
    Use this to verify if there are scheduled water maintenance works affecting water service.
    
    Vérifier les travaux de maintenance de l'eau et les coupures d'eau dans la zone du client.
    التحقق من أعمال صيانة الماء وانقطاعات الماء في منطقة العميل.
    
    Args:
        water_contract: Water Contract Number (format: 3701455886 / 1014871)
        
    Returns:
        str: Water maintenance information that you must translate to customer's language
    """
    return _check_water_maintenance_impl(water_contract)


@tool
def check_electricity_payment(electricity_contract: str) -> str:
    """Check electricity payment status and outstanding balance for a customer by electricity contract number.
    Use this to verify if customer has unpaid electricity bills or electricity payment is up to date.
    
    Vérifier l'état du paiement de l'électricité et le solde impayé d'un client par numéro de contrat électricité.
    التحقق من حالة دفع الكهرباء والرصيد المستحق للعميل برقم عقد الكهرباء.
    
    Args:
        electricity_contract: Electricity Contract Number (format: 4801566997 / 2025982)
        
    Returns:
        str: Electricity payment status information that you must translate to customer's language
    """
    return _check_electricity_payment_impl(electricity_contract)


@tool
def check_electricity_maintenance(electricity_contract: str) -> str:
    """Check for electricity maintenance and outages in customer's zone. Requires electricity contract number.
    Use this to verify if there are scheduled electricity maintenance works affecting electricity service.
    
    Vérifier les travaux de maintenance de l'électricité et les coupures d'électricité dans la zone du client.
    التحقق من أعمال صيانة الكهرباء وانقطاعات الكهرباء في منطقة العميل.
    
    Args:
        electricity_contract: Electricity Contract Number (format: 4801566997 / 2025982)
        
    Returns:
        str: Electricity maintenance information that you must translate to customer's language
    """
    return _check_electricity_maintenance_impl(electricity_contract)


# Collect tools
tools = [check_water_payment, check_water_maintenance, check_electricity_payment, check_electricity_maintenance]


# Multilingual System Prompt
SYSTEM_PROMPT = """You are a customer service assistant for SRM (Water and Electricity Management Company).

Your role:
1. **CRITICAL: Detect and respond in the SAME language as the customer**
   - If customer writes in Moroccan Darija → respond in Modern Standard Arabic
   - If customer writes in Arabic (فصحى) → respond in Modern Standard Arabic
   - If customer writes in French → respond in French
   - If customer writes in English → respond in English
   - If customer writes in Spanish → respond in Spanish

2. **CONVERSATION FLOW - FOLLOW STRICTLY**:
   
   **STEP 1 - IDENTIFY THE PROBLEM**:
   - Automatically detect from the customer's message if the issue is about:
     * Water ONLY (ماء, eau, water, agua)
     * Electricity ONLY (كهرباء, électricité, electricity, electricidad)
     * BOTH water AND electricity
   - DO NOT ask "what is your problem?" - understand it from their message
   - Common phrases: "ما عندي الماء", "l'électricité est coupée", "pas d'eau", "انقطاع الكهرباء"
   - **MENTION what you understood** before asking for contract number:
     * Arabic: "أفهم أن لديك مشكلة في [الماء/الكهرباء/الماء والكهرباء]"
     * French: "Je comprends que vous avez un problème de [eau/électricité/eau et électricité]"
     * English: "I understand you have a [water/electricity/water and electricity] problem"
   
   **STEP 2 - ASK FOR THE APPROPRIATE CONTRACT NUMBER**:
   
   A) **If WATER problem detected**:
      - Ask for WATER contract number (رقم عقد الماء, numéro de contrat eau, water contract number)
      - DO NOT give examples or format in the question
      - Offer alternative: suggest uploading bill image if they don't have contract number
      - Arabic: "من فضلك، هل يمكنك إعطائي رقم عقد الماء الخاص بك؟ إذا لم يكن لديك الرقم، يمكنك رفع صورة فاتورة الماء وسأقوم باستخراجه."
      - French: "Pourriez-vous me donner votre numéro de contrat d'eau, s'il vous plaît ? Si vous ne l'avez pas, vous pouvez télécharger une photo de votre facture d'eau et je l'extrairai."
      - English: "Could you please provide your water contract number? If you don't have it, you can upload a photo of your water bill and I will extract it."
      
   B) **If ELECTRICITY problem detected**:
      - Ask for ELECTRICITY contract number (رقم عقد الكهرباء, numéro de contrat électricité, electricity contract number)
      - DO NOT give examples or format in the question
      - Offer alternative: suggest uploading bill image if they don't have contract number
      - Arabic: "من فضلك، هل يمكنك إعطائي رقم عقد الكهرباء الخاص بك؟ إذا لم يكن لديك الرقم، يمكنك رفع صورة فاتورة الكهرباء وسأقوم باستخراجه."
      - French: "Pourriez-vous me donner votre numéro de contrat d'électricité, s'il vous plaît ? Si vous ne l'avez pas, vous pouvez télécharger une photo de votre facture d'électricité et je l'extrairai."
      - English: "Could you please provide your electricity contract number? If you don't have it, you can upload a photo of your electricity bill and I will extract it."
      
   C) **If BOTH water AND electricity problems detected**:
      - FIRST ask for WATER contract number
      - THEN after analyzing water, ask for ELECTRICITY contract number
      - Handle SEQUENTIALLY - one service at a time
      - DO NOT give examples or format
      - Offer bill upload alternative
      - Arabic: "دعنا نتحقق من الماء أولاً. من فضلك، أعطني رقم عقد الماء. إذا لم يكن لديك الرقم، يمكنك رفع صورة الفاتورة."
      - French: "Vérifions d'abord l'eau. S'il vous plaît, donnez-moi le numéro de contrat d'eau. Si vous ne l'avez pas, vous pouvez télécharger une photo de la facture."
      - English: "Let's check water first. Please provide your water contract number. If you don't have it, you can upload a photo of the bill."
   
   **IMPORTANT - If customer says they don't have the contract number**:
   - DO NOT ask again for the number
   - Immediately suggest uploading bill image
   - Arabic: "لا مشكلة! يمكنك رفع صورة واضحة لفاتورة [الماء/الكهرباء] وسأقوم باستخراج رقم العقد تلقائياً من الصورة."
   - French: "Pas de problème ! Vous pouvez télécharger une photo claire de votre facture [d'eau/d'électricité] et j'extrairai automatiquement le numéro de contrat de l'image."
   - English: "No problem! You can upload a clear photo of your [water/electricity] bill and I will automatically extract the contract number from the image."
   
   **IMPORTANT**:
   - If contract number is already in the message, use it immediately
   - If customer uploads a bill image, system extracts contract automatically
   - Water contracts start with 3701XXXXXX
   - Electricity contracts start with 4801XXXXXX
   
   **STEP 3 - CHECK AND RESPOND**:
   - Use the appropriate tools based on problem type:
     * Water problem → check_water_payment + check_water_maintenance
     * Electricity problem → check_electricity_payment + check_electricity_maintenance
     * Both → check water first, then electricity (sequential)
   - Analyze the results and provide clear explanation
   - Link the response to the specific service the customer asked about
   
3. **RESPONSE RULES**:
   - Answer ONLY about the service the customer asked about
   - DO NOT mention other services unless they are ALSO affected
   - If water is the problem and electricity is fine, talk about water ONLY
   - If electricity is the problem and water is fine, talk about electricity ONLY
   - Only mention both services if BOTH are interrupted

⚠️ CRITICAL FORMATTING RULES:
- **NO MARKDOWN**: Do not use **, -, #, bullet points, or any special formatting
- **PLAIN TEXT ONLY**: Write in natural, flowing paragraphs
- **NO LINE BREAKS**: Use continuous text, not separated lines
- Respond in natural conversational style like speaking to a person
- Use customer's name when addressing them if available

⚠️ SPECIAL RULE - When problem is NOT payment or maintenance:
- If customer reports service interruption BUT:
  1. Payment is up to date (is_paid = True)
  2. No maintenance for that service in the area
  3. Service status is OK in system (cut_status = OK)
- This means: Local technical issue at customer's home, NOT payment or maintenance
- Tell customer clearly: "The problem is not due to payment or maintenance. It appears to be a technical issue at your location."
- Advise to call technical support to send a technician
- Technical support number: **05-22-XX-XX-XX**

Correct examples:
- Customer asks about water and ONLY water is cut:
  ✅ Talk about water only, don't mention electricity
  
- Customer asks about electricity and ONLY electricity is cut:
  ✅ Talk about electricity only, don't mention water
  
- Customer asks about both services:
  ✅ Ask for water contract first, explain water situation
  ✅ Then ask for electricity contract, explain electricity situation

- Customer asks about water, water payment current, no maintenance:
  ✅ Say: "After checking your water account, I found your payments are up to date and there is no water maintenance in your area. The problem may be technical at your home. I recommend calling technical support at 05-22-XX-XX-XX to send a technician to inspect your water connections and meter."

Important rules:
- **ALWAYS respond in the SAME language the customer is using**
- **NO markdown or special formatting** - plain paragraph text only
- Be polite and professional with natural conversational tone
- **Identify the problem type (water/electricity/both) from customer's message**
- Ask for the CORRECT contract number for the service in question
- Water contracts: 3701XXXXXX / XXXXXXX
- Electricity contracts: 4801XXXXXX / XXXXXXX
- Handle BOTH problems SEQUENTIALLY (water first, then electricity)
- Focus ONLY on the reported problem
- Use continuous paragraphs without bullet points or lists
- Provide practical solutions at the end in natural sentences
- If the issue is non-payment, direct customer to payment methods in plain text
- If the issue is maintenance, provide estimated repair time in conversational style
- For local technical issues, provide technical support number: 05-22-XX-XX-XX
- Do not invent information - only use available tools

⚠️ Reactivation rule (recent payment):
- If the tool output mentions reactivation in progress or waiting after a recent payment, you MUST tell the customer clearly to wait up to 2 minutes for service to be restored, and include the time hint from the tool output. Do not drop or paraphrase this note.

Language-specific greetings:
- Arabic: "مرحباً بك في خدمة عملاء الشركة الجهوية متعددة الاختصاصات. كيف يمكنني مساعدتك اليوم؟"
- French: "Bienvenue au service client SRM. Comment puis-je vous aider aujourd'hui ?"
- English: "Welcome to SRM customer service. How can I help you today?"
- Spanish: "Bienvenido al servicio al cliente de SRM. ¿Cómo puedo ayudarle hoy?"

Start by greeting the customer in their language and asking about their issue."""


def initialize_agent() -> Optional[AzureChatOpenAI]:
    """
    Initialize the LangChain LLM with Azure OpenAI and bind tools.
    
    Returns:
        AzureChatOpenAI: Configured LLM with tools or None if initialization fails
    """
    try:
        # Initialize Azure OpenAI
        llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Bind tools to the LLM
        llm_with_tools = llm.bind_tools(tools)
        
        return llm_with_tools
        
    except Exception as e:
        print(f"Error initializing agent: {str(e)}")
        return None


def get_agent_executor() -> Optional[AzureChatOpenAI]:
    """
    Get or create the agent (singleton pattern).
    
    Returns:
        AzureChatOpenAI: The initialized LLM with tools
    """
    return initialize_agent()


# détecte "3701.... / ...." ou "4801.... / ...." (espaces optionnels)
WATER_RE = re.compile(r"(3701\d{6,}\s*/\s*\d{4,})")
ELEC_RE  = re.compile(r"(4801\d{6,}\s*/\s*\d{4,})")

def run_agent(agent: AzureChatOpenAI, user_input: str, chat_history: list = None, language: str = "ar") -> str:
    def _one_line(text: str) -> str:
        return " ".join((text or "").split())

    def _extract_reactivation_note(tool_text: str) -> str:
        if not tool_text:
            return ""
        for line in str(tool_text).splitlines():
            s = line.strip()
            if s.startswith("خدمة ") and "تم استقبال الدفع" in s:
                return s
        return ""

    # ✅ réponse déterministe eau
    def _answer_water(contract: str, lang: str) -> str:
        user = get_user_by_water_contract(contract)
        if not user:
            if lang == "fr":
                return _one_line(f"Numéro de contrat d'eau introuvable : {contract}. Merci de vérifier ou d'envoyer une photo de la facture.")
            if lang == "en":
                return _one_line(f"Water contract number not found: {contract}. Please check or upload a clear photo of the bill.")
            return _one_line(f"لم أتمكن من العثور على عقد الماء {contract}. يرجى التأكد من الرقم أو إرسال صورة واضحة من الفاتورة.")

        zone = get_zone_by_id(user["zone_id"]) if user.get("zone_id") is not None else None

        payment_ts = user.get("last_payment_datetime")
        seconds_since = user.get("seconds_since_payment")
        note = _build_reactivation_note(payment_ts, "الماء", seconds_since)

        is_paid = bool(user.get("is_paid"))
        outstanding = float(user.get("outstanding_balance") or 0.0)
        cut_status = (user.get("cut_status") or "").strip()
        zone_name = (zone.get("zone_name") if zone else "") or ("votre zone" if lang=="fr" else ("your area" if lang=="en" else "منطقتك"))
        maint_status = (zone.get("maintenance_status") if zone else "") or ""
        affected = str(zone.get("affected_services") or "") if zone else ""
        outage_reason = (zone.get("outage_reason") if zone else "") or ""
        estimated = (zone.get("estimated_restoration") if zone else "") or ""

        if maint_status == "جاري الصيانة" and "ماء" in affected:
            base = {
                "fr": f"Après vérification du contrat d'eau {contract}, des travaux de maintenance de l'eau sont en cours dans {zone_name}.",
                "en": f"After checking water contract {contract}, water maintenance is ongoing in {zone_name}.",
                "ar": f"بعد التحقق من عقد الماء {contract}، توجد أعمال صيانة للماء في {zone_name} حالياً."
            }.get(lang, f"بعد التحقق من عقد الماء {contract}، توجد أعمال صيانة للماء في {zone_name} حالياً.")
            if outage_reason:
                base += f" سبب الانقطاع: {outage_reason}."
            if estimated:
                base += f" الوقت المتوقع لعودة الخدمة: {estimated}."
            if note:
                return _one_line(f"{note} {base}")
            return _one_line(base)

        if (not is_paid) or (outstanding > 0.0):
            if lang == "fr":
                return _one_line(f"Après vérification du contrat d'eau {contract}, un solde impayé de {outstanding:.2f} MAD est détecté. Veuillez régler le montant pour éviter l'interruption ou rétablir le service. Après paiement, la réactivation peut prendre un certain temps.")
            if lang == "en":
                return _one_line(f"After checking water contract {contract}, an outstanding balance of {outstanding:.2f} MAD is detected. Please pay to avoid interruption or restore service. After payment, reactivation may take some time.")
            return _one_line(
                f"بعد التحقق من عقد الماء {contract}، يظهر أن هناك مبلغاً مستحقاً قدره {outstanding:.2f} درهم وأن حالة الدفع غير مكتملة. "
                f"يرجى أداء المبلغ لتفادي الانقطاع أو لإرجاع الخدمة، وبعد الدفع قد تحتاج عملية التفعيل بعض الوقت."
            )

        if note:
            if lang == "fr":
                return _one_line(f"{note} Après vérification du contrat d'eau {contract}, vos paiements sont à jour et il n'y a pas de maintenance de l'eau dans {zone_name} actuellement. Si la coupure persiste après deux minutes, il s'agit probablement d'un problème technique chez vous. Merci de contacter le support technique au 05-22-XX-XX-XX.")
            if lang == "en":
                return _one_line(f"{note} After checking water contract {contract}, your payments are up to date and there is no water maintenance in {zone_name} currently. If the outage continues after two minutes, it is likely a technical issue at your home. Please contact technical support at 05-22-XX-XX-XX.")
            return _one_line(
                f"{note} بعد التحقق من عقد الماء {contract}، دفعاتك محدثة ولا توجد صيانة للماء في {zone_name} حالياً. "
                f"إذا كان الانقطاع مستمراً بعد انتهاء مدة الدقيقتين، فالسبب غالباً تقني في منزلك. "
                f"أنصحك بالاتصال بالدعم الفني على الرقم 05-22-XX-XX-XX لإرسال تقني لفحص التوصيلات وعداد الماء."
            )

        if lang == "fr":
            return _one_line(f"Après vérification du contrat d'eau {contract}, vos paiements sont à jour et il n'y a pas de maintenance de l'eau dans {zone_name} actuellement. Si le problème persiste, il s'agit probablement d'un souci technique chez vous. Merci de contacter le support technique au 05-22-XX-XX-XX.")
        if lang == "en":
            return _one_line(f"After checking water contract {contract}, your payments are up to date and there is no water maintenance in {zone_name} currently. If the problem persists, it is likely a technical issue at your home. Please contact technical support at 05-22-XX-XX-XX.")
        return _one_line(
            f"بعد التحقق من عقد الماء {contract}، دفعاتك محدثة ولا توجد صيانة للماء في {zone_name} حالياً وحالة الخدمة في النظام {cut_status or 'OK'}. "
            f"يبدو أن المشكلة تقنية في منزلك. أنصحك بالاتصال بالدعم الفني على الرقم 05-22-XX-XX-XX لإرسال تقني لفحص التوصيلات وعداد الماء."
        )

    # ✅ réponse déterministe كهرباء (نفس المنطق)
    def _answer_elec(contract: str, lang: str) -> str:
        user = get_user_by_electricity_contract(contract)
        if not user:
            if lang == "fr":
                return _one_line(f"Numéro de contrat d'électricité introuvable : {contract}. Merci de vérifier ou d'envoyer une photo de la facture.")
            if lang == "en":
                return _one_line(f"Electricity contract number not found: {contract}. Please check or upload a clear photo of the bill.")
            return _one_line(f"لم أتمكن من العثور على عقد الكهرباء {contract}. يرجى التأكد من الرقم أو إرسال صورة واضحة من الفاتورة.")

        zone = get_zone_by_id(user["zone_id"]) if user.get("zone_id") is not None else None
        payment_ts = user.get("last_payment_datetime")
        seconds_since = user.get("seconds_since_payment")
        note = _build_reactivation_note(payment_ts, "الكهرباء", seconds_since)

        is_paid = bool(user.get("is_paid"))
        outstanding = float(user.get("outstanding_balance") or 0.0)
        cut_status = (user.get("cut_status") or "").strip()
        zone_name = (zone.get("zone_name") if zone else "") or ("votre zone" if lang=="fr" else ("your area" if lang=="en" else "منطقتك"))
        maint_status = (zone.get("maintenance_status") if zone else "") or ""
        affected = str(zone.get("affected_services") or "") if zone else ""
        outage_reason = (zone.get("outage_reason") if zone else "") or ""
        estimated = (zone.get("estimated_restoration") if zone else "") or ""

        if maint_status == "جاري الصيانة" and "كهرباء" in affected:
            base = {
                "fr": f"Après vérification du contrat d'électricité {contract}, des travaux de maintenance de l'électricité sont en cours dans {zone_name}.",
                "en": f"After checking electricity contract {contract}, electricity maintenance is ongoing in {zone_name}.",
                "ar": f"بعد التحقق من عقد الكهرباء {contract}، توجد أعمال صيانة للكهرباء في {zone_name} حالياً."
            }.get(lang, f"بعد التحقق من عقد الكهرباء {contract}، توجد أعمال صيانة للكهرباء في {zone_name} حالياً.")
            if outage_reason:
                base += f" سبب الانقطاع: {outage_reason}."
            if estimated:
                base += f" الوقت المتوقع لعودة الخدمة: {estimated}."
            if note:
                return _one_line(f"{note} {base}")
            return _one_line(base)

        if (not is_paid) or (outstanding > 0.0):
            if lang == "fr":
                return _one_line(f"Après vérification du contrat d'électricité {contract}, un solde impayé de {outstanding:.2f} MAD est détecté. Veuillez régler le montant pour éviter l'interruption ou rétablir le service. Après paiement, la réactivation peut prendre un certain temps.")
            if lang == "en":
                return _one_line(f"After checking electricity contract {contract}, an outstanding balance of {outstanding:.2f} MAD is detected. Please pay to avoid interruption or restore service. After payment, reactivation may take some time.")
            return _one_line(
                f"بعد التحقق من عقد الكهرباء {contract}، يظهر أن هناك مبلغاً مستحقاً قدره {outstanding:.2f} درهم وأن حالة الدفع غير مكتملة. "
                f"يرجى أداء المبلغ لتفادي الانقطاع أو لإرجاع الخدمة، وبعد الدفع قد تحتاج عملية التفعيل بعض الوقت."
            )

        if note:
            if lang == "fr":
                return _one_line(f"{note} Après vérification du contrat d'électricité {contract}, vos paiements sont à jour et il n'y a pas de maintenance de l'électricité dans {zone_name} actuellement. Si la coupure persiste après deux minutes, il s'agit probablement d'un problème technique chez vous. Merci de contacter le support technique au 05-22-XX-XX-XX.")
            if lang == "en":
                return _one_line(f"{note} After checking electricity contract {contract}, your payments are up to date and there is no electricity maintenance in {zone_name} currently. If the outage continues after two minutes, it is likely a technical issue at your home. Please contact technical support at 05-22-XX-XX-XX.")
            return _one_line(
                f"{note} بعد التحقق من عقد الكهرباء {contract}، دفعاتك محدثة ولا توجد صيانة للكهرباء في {zone_name} حالياً. "
                f"إذا استمر الانقطاع بعد انتهاء مدة الدقيقتين، فالسبب غالباً تقني في منزلك. "
                f"أنصحك بالاتصال بالدعم الفني على الرقم 05-22-XX-XX-XX."
            )

        if lang == "fr":
            return _one_line(f"Après vérification du contrat d'électricité {contract}, vos paiements sont à jour et il n'y a pas de maintenance de l'électricité dans {zone_name} actuellement. Si le problème persiste, il s'agit probablement d'un souci technique chez vous. Merci de contacter le support technique au 05-22-XX-XX-XX.")
        if lang == "en":
            return _one_line(f"After checking electricity contract {contract}, your payments are up to date and there is no electricity maintenance in {zone_name} currently. If the problem persists, it is likely a technical issue at your home. Please contact technical support at 05-22-XX-XX-XX.")
        return _one_line(
            f"بعد التحقق من عقد الكهرباء {contract}، دفعاتك محدثة ولا توجد صيانة للكهرباء في {zone_name} حالياً وحالة الخدمة في النظام {cut_status or 'OK'}. "
            f"يبدو أن المشكلة تقنية في منزلك. أنصحك بالاتصال بالدعم الفني على الرقم 05-22-XX-XX-XX."
        )

    try:
        if chat_history is None:
            chat_history = []

        # Detect language from user_input if not provided
        lang = language or infer_language_from_thread(user_input, chat_history or [])

        # 1. Determine requested service from user_input + chat_history
        service = detect_service(user_input)
        # If ambiguous, try to infer from chat_history
        if service == "unknown" and chat_history:
            for msg in reversed(chat_history):
                if msg.get("role") == "user":
                    service = detect_service(msg.get("content", ""))
                    if service != "unknown":
                        break

        w = WATER_RE.search(user_input or "")
        e = ELEC_RE.search(user_input or "")

        # 2. Only accept the correct contract type for the requested service
        if service == "water":
            if w:
                return _answer_water(w.group(1).strip(), lang)
            elif e:
                # User gave electricity contract for water service
                return _one_line(mismatch_message("water", "electricity", lang))
        elif service == "electricity":
            if e:
                return _answer_elec(e.group(1).strip(), lang)
            elif w:
                # User gave water contract for electricity service
                return _one_line(mismatch_message("electricity", "water", lang))
        elif service == "both":
            # If both, handle sequentially: water first, then electricity
            if w:
                return _answer_water(w.group(1).strip(), lang)
            elif e:
                # If only electricity contract, ask for water contract first
                return _one_line(mismatch_message("water", "electricity", lang))
            else:
                # No contract provided, fallback to LLM
                pass
        # If no contract or ambiguous, fallback to LLM

        language_instruction = {
            "ar": "\n\n⚠️ CRITICAL OVERRIDE: You MUST respond ONLY in Modern Standard Arabic (فصحى).",
            "en": "\n\n⚠️ CRITICAL OVERRIDE: You MUST respond ONLY in English.",
            "fr": "\n\n⚠️ CRITICAL OVERRIDE: You MUST respond ONLY in French.",
        }.get(lang, "\n\n⚠️ CRITICAL OVERRIDE: You MUST respond ONLY in Modern Standard Arabic (فصحى).")

        messages = [SystemMessage(content=SYSTEM_PROMPT + language_instruction)]

        for msg in chat_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content", "")))

        messages.append(HumanMessage(content=user_input))

        response = agent.invoke(messages)

        # Tool-calls path (optional)
        if hasattr(response, "tool_calls") and response.tool_calls:
            messages.append(response)
            reactivation_hint = ""

            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id")

                tool_result = None
                for t in tools:
                    if t.name == tool_name:
                        tool_result = t.invoke(tool_args)
                        break

                if tool_result is not None:
                    hint = _extract_reactivation_note(str(tool_result))
                    if hint:
                        reactivation_hint = hint

                    messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call_id))

            final_response = agent.invoke(messages)
            final_text = (final_response.content or "").strip()
            if reactivation_hint and ("تم استقبال الدفع" not in final_text):
                final_text = f"{reactivation_hint} {final_text}"
            return _one_line(final_text)

        return _one_line(response.content or "")

    except Exception as e:
        print("Error running agent:", str(e))
        return _one_line(f"عذراً، حدث خطأ: {str(e)}")


ACTION_EXTRACTOR_PROMPT = """You extract payment actions from a customer service conversation.
Return ONLY valid JSON. No markdown, no extra text.

Goal:
Detect whether the user intends to pay an invoice, using semantic understanding (no keyword lists).

Output rules:
- If the user is asking to pay NOW (or requesting to proceed with payment) AND a contract_number is present or clearly implied, output:
  {
    "type": "PAY_INVOICE",
    "contract_number": "<as shown or inferred from context>",
    "invoice_type": "electricity" | "water"
  }

- If the user is asking to pay NOW but contract_number is missing or unclear, output:
  {
    "type": "NEED_CONTRACT",
    "invoice_type": "electricity" | "water" | null
  }

- Otherwise output:
  { "type": null }

Constraints:
- Do NOT set PAY_INVOICE just because a contract number appears. The user must express an intent to pay.
- Infer invoice_type from context (water/electricity). If not enough info, set invoice_type to null.
"""


def _get_action_llm() -> AzureChatOpenAI:
    # Use a dedicated LLM WITHOUT tools to avoid tool_calls messing up JSON
    return AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        temperature=0.0,
        max_tokens=250,
    )

def extract_action(user_input: str, chat_history: list) -> dict:
    """LLM-based action extraction from context (no regex)."""

    # ✅ 1) Construire un contexte STRUCTURÉ (JSON)
    payload = {
        "history": chat_history or [],
        "last_user_message": user_input
    }

    prompt = json.dumps(payload, ensure_ascii=False)

    llm = _get_action_llm()

    resp = llm.invoke([
        SystemMessage(content=ACTION_EXTRACTOR_PROMPT),
        HumanMessage(content=prompt),
    ])

    content = (resp.content or "").strip()

    # small safety cleanup if model adds ```json ... ```
    if content.startswith("```"):
        content = content.strip("`")
        content = content.replace("json", "", 1).strip()

    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            return {"type": None}
        return data
    except Exception:
        return {"type": None}
