import asyncio
import json
import logging
from celery import shared_task
from .models import Conversation, Message
from .ai_engine import get_ai_response

logger = logging.getLogger(__name__)


@shared_task
def process_ai_response(conversation_id, user_id, user_message_content):
    """
    Celery task to handle AI agent reasoning and response.
    """
    try:
        # 1. Run the AI Agent asynchronously
        ai_response_raw = asyncio.run(
            get_ai_response(conversation_id, user_id, user_message_content)
        )

        # 2. Parse structured output (if it's JSON)
        try:
            ai_data = json.loads(ai_response_raw)
            ai_text = ai_data.get("response", ai_response_raw)
            # You could also use ai_data.get("category") or ai_data.get("action_required") here
        except json.JSONDecodeError:
            ai_text = ai_response_raw

        # 3. Save the AI response to the database
        conversation = Conversation.objects.get(id=conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender_type="agent",
            content=ai_text,
        )

        # 4. Update denormalized fields on Conversation
        Conversation.objects.filter(id=conversation_id).update(last_message=ai_text)
        conversation.save(update_fields=["updated_at"])

        # 5. Publish real-time event via Ably
        # We import here to avoid circular dependencies
        from .views import _publish_to_ably

        payload = {
            "id": str(message.id),
            "conversation_id": str(conversation.id),
            "sender_type": "agent",
            "content": ai_text,
            "timestamp": message.timestamp.isoformat(),
        }
        _publish_to_ably(conversation.ably_channel_name, "new_message", payload)

    except Exception as e:
        logger.error(f"Error in process_ai_response task: {e}")
