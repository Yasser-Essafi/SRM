"""
AI Service using LangChain and Azure OpenAI.
Defines the agent, tools, and Arabic language prompts.
Refactored to support separate water and electricity contracts nice.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnablePassthrough
from config.settings import settings
from data.mock_db import get_user_by_water_contract, get_user_by_electricity_contract, get_zone_by_id


def _build_reactivation_note(payment_timestamp: Optional[str], service_label: str) -> str:
    """Return a short bilingual note if payment is recent and reactivation (<=2h) may still be running."""
    if not payment_timestamp:
        return ""
    try:
        paid_at = datetime.fromisoformat(payment_timestamp)
    except ValueError:
        return ""

    now = datetime.now()
    if paid_at > now:
        return ""

    elapsed_seconds = (now - paid_at).total_seconds()
    window_seconds = 2 * 60 * 60  # 2 hours
    if elapsed_seconds < window_seconds:
        remaining_minutes = max(1, int((window_seconds - elapsed_seconds) // 60))
        paid_at_str = paid_at.strftime('%Y-%m-%d %H:%M')
        return (
            f"⏳ خدمة {service_label}: تم استقبال الدفع في {paid_at_str}. "
            f"قد تستغرق إعادة التفعيل حتى ساعتين، يرجى الانتظار ~{remaining_minutes} دقيقة، وعدم إعادة فتح بلاغ جديد خلال هذه المدة.\n"
            f"Reactivation in progress for {service_label}. Payment received at {paid_at_str}. "
            f"Please allow up to 2 hours (~{remaining_minutes} minutes remaining) and avoid opening a new ticket during this window."
        )
    return ""


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
    cut_status = user['cut_status']
    cut_reason = user.get('cut_reason')
    reactivation_note = _build_reactivation_note(payment_timestamp, 'water')
    
    if is_paid:
        return f"""
[WATER_PAYMENT_STATUS: PAID]
Customer: {name}
Service Type: 💧 Water (ماء)
Payment Status: ✅ Paid (مدفوع)
Last Payment: {last_payment}
Outstanding Balance: {outstanding_balance} MAD
Service Status: {cut_status}

{reactivation_note}

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
    cut_status = user['cut_status']
    cut_reason = user.get('cut_reason')
    reactivation_note = _build_reactivation_note(payment_timestamp, 'electricity')
    
    if is_paid:
        return f"""
[ELECTRICITY_PAYMENT_STATUS: PAID]
Customer: {name}
Service Type: ⚡ Electricity (كهرباء)
Payment Status: ✅ Paid (مدفوع)
Last Payment: {last_payment}
Outstanding Balance: {outstanding_balance} MAD
Service Status: {cut_status}

{reactivation_note}

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
- If the tool output mentions reactivation in progress or waiting after a recent payment, you MUST tell the customer clearly to wait up to 2 hours for service to be restored, and include the time hint from the tool output. Do not drop or paraphrase this note.

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


def run_agent(agent: AzureChatOpenAI, user_input: str, chat_history: list = None, language: str = 'ar') -> str:
    """
    Run the agent with user input.
    
    Args:
        agent: The LLM with bound tools
        user_input: User's message
        chat_history: Previous chat messages
        language: Preferred response language ('ar', 'en', 'fr')
        
    Returns:
        str: Agent's response
    """
    try:
        if chat_history is None:
            chat_history = []
        
        # Language-specific instruction (OVERRIDE automatic detection)
        language_instruction = {
            'ar': '\n\n⚠️ CRITICAL OVERRIDE: You MUST respond ONLY in Modern Standard Arabic (فصحى), regardless of the language the user writes in. Ignore rule #1 about language detection.',
            'en': '\n\n⚠️ CRITICAL OVERRIDE: You MUST respond ONLY in English, regardless of the language the user writes in. Ignore rule #1 about language detection.',
            'fr': '\n\n⚠️ CRITICAL OVERRIDE: You MUST respond ONLY in French, regardless of the language the user writes in. Ignore rule #1 about language detection.'
        }.get(language, '\n\n⚠️ CRITICAL OVERRIDE: You MUST respond ONLY in Modern Standard Arabic (فصحى), regardless of the language the user writes in. Ignore rule #1 about language detection.')
        
        # Build messages list with language instruction
        messages = [SystemMessage(content=SYSTEM_PROMPT + language_instruction)]
        
        # Add chat history
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current user input
        messages.append(HumanMessage(content=user_input))
        
        # Get response from agent
        response = agent.invoke(messages)
        
        # Check if agent wants to use tools
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Add the AI response with tool calls to messages
            messages.append(response)
            
            # Execute tools and create tool messages
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_call_id = tool_call['id']
                
                # Find and execute the tool
                tool_result = None
                for t in tools:
                    if t.name == tool_name:
                        tool_result = t.invoke(tool_args)
                        break
                
                # Add tool message with proper tool_call_id
                if tool_result:
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call_id
                    ))
            
            # Get final response after tool execution
            final_response = agent.invoke(messages)
            return final_response.content
        
        return response.content
        
    except Exception as e:
        print(f"Error running agent: {str(e)}")
        return f"عذراً، حدث خطأ: {str(e)}"
