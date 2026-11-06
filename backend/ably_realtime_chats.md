# Ably Realtime Chats Integration Guide

This document explains how to integrate the AXpress Chat System with Ably for real-time message updates.

## 1. Authentication

To connect to Ably, you must first obtain a temporary token from the AXpress backend. Use the following endpoint:

**Endpoint:** `GET /api/dispatch/ably-token/`  
**Authentication:** Required (Bearer Token)  
**Description:** Returns an Ably token and a full `token_request` object.

### Example Response:
```json
{
  "token": "...",
  "token_request": {
    "keyName": "...",
    "ttl": 86400000,
    "capability": "{\"chat:*\": [\"publish\", \"subscribe\"], ...}",
    "clientId": "...",
    "timestamp": 1712484738,
    "nonce": "...",
    "mac": "..."
  }
}
```

## 2. Connecting to Ably

Using the Ably JavaScript SDK, you can initialize the client using the `token` or `authCallback`.

```javascript
import * as Ably from 'ably';

const ably = new Ably.Realtime({
  token: 'TOKEN_FROM_BACKEND',
});
```

## 3. Channel Naming Convention

Each conversation has a unique Ably channel. The naming convention is:

`chat:{type}:{user_id}`

- **`type`**: Either `customers` or `riders`.
- **`user_id`**: The UUID or ID of the user (customer/rider) who owns the conversation.

> [!TIP]
> You can find the `type` and `user_id` by calling the `GET /api/chats/conversations/` endpoint.

## 4. Subscribing to Messages

Once connected to the channel, subscribe to the `new_message` event.

### Example:
```javascript
const channelName = `chat:customers:550e8400-e29b-41d4-a716-446655440000`;
const channel = ably.channels.get(channelName);

channel.subscribe('new_message', (message) => {
  console.log('Received message:', message.data);
  /*
    Payload Structure:
    {
      "id": "message_uuid",
      "conversation_id": "conversation_uuid",
      "sender_type": "agent", // or "customer", "rider"
      "content": "Hello, how can I help you?",
      "timestamp": "2024-04-07T10:42:18Z"
    }
  */
});
```

## 5. Publishing Messages

While you should always send messages through the REST API (`POST /api/chats/conversations/<pk>/messages/send/`), the backend will automatically publish the message to Ably for you. 

However, your client-side capability allows you to publish if needed (e.g., for "typing..." indicators).

```javascript
// Example (Typing Indicator):
channel.publish('typing', { user: 'John Doe', typing: true });
```

---

## 5. Flutter Implementation

If you are building the AXpress mobile app with Flutter, follow these steps:

### 1. Add Dependency
Add `ably_flutter` to your `pubspec.yaml`:
```yaml
dependencies:
  ably_flutter: ^1.2.14 # or latest
```

### 2. Initialization
Initialize the Ably Realtime client using the token obtained from the AXpress backend.

```dart
import 'package:ably_flutter/ably_flutter.dart' as ably;

final clientOptions = ably.ClientOptions(
  token: 'TOKEN_FROM_BACKEND',
);
final realtime = ably.Realtime(options: clientOptions);
```

### 3. Subscribing to Messages
Listen for new messages on the conversation channel.

```dart
final channelName = 'chat:customers:USER_UUID';
final channel = realtime.channels.get(channelName);

// Subscribe to the 'new_message' event
final subscription = channel.subscribe(name: 'new_message').listen((ably.Message message) {
  final data = message.data as Map<dynamic, dynamic>;
  print('New message received: ${data['content']}');
  
  // Update your local state/UI here
});

// Don't forget to cancel the subscription when the widget is disposed
// subscription.cancel();
```

---

## 6. Summary of Events

| Event Name | Direction | Description |
| :--- | :--- | :--- |
| `new_message` | Server -> Client | Triggered when a new message is saved to the DB. |
| `typing` (optional) | Client <-> Client | Can be used for real-time typing indicators. |

---

> [!IMPORTANT]
> Always ensure you have a valid Bearer token before requesting an Ably token. Ably tokens granted by the AXpress backend are valid for **24 hours**.
