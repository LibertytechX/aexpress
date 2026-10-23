# Independent Rider Face Match Verification API

This integration guide explains how to integrate the asynchronous Face Match verification endpoint and real-time Ably status updates into the mobile application (e.g., Flutter / React Native).

---

## 1. Flow Overview

```
[Rider App]               [AXpress Backend]               [Ably Realtime]
     |                            |                              |
     | 1. Upload selfie to S3     |                              |
     |--------------------------->|                              |
     |                            |                              |
     | 2. POST /api/riders/facematch/                            |
     |    { "image_url": "..." }  |                              |
     |--------------------------->|                              |
     |                            |                              |
     | 3. Returns 202 Accepted    |                              |
     |    { "channel": "...", ...}|                              |
     |<---------------------------|                              |
     |                                                           |
     | 4. Subscribe to Ably channel `facematch:<rider_id>`       |
     |---------------------------------------------------------->|
     |                                                           |
     |                    5. Backend verifies face via Celery    |
     |                       & publishes result to Ably          |
     |                            |----------------------------->|
     |                                                           |
     | 6. Receives event `facematch_result`                      |
     |<----------------------------------------------------------|
     |
     * If matched: Show success screen & continue
     * If failed:  Show error alert & automatically logout rider
```

---

## 2. API Endpoint Specification

### **Initiate Face Match Verification**
- **Method:** `POST`
- **URL:** `/api/riders/facematch/` *(alias: `/api/riders/face-match/`)*
- **Authentication:** Required (`Bearer <access_token>`)
- **Headers:** 
  ```http
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```

### **Request Body**
```json
{
  "image_url": "https://assuredexpress.s3.us-east-1.amazonaws.com/uploads/selfie_snapshot.jpg"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `image_url` | `string` (URL) | **Yes** | S3 bucket URL of the selfie snapshot image captured by the rider. |

---

### **Success Response (`202 Accepted`)**
Returned immediately while verification processes in the background:

```json
{
  "status": "success",
  "status_code": 202,
  "message": "Face match verification initiated.",
  "data": {
    "channel": "facematch:RD1234",
    "event": "facematch_result",
    "status": "processing"
  }
}
```

| Field | Description |
|---|---|
| `data.channel` | The exact Ably channel to subscribe to (e.g. `facematch:RD1234`). |
| `data.event` | The Ably event name to listen for (`facematch_result`). |
| `data.status` | State of the request (`processing`). |

---

### **Error Responses**

#### `400 Bad Request` — Non-independent rider
```json
{
  "status": "error",
  "status_code": 400,
  "message": "Face match verification is only applicable to independent riders.",
  "data": null
}
```

#### `400 Bad Request` — Missing reference profile photo
```json
{
  "status": "error",
  "status_code": 400,
  "message": "No reference profile photo found in rider documents. Please upload a profile photo first.",
  "data": null
}
```

#### `401 Unauthorized` — Missing or expired token
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## 3. Real-Time Ably Event Handling

### Step A: Connect to Ably
1. Obtain an Ably token from `GET /api/dispatch/ably-token/` using the rider's Bearer token.
2. Initialize the Ably client with the returned token.
3. Subscribe to the channel returned in the 202 response: `facematch:<rider_id>`.
4. Listen for the event: `facematch_result`.

---

### Step B: Handle Event Payloads

#### 1. Match Succeeded (`matched: true`)
The selfie matches the rider's KYC profile photo. The rider remains authorized and online.
```json
{
  "status": "success",
  "matched": true,
  "similarity": 98.4,
  "message": "Face match verification successful."
}
```
> **App Action:** Dismiss loading indicator and display success message/check mark. Rider continues regular app usage.

---

#### 2. Match Failed (`matched: false` with `"action": "logout"`)
The selfie **did not match** or validation failed. The backend has **blocked and deauthorized the rider's account** (`is_authorized = false`, `status = "offline"`), and invalidated active sessions.
```json
{
  "status": "failed",
  "matched": false,
  "similarity": 24.1,
  "action": "logout",
  "message": "Face match verification failed. Your account has been unauthorized."
}
```
> **App Action:** 
> 1. Stop background listeners.
> 2. Show a dialog informing the rider that face verification failed and their account has been unauthorized.
> 3. Clear local tokens and **force logout** the rider to the login screen.

---

#### 3. Error (`status: "error"`)
An unexpected network or image download issue occurred.
```json
{
  "status": "error",
  "matched": false,
  "message": "Failed to download face images: Connection timeout"
}
```
> **App Action:** Inform the rider to check their internet connection and retry.

---

## 4. Mobile Integration Code Example (Flutter / Dart)

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:ably_flutter/ably_flutter.dart' as ably;

Future<void> performFaceMatchVerification({
  required String s3ImageUrl,
  required String authToken,
}) async {
  final url = Uri.parse('https://api.assuredexpress.com/api/riders/facematch/');

  // 1. Send verification request
  final response = await http.post(
    url,
    headers: {
      'Authorization': 'Bearer $authToken',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({'image_url': s3ImageUrl}),
  );

  if (response.statusCode != 202) {
    final error = jsonDecode(response.body);
    throw Exception(error['message'] ?? 'Failed to initiate face match.');
  }

  final responseData = jsonDecode(response.body)['data'];
  final channelName = responseData['channel'];
  final eventName = responseData['event']; // 'facematch_result'

  // 2. Fetch Ably auth token
  final ablyTokenResponse = await http.get(
    Uri.parse('https://api.assuredexpress.com/api/dispatch/ably-token/'),
    headers: {'Authorization': 'Bearer $authToken'},
  );
  final token = jsonDecode(ablyTokenResponse.body)['token'];

  // 3. Connect to Ably & Subscribe to Channel
  final clientOptions = ably.ClientOptions(token: token);
  final realtime = ably.Realtime(options: clientOptions);
  final channel = realtime.channels.get(channelName);

  channel.subscribe(name: eventName).listen((ably.Message message) {
    final payload = message.data is String 
        ? jsonDecode(message.data as String) 
        : Map<String, dynamic>.from(message.data as Map);

    final bool matched = payload['matched'] == true;
    final String? action = payload['action'];
    final String statusMsg = payload['message'] ?? '';

    if (matched) {
      // SUCCESS: Dismiss loading & continue
      print("Face match successful: $statusMsg");
      channel.detach();
      realtime.close();
    } else if (action == 'logout') {
      // FAILURE: Account blocked -> force logout immediately
      print("Face match failed: $statusMsg");
      channel.detach();
      realtime.close();
      _handleForcedLogout(statusMsg);
    } else {
      // Error handling (e.g. retry)
      print("Face match error: $statusMsg");
    }
  });
}

void _handleForcedLogout(String reason) {
  // Clear local secure storage/preferences and route to Login Screen
}
```
