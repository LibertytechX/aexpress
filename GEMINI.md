# Development Rules & Standards

### 1. Coding Style (Python)
- **Type Hinting:** Mandatory for all function signatures and class attributes.
- **Docstrings:** Use Google-style docstrings for any public-facing method.
- **Imports:** Use absolute imports for all modules and always put imports at the top of the file.

### 2. API Standards (DRF)
- Use Serializers for validation, not just for output.
- Use the `ServiceException` class for consistent serializer validation error handling, and use the `exception_advice` decorator to handle exceptions and always pass the arg model_object=ErrorLog, and return consistent service responses `service_response`, this is the `service_response` function from `sparky_utils.response`.
```
## Example usage
<!-- ServiceException -->
class CryptoPaymentSerializer(serializers.Serializer):
    amount = serializers.FloatField(required=False)
    pay_currency = serializers.CharField(max_length=10, required=False)

    def validate(self, attrs):
        amount = attrs.get("amount")
        currency = attrs.get("pay_currency")
        if not amount or not currency:
            raise ServiceException(
                status_code=400, message="Amount and currency are required"
            )
        if amount <= 0:
            raise ServiceException(
                status_code=400, message="Amount must be greater than 0"
            )
        if amount < 50 and attrs.get("pay_currency") == "btc":
            raise ServiceException(
                status_code=400, message="Amount must be greater than 50 USD for btc"
            )
        return attrs

<!-- exception_advice and service response -->
@exception_advice(model_object=ErrorLog)
    def post(self, request, *args, **kwargs):
        data = request.data
        chat_id = data.get("chat_id")
        print(chat_id)
        message_id = data.get("message_id")
        db_ref = db.reference(f"/")
        chats_ref = db_ref.child(chat_id)
        message_ref = chats_ref.child(message_id)
        message = message_ref.get()
        print(message)
        # TODO Will process the message with AI and add the AI message
        chats_ref.push(
            {
                "text": "Changed Named",
                "userType": "AI",
                "timestamp": datetime.now().isoformat(),
                "username": "Somename",
            }
        )
        return service_response(
            status="success",
            message="Chat AI",
            data={},
            status_code=200,
        )
```
- Prefer `ModelSerializer` unless the logic is highly custom.
- Use `APIView` or `ViewSet` for API views, but always prefer `APIView`

### 3. Documentation and changelog
- For every new updates (features, bugs, chores) let's update the `CHANGELOG.md` file in the root of the project to keep track of what has been done and when, and also update the `ENDPOINTS_DOCUMENTATION.md` file to reflect the changes in the API endpoints. 


### 4. Testing
- For every new implementations/features let's write a unittest and e2e for the implementation/feature


### 5. Running Commands
- Active venv in the backend directory `/Users/ayo/Liberty/aexpress/backend` using `source venv/bin/activate`


## ClickUp Task Logging
- Log dev work to ClickUp so the PM and QA team can track it.

### Credentials
- Load from ⁠ .claude/clickup.env ⁠ (gitignored). See ⁠ .claude/clickup.env.example ⁠ for the full list of required values.



### When to log
•⁠  ⁠*End of session*: Log everything done in the session automatically.
•⁠  ⁠*On-demand*: If the user says "log now", "log to clickup", or similar, log immediately without waiting for end of session.
•⁠  ⁠*Every task must be assigned to ⁠ CLICKUP_USER_ID ⁠*.

### Status mapping (ClickUp expects lowercase values in the API)
•⁠  ⁠Not started → ⁠ to do ⁠
•⁠  ⁠Currently working on it → ⁠ in progress ⁠
•⁠  ⁠Blocked by something external → ⁠ blocker ⁠
•⁠  ⁠Completed in this session → ⁠ in qa ⁠ (default) or ⁠ awaiting dev deployment ⁠ if the user specifies

Before creating tasks on a list, fetch the list's statuses (⁠ GET /list/{id} ⁠) and use the exact string returned. ClickUp sometimes has trailing whitespace in status names — always read and use the exact value from the API.

# Task Routing Guide

## Task routing (infer from the task subject)

- Merchant web features (dashboard, orders view, analytics, settings, integrations) → **CLICKUP_LIST_MERCHANT_WEB**
- Merchant mobile app features (order management, notifications, profile, in-app actions) → **CLICKUP_LIST_MERCHANT_APP**
- Rider app features (delivery flow, navigation, availability, earnings, notifications) → **CLICKUP_LIST_RIDER_APP**
- Operations dashboard (admin tools, monitoring, reporting, system-wide controls) → **CLICKUP_LIST_OPERATION_DASHBOARD**
- Dispatcher tools (order assignment, routing, live tracking, dispatch controls) → **CLICKUP_LIST_DISPATCHER**

---

## Cross-layer rule

If a task spans backend and frontend, create **one task per layer**:

- **Backend:** focus on APIs, business logic, data handling  
- **Frontend:** focus on UI, UX, state management  

Always **cross-reference both tasks** in their descriptions.

---

## Examples

- **Backend: Optimize dispatch auto-assignment logic**  
  Improved how orders are assigned to riders based on proximity and load.

- **Frontend: Improve dispatcher live map performance**  
  Reduced lag and improved real-time updates for order and rider movement.

- **Backend: Persist merchant notification settings**  
  Merchant preferences now save and reload correctly across sessions.

- **Frontend: Add order filtering on merchant dashboard**  
  Merchants can now filter orders by status, date, and delivery progress.

### Task format
•⁠  ⁠*Title*: Imperative, concise. Prefix with ⁠ Backend: ⁠ or ⁠ Frontend: ⁠ when useful.
•⁠  ⁠*Description*: 1-3 sentences in plain language — what changed and why. No code snippets, function names, or endpoint paths. The PM and QA read these.
•⁠  ⁠*Assignee*: Always ⁠ CLICKUP_USER_ID ⁠.
•⁠  ⁠*Priority*: Default unless the user specifies.
