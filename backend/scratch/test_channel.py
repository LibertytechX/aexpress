import os, django, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from chats.models import Conversation
from authentication.models import User
from chats.serializers import ConversationListSerializer

u = User.objects.create(phone="1234567890")
c = Conversation.objects.create(user_id=u, type="customers")
try:
    print("ably_channel_name: ", c.ably_channel_name)
    data = ConversationListSerializer(c).data
    print("serializer output participant.id:", data['participant']['id'])
    print("frontend expected channel:", f"chat:{data['type']}:{data['participant']['id']}")
finally:
    c.delete()
    u.delete()
