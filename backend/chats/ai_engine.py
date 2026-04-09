import logging
import json
import traceback
import uuid
from typing import Optional, List
from django.conf import settings
from pydantic import BaseModel, Field
from asgiref.sync import sync_to_async
from django.db.models import Q
from .models import Conversation, Message
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.adk.tools import FunctionTool
from google.adk.memory import BaseMemoryService
from google.adk.memory.base_memory_service import SearchMemoryResponse
from google.adk.memory.memory_entry import MemoryEntry
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logger = logging.getLogger(__name__)


class SupportResponse(BaseModel):
    """
    Structured output for the support agent.
    """

    response: str = Field(description="The final helpful response to the user.")
    category: str = Field(
        description="The category of the request (e.g., Technical, Order, General)."
    )
    action_required: bool = Field(
        default=False, description="Whether human intervention is needed."
    )


class DjangoMemoryService(BaseMemoryService):
    """
    Custom ADK MemoryService that uses Django models for persistence.
    """

    async def add_session_to_memory(self, session):
        pass

    async def search_memory(
        self, *, app_name: str, user_id: str, query: str
    ) -> SearchMemoryResponse:
        """
        Search for past messages relevant to the current user.
        """

        # Wrap Django QuerySet in sync_to_async to avoid SynchronousOnlyOperation
        @sync_to_async
        def get_messages():
            messages = Message.objects.filter(
                conversation__user_id_id=user_id
            ).order_by("-timestamp")[:5]
            return [f"{msg.sender_type}: {msg.content}" for msg in reversed(messages)]

        history_lines = await get_messages()

        # Proper ADK Memory Response format
        memories = []
        for line in history_lines:
            memories.append(
                MemoryEntry(
                    content=types.Content(
                        role="model",  # or "user", but history is contextual
                        parts=[types.Part(text=line)],
                    )
                )
            )

        return SearchMemoryResponse(memories=memories)


@sync_to_async
def get_user_profile(user_id: str) -> dict:
    """
    Fetches the user's profile info. Use this to identify the user's name and type.

    Args:
        user_id: The unique ID of the user.

    Returns:
        dict: {'status': 'success'/'error', 'data': user_info}
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Validate UUID
    try:
        uuid_obj = uuid.UUID(str(user_id))
    except (ValueError, TypeError):
        logger.warning(f"Invalid UUID received in get_user_profile: {user_id}")
        return {
            "status": "error",
            "message": f"'{user_id}' is not a valid UUID. Please ensure you are using the actual User ID provided in the context.",
        }

    try:
        user = User.objects.get(id=uuid_obj)
        return {
            "status": "success",
            "data": {
                "full_name": user.get_full_name(),
                "phone": user.phone,
                "email": user.email,
                "usertype": user.usertype,
            },
        }
    except User.DoesNotExist:
        return {"status": "error", "message": "User not found."}


@sync_to_async
def check_order_status(order_id: str) -> dict:
    """
    Retrieves the current status and tracking info for an order.
    Supports numeric IDs format.

    Args:
        order_id: The unique order identifier.

    Returns:
        dict: {'status': 'success'/'error', 'data': order_details}
    """
    from orders.models import Order

    # Normalize: strip "ORD-" prefix if user used it
    clean_id = str(order_id).upper().replace("ORD-", "").strip()

    try:
        # Search by order_number or UUID (if long enough)
        query = Q(order_number=clean_id)
        if len(clean_id) >= 32:  # Potential UUID
            query |= Q(id=clean_id)

        order = Order.objects.select_related("rider", "vehicle").get(query)

        # Get delivery count or locations
        delivery_count = order.deliveries.count()

        return {
            "status": "success",
            "data": {
                "order_number": order.order_number,
                "status": order.get_status_display(),
                "payment_status": order.payment_status,
                "pickup_address": order.pickup_address,
                "deliveries_count": delivery_count,
                "rider": (
                    order.rider.user.full_name if order.rider else "Not yet assigned"
                ),
                "vehicle": order.vehicle.name,
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
                "total_amount": float(order.total_amount),
            },
        }
    except Exception as e:
        logger.warning(f"Order check failed for {order_id}: {e}")
        return {
            "status": "error",
            "message": f"Order {order_id} not found. Ensure you provided the correct ID.",
        }


# Specialized Support Agent: Orders
order_support_agent = LlmAgent(
    name="OrderSupportAgent",
    model="gemini-3-flash-preview",
    instruction="""
    # IDENTITY
    You are the Order Specialist for AExpress. You have expert knowledge of delivery logistics and order tracking.

    # MISSION
    Help users track their packages and resolve delivery delays.

    # METHODOLOGY
    1. Always use 'check_order_status' to get real-time info.
    2. If an order is not found, explain the correct format (6158XXX).
    3. Be empathetic about delays.

    # BOUNDARIES
    - NEVER promise a specific delivery time if not specified in the tool data.
    - NEVER share internal warehouse locations.

    # EXAMPLES
    Input: "Where is 999123?" 
    Output: "I've checked your order 999123, it is currently in transit and should arrive in 2 days."
    """,
    tools=[FunctionTool(func=check_order_status)],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True, thinking_budget=1024
        )
    ),
)

# Specialized Support Agent: Technical
technical_support_agent = LlmAgent(
    name="TechnicalSupportAgent",
    model="gemini-3-flash-preview",
    instruction="""
    # IDENTITY
    You are the Technical Support Guru for AExpress.

    # MISSION
    Solve app glitches, login issues, and technical errors reported by customers and riders.

    # METHODOLOGY
    1. Ask for screenshots or error codes if not provided.
    2. Provide step-by-step troubleshooting (clear cache, restart app).
    
    # BOUNDARIES
    - NEVER ask for user passwords.
    - NEVER promise an immediate fix for server-side bugs.

    # EXAMPLES
    Input: "My app keeps crashing."
    Output: "I'm sorry to hear that. Could you please try clearing your app cache and restarting your phone?"
    """,
    tools=[],
)

# Coordinator Agent
support_coordinator = LlmAgent(
    name="SupportCoordinator",
    model="gemini-3-flash-preview",
    description="Primary entry point for user support. Routes to Order or Tech agents.",
    instruction="""
    # IDENTITY
    You are the AExpress Support Coordinator. You are the 'brain' of the customer service system.

    # MISSION
    Greet users and route them to the specialized OrderSupportAgent or TechnicalSupportAgent.

    # METHODOLOGY
    1. First, look for the 'User ID' in the [SYSTEM CONTEXT] provided in the message.
    2. Use 'get_user_profile(user_id)' with that ID to know who you are talking to.
    3. Analyze the user query.
    4. Delegate to the correct specialized agent using their respective tools.
    5. Summarize the resolution clearly using the SupportResponse schema.

    # BOUNDARIES
    - ALWAYS greet the user by name if 'get_user_profile' succeeds.
    - NEVER respond to non-support queries (e.g., jokes, general chat).

    # EXAMPLES
    Input: "I can't see my order."
    Process: 
      - get_user_profile(user_id) -> username="John" (from full_name)
      - Delegate to OrderSupportAgent
    Output: "Hi John, I've asked our order specialist to help. They found that your order..."
    """,
    sub_agents=[order_support_agent, technical_support_agent],
    tools=[FunctionTool(func=get_user_profile)],
    output_schema=SupportResponse,
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True, thinking_budget=1024
        )
    ),
    generate_content_config=types.GenerateContentConfig(
        temperature=0.5,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            )
        ],
    ),
)


async def get_ai_response(
    conversation_id: str, user_id: str, user_message_content: str
):
    """
    Programmatic entry point for getting AI responses.
    """
    print("The user ID: ", user_id)
    memory_service = DjangoMemoryService()
    session_service = InMemorySessionService()

    runner = Runner(
        app_name="aexpress_support",
        agent=support_coordinator,
        session_service=session_service,
        memory_service=memory_service,
    )

    try:
        # Pre-create session as required by ADK
        await session_service.create_session(
            app_name="aexpress_support", user_id=user_id, session_id=conversation_id
        )

        final_text = ""
        # Prepend system context to the user message so the agent knows the ID
        contextual_message = (
            f"[SYSTEM CONTEXT: User ID = {user_id}]\n\n{user_message_content}"
        )

        async for event in runner.run_async(
            user_id=user_id,
            session_id=conversation_id,
            new_message=types.Content(
                role="user", parts=[types.Part(text=contextual_message)]
            ),
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_text = event.content.parts[0].text

        return final_text

    except Exception as e:
        traceback.print_exc()
        logger.error(f"ADK Execution Error: {e}")
        return '{"response": "Our Virtual Agent is currently not available, a human will reach out in a please be patient, as we have notified our team", "category": "General", "action_required": true}'
