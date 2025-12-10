"""
AI Service using LangChain and Azure OpenAI.
Defines the agent, tools, and Arabic language prompts.
"""
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnablePassthrough
from config.settings import settings
from data.mock_db import get_user_by_contract, get_zone_by_id


# Tool Functions (without decorator for direct calling)
def _check_payment_impl(contract: str) -> str:
    """Implementation of payment check - Returns multilingual data."""
    user = get_user_by_contract(contract)
    
    if not user:
        return f"CONTRACT_NOT_FOUND:{contract}"
    
    name = user['name']
    payment_status = user['payment_status']
    outstanding_balance = user['outstanding_balance']
    last_payment = user['last_payment_date']
    service_status = user['service_status']
    service_type = user['service_type']
    
    # Determine service emoji
    service_emoji = "💧⚡" if service_type == "ماء وكهرباء" else ("💧" if service_type == "ماء" else "⚡")
    
    if payment_status == 'مدفوع':
        return f"""
[PAYMENT_STATUS: PAID]
Customer: {name}
Service Type: {service_emoji} {service_type}
Payment Status: ✅ {payment_status} (Paid)
Last Payment: {last_payment}
Outstanding Balance: {outstanding_balance} MAD
Service Status: {service_status}

Note: Payment is up to date. If service is interrupted, it may be due to maintenance in the area.
Important: Match service type ({service_type}) with customer's reported problem.
"""
    else:
        return f"""
[PAYMENT_STATUS: UNPAID]
Customer: {name}
Service Type: {service_emoji} {service_type}
Payment Status: ⚠️ {payment_status} (Unpaid)
Last Payment: {last_payment}
Outstanding Balance: {outstanding_balance} MAD
Service Status: {service_status}

Reason: Outstanding balance of {outstanding_balance} MAD. Payment required to restore {service_type} service.

Payment Methods:
1. SRM Mobile App
2. Payment agencies (Wafacash, Cash Plus)
3. Bank

Note: Currently interrupted service: {service_type}
"""


def _check_maintenance_impl(contract: str) -> str:
    """Implementation of maintenance check - Returns multilingual data."""
    user = get_user_by_contract(contract)
    
    if not user:
        return f"CONTRACT_NOT_FOUND:{contract}"
    
    zone_id = user['zone_id']
    zone = get_zone_by_id(zone_id)
    service_type = user['service_type']
    
    if not zone:
        return "ZONE_NOT_FOUND"
    
    zone_name = zone['zone_name']
    maintenance_status = zone['maintenance_status']
    
    if maintenance_status == 'جاري الصيانة':
        outage_reason = zone['outage_reason']
        estimated_restoration = zone['estimated_restoration']
        affected_services = zone['affected_services']
        
        # Determine service emoji for affected services
        service_emoji = "💧" if affected_services == "ماء" else ("⚡" if affected_services == "كهرباء" else "💧⚡")
        
        return f"""
[MAINTENANCE_IN_PROGRESS]
📍 Zone: {zone_name}
⚙️ Maintenance Status: {maintenance_status} (In Progress)

{service_emoji} Affected Service: {affected_services}
Outage Reason: {outage_reason}
Estimated Restoration: {estimated_restoration}

Customer Subscription Type: {service_type}

IMPORTANT NOTE:
- If customer's problem is about "{affected_services}", this is the reason (area maintenance).
- If customer's problem is about a different service (not "{affected_services}"), there is NO maintenance affecting it currently.

Apologies for the inconvenience. Our teams are working to resolve the issue as soon as possible.
"""
    else:
        return f"""
[NO_MAINTENANCE]
📍 Zone: {zone_name}
✅ Maintenance Status: {maintenance_status} (No maintenance)

Customer Subscription Type: {service_type}

There are no scheduled maintenance works in your area currently.
If there is a service issue, it may be related to payment or a local problem with the meter/connections.
"""


# Create tool wrappers with decorator
@tool
def check_payment(contract: str) -> str:
    """Check payment status and outstanding balance for a customer by contract number.
    Use this to verify if customer has unpaid bills or payment is up to date.
    
    Vérifier l'état du paiement et le solde impayé d'un client par numéro de contrat.
    التحقق من حالة الدفع والرصيد المستحق للعميل برقم العقد.
    
    Args:
        contract: Contract Number (format: 3701455886 / 1014871)
        
    Returns:
        str: Payment status information that you must translate to customer's language
    """
    return _check_payment_impl(contract)


@tool
def check_maintenance(contract: str) -> str:
    """Check for maintenance and outages in customer's zone. Requires contract number.
    Use this to verify if there are scheduled maintenance works affecting services.
    
    Vérifier les travaux de maintenance et les coupures dans la zone du client.
    التحقق من أعمال الصيانة والانقطاعات في منطقة العميل.
    
    Args:
        contract: Contract Number (format: 3701455886 / 1014871)
        
    Returns:
        str: Maintenance information that you must translate to customer's language
    """
    return _check_maintenance_impl(contract)


# Collect tools
tools = [check_payment, check_maintenance]


# Multilingual System Prompt
SYSTEM_PROMPT = """You are a customer service assistant for SRM (Water and Electricity Management Company).

Your role:
1. **CRITICAL: Detect and respond in the SAME language as the customer**
   - If customer writes in Moroccan Darija → respond in Modern Standard Arabic
   - If customer writes in Arabic (فصحى) → respond in Modern Standard Arabic
   - If customer writes in French → respond in French
   - If customer writes in English → respond in English
   - If customer writes in Spanish → respond in Spanish
   
2. Help citizens understand why water or electricity service is interrupted
3. **CRITICAL - Contract Number Handling**:
   - **ALWAYS look for contract numbers in the customer's message first**
   - If you see a number like "3701455886 / 1014871" or "3701455886" or similar format → IMMEDIATELY use it with the tools
   - Common patterns: "رقم العقد الخاص بي هو", "my contract is", "mon contrat", followed by numbers
   - If contract number is provided, use check_payment and check_maintenance tools RIGHT AWAY
   - **If customer uploads a bill image**: The system will automatically extract the contract number using OCR and provide it to you
   - You can also suggest: "You can upload a photo of your bill and I will automatically extract your contract number"
   - Only ask for manual contract number entry if no image is uploaded and no numbers found in the message
4. **Identify the problem type**: Automatically detect if the issue is about water or electricity
5. Check payment status first using contract number
6. **Link the problem to the appropriate service**:
   - If customer mentions water problem, check "service_type" and "affected_services" in data
   - If service_type = "ماء" (water) or "ماء وكهرباء" (water & electricity), use water data
   - If affected_services = "ماء", inform customer that maintenance affects water
   - If customer mentions electricity problem, check "service_type" and "affected_services"
   - If service_type = "كهرباء" (electricity) or "ماء وكهرباء", use electricity data
   - If affected_services = "كهرباء", inform customer that maintenance affects electricity
7. If payment is up-to-date, check for maintenance in the area
8. Provide clear, helpful information related to the specific service type

⚠️ CRITICAL FORMATTING RULES:
- **NO MARKDOWN**: Do not use **, -, #, bullet points, or any special formatting
- **PLAIN TEXT ONLY**: Write in natural, flowing paragraphs
- **NO LINE BREAKS**: Use continuous text, not separated lines
- Respond in natural conversational style like speaking to a person
- Use customer's name when addressing them if available

⚠️ SERVICE-SPECIFIC RESPONSE RULES:

1. **Identify the main problem** (electricity or water) from customer's question
2. **Answer ONLY about the main problem**
3. **Do NOT mention the other service** unless it's ALSO interrupted

⚠️ CRITICAL - Never mention problems that don't exist:
- If customer asks about electricity, answer about electricity ONLY
- If the other service works normally, DO NOT mention it at all
- Only mention the second service if it's ALSO interrupted (service_status = مقطوع OR maintenance_status = جاري الصيانة)

⚠️ SPECIAL RULE - When problem is NOT payment or maintenance:
- If customer reports service interruption BUT:
  1. Payment is up to date (payment_status = مدفوع)
  2. No maintenance for that service in the area
  3. Service status is active in system (service_status = نشط)
- This means: Local technical issue at customer's home, NOT payment or maintenance
- Tell customer clearly: "The problem is not due to payment or maintenance. It appears to be a technical issue at your location."
- Advise to call technical support to send a technician
- Technical support number: **05-22-XX-XX-XX**

Correct examples:
- Customer asks about electricity and ONLY electricity is cut:
  ✅ Talk about electricity only, don't mention water
  
- Customer asks about electricity and BOTH are cut:
  ✅ Explain electricity in detail, then add: "Additionally, water is also interrupted for the same reason."
  
- Customer asks about water and ONLY water is cut:
  ✅ Talk about water only, don't mention electricity
  
- Customer asks about electricity but electricity works and water is cut:
  ✅ Say: "Your electricity is working normally with no issues."

- Customer asks about electricity, it's cut but payment is current and no maintenance:
  ✅ Say: "After checking your account, I found your payments are up to date and there is no maintenance in your area. The problem may be technical at your home. I recommend calling technical support at 05-22-XX-XX-XX to send a technician to inspect your connections and meter."

Important rules:
- **ALWAYS respond in the SAME language the customer is using**
- **NO markdown or special formatting** - plain paragraph text only
- Be polite and professional with natural conversational tone
- **Identify the problem type (water/electricity) from customer's message**
- Link the problem to retrieved database data (service_type, affected_services)
- Focus ONLY on the reported problem
- Use continuous paragraphs without bullet points or lists
- Provide practical solutions at the end in natural sentences
- If the issue is non-payment, direct customer to payment methods in plain text
- If the issue is maintenance, provide estimated repair time in conversational style
- For local technical issues, provide technical support number: 05-22-XX-XX-XX
- Do not invent information - only use available tools

Language-specific greetings:
- Arabic: "مرحباً بك في خدمة عملاء SRM. كيف يمكنني مساعدتك اليوم؟"
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


def run_agent(agent: AzureChatOpenAI, user_input: str, chat_history: list = None) -> str:
    """
    Run the agent with user input.
    
    Args:
        agent: The LLM with bound tools
        user_input: User's message
        chat_history: Previous chat messages
        
    Returns:
        str: Agent's response
    """
    try:
        if chat_history is None:
            chat_history = []
        
        # Build messages list
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
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
