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
from data.mock_db import get_user_by_cil, get_zone_by_id


# Tool Functions (without decorator for direct calling)
def _check_payment_impl(cil: str) -> str:
    """Implementation of payment check - Returns multilingual data."""
    user = get_user_by_cil(cil)
    
    if not user:
        return f"""
[CUSTOMER_NOT_FOUND]
CIL: {cil}
Message: Customer not found with this CIL number. Please verify the number.
"""
    
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


def _check_maintenance_impl(cil: str) -> str:
    """Implementation of maintenance check - Returns multilingual data."""
    user = get_user_by_cil(cil)
    
    if not user:
        return f"[ERROR] Customer not found with CIL: {cil}"
    
    zone_id = user['zone_id']
    zone = get_zone_by_id(zone_id)
    service_type = user['service_type']
    
    if not zone:
        return "[ERROR] No zone information available."
    
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
def check_payment(cil: str) -> str:
    """Check payment status and outstanding balance for a customer by CIL number.
    Use this to verify if customer has unpaid bills or payment is up to date.
    
    Vérifier l'état du paiement et le solde impayé d'un client par numéro CIL.
    التحقق من حالة الدفع والرصيد المستحق للعميل برقم CIL.
    
    Args:
        cil: Customer Identification Number (format: 1071324-101)
        
    Returns:
        str: Payment status information that you must translate to customer's language
    """
    return _check_payment_impl(cil)


@tool
def check_maintenance(cil: str) -> str:
    """Check for maintenance and outages in customer's zone. Requires CIL number.
    Use this to verify if there are scheduled maintenance works affecting services.
    
    Vérifier les travaux de maintenance et les coupures dans la zone du client.
    التحقق من أعمال الصيانة والانقطاعات في منطقة العميل.
    
    Args:
        cil: Customer Identification Number (format: 1071324-101)
        
    Returns:
        str: Maintenance information that you must translate to customer's language
    """
    return _check_maintenance_impl(cil)


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
3. Request CIL number (Customer ID format: 1071324-101) if not provided
4. **Identify the problem type**: Automatically detect if the issue is about water or electricity
5. Check payment status first using CIL number
6. **Link the problem to the appropriate service**:
   - If customer mentions water problem, check "service_type" and "affected_services" in data
   - If service_type = "ماء" (water) or "ماء وكهرباء" (water & electricity), use water data
   - If affected_services = "ماء", inform customer that maintenance affects water
   - If customer mentions electricity problem, check "service_type" and "affected_services"
   - If service_type = "كهرباء" (electricity) or "ماء وكهرباء", use electricity data
   - If affected_services = "كهرباء", inform customer that maintenance affects electricity
7. If payment is up-to-date, check for maintenance in the area
8. Provide clear, helpful information related to the specific service type

Important rules:
- **ALWAYS respond in the SAME language the customer is using**
- Be polite and professional
- **Identify the problem type (water/electricity) from customer's message**
- Link the problem to retrieved database data (service_type, affected_services)
- Provide practical solutions related to the specific service type
- If the issue is non-payment, direct customer to payment methods
- If the issue is maintenance, provide estimated repair time and confirm affected service type
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
