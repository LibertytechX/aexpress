## Add order completed and paid filter to the order list - dispatcher 
## Add order completed and unpaid filter to the order list - dispatcher
- [x] Add Idempotency or rate limiting in order creation if within the same 1 min frame and same user
- [x] add a flag for rider assignment by either the dispatcher or by the rider
- [] add an order source i.e where an order is being created from either from the merchant web or the dispatcher web
- [x] rider accepts/reject assignment if a dispatcher assigned the rider and order
- [x] order export all
- [x] complete the merchant referral implementation with agency banking
- [x] move all marketing tasks to tasks.py and update their references in the codebase
- [x] add check for rider acceptance of order offer to make sure the order within their zone.
- [x] Bonus: integrate AI chatbot to the merchant support chats
- [] Bonus: Build an MCP tools for Axpress Order booking and basic enquires
- [x] Move all map services to a separate secure service and use it across the platform 
- [x] update the onboard dispatcher in teams to support role assignment.
- [x] implement merchant delete endpoint
- [] merchant notifications, notification_settings toggle
- [x] Adjust app server logging for faster error tracing and debugging and troubleshooting on axpress.
- [] (Bonus). Integrate AI Chats using Gemini AI model to axpress customer chats features 
- [x] update all relay sub orders payment status to paid when the main order is paid for.
- [] Smartparcel integration
- [x] update weekly report template to show order volume and amount for the week.
- [x] Rider metrics for rider's daily orders, weekly and monthly and distance covered all time and overall orders completed.
- [] Rider to own for riders, weekly and daily update
- [x] implement simulate drop and collect smartpercel
- [x] Add distinguishing feature for jumia riders
- [x] Document refresh token endpoint
- [x] Add weekly and daily filter for rider earnings
## Data - 2026-04-20
- [x] change collectcode to boxlockernumber for smartpercel pending pickups
- [] Document Merchant API endpoints
- [x] Refactor quick send api endpoint to reduce complexity
- [X] Fix hpmr send sms bug
- [X] Fix hpmr log customer contact bug
- [] profile slow endpoints and SLOs for all endpoints
- [x] fix slow rider start order endpoint in orders/views.py
- [x] add soft delete for riders and merchants
- [xx] add bike reassignment history for riders
- [] also restrict permission to reassign vehicle assets to riders on dispatcher panel and also add admin who initiated the request
- [x] add support is jumia order creation

routing functions to update for backend to use osrm
- calculate_route
- find_closest_zone


routing functions for the frontend

