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
    """Implementation of payment check."""
    user = get_user_by_cil(cil)
    
    if not user:
        return f"لم يتم العثور على عميل برقم CIL: {cil}. الرجاء التحقق من الرقم."
    
    name = user['name']
    payment_status = user['payment_status']
    outstanding_balance = user['outstanding_balance']
    last_payment = user['last_payment_date']
    service_status = user['service_status']
    service_type = user['service_type']
    
    if payment_status == 'مدفوع':
        return f"""
معلومات العميل {name}:
- نوع الخدمة: {service_type}
- حالة الدفع: ✅ {payment_status}
- آخر دفعة: {last_payment}
- الرصيد المستحق: {outstanding_balance} درهم
- حالة الخدمة: {service_status}

الدفعات محدثة. إذا كانت الخدمة مقطوعة، قد يكون السبب صيانة في المنطقة.
"""
    else:
        return f"""
معلومات العميل {name}:
- نوع الخدمة: {service_type}
- حالة الدفع: ⚠️ {payment_status}
- آخر دفعة: {last_payment}
- الرصيد المستحق: {outstanding_balance} درهم
- حالة الخدمة: {service_status}

يوجد رصيد مستحق بقيمة {outstanding_balance} درهم. الرجاء سداد المبلغ لاستعادة الخدمة.
يمكنك الدفع عبر:
1. التطبيق المحمول لـ SRM
2. وكالات الأداء (وفا كاش، كاش بلس)
3. البنك
"""


def _check_maintenance_impl(cil: str) -> str:
    """Implementation of maintenance check."""
    user = get_user_by_cil(cil)
    
    if not user:
        return f"لم يتم العثور على عميل برقم CIL: {cil}"
    
    zone_id = user['zone_id']
    zone = get_zone_by_id(zone_id)
    
    if not zone:
        return "لا توجد معلومات عن المنطقة."
    
    zone_name = zone['zone_name']
    maintenance_status = zone['maintenance_status']
    
    if maintenance_status == 'جاري الصيانة':
        outage_reason = zone['outage_reason']
        estimated_restoration = zone['estimated_restoration']
        affected_services = zone['affected_services']
        
        return f"""
📍 منطقتك: {zone_name}
⚙️ حالة الصيانة: {maintenance_status}

سبب الانقطاع: {outage_reason}
الخدمات المتأثرة: {affected_services}
الوقت المتوقع للإصلاح: {estimated_restoration}

نعتذر عن الإزعاج. فرقنا تعمل على حل المشكلة في أقرب وقت ممكن.
"""
    else:
        return f"""
📍 منطقتك: {zone_name}
✅ حالة الصيانة: {maintenance_status}

لا توجد أعمال صيانة مجدولة في منطقتك حالياً.
"""


# Create tool wrappers with decorator
@tool
def check_payment(cil: str) -> str:
    """يستخدم للتحقق من حالة الدفع والرصيد المستحق للعميل. يتطلب رقم CIL (8 أرقام).
    
    Check payment status and outstanding balance for a customer by CIL number.
    
    Args:
        cil: Customer Identification Number (8 digits)
        
    Returns:
        str: Payment status information in Arabic
    """
    return _check_payment_impl(cil)


@tool
def check_maintenance(cil: str) -> str:
    """يستخدم للتحقق من أعمال الصيانة والانقطاعات في منطقة العميل. يتطلب رقم CIL.
    
    Check for maintenance and outages in customer's zone. Requires CIL number.
    
    Args:
        cil: Customer Identification Number (8 digits)
        
    Returns:
        str: Maintenance information in Arabic
    """
    return _check_maintenance_impl(cil)


# Collect tools
tools = [check_payment, check_maintenance]


# Arabic System Prompt
SYSTEM_PROMPT = """أنت مساعد خدمة العملاء لشركة SRM (إدارة المياه والكهرباء).

دورك:
1. التحدث باللغة العربية الفصحى بشكل احترافي ومهذب
2. مساعدة المواطنين في فهم سبب انقطاع الماء أو الكهرباء
3. طلب رقم CIL (رقم العميل المكون من 8 أرقام) إذا لم يتم تقديمه
4. التحقق من حالة الدفع أولاً
5. إذا كان الدفع منتظم، التحقق من الصيانة في المنطقة
6. تقديم معلومات واضحة ومفيدة

قواعد مهمة:
- استخدم اللغة العربية فقط في جميع الردود
- كن مهذباً ومحترماً
- قدم حلول عملية
- إذا كان السبب عدم الدفع، وجه العميل لطرق الدفع
- إذا كان السبب الصيانة، قدم الوقت المتوقع للإصلاح
- لا تخترع معلومات - استخدم الأدوات المتاحة فقط

ابدأ بالترحيب بالعميل وسؤاله عن مشكلته."""


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
