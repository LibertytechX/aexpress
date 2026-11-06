"""
WhatsApp message templates for each event type.
Each function receives relevant context and returns the message text.
"""


def signup_message(contact_name, business_name):
    return (
        f"Welcome to AXpress, {contact_name}! 🎉\n\n"
        f"Your account for *{business_name}* has been created successfully.\n"
        f"Please verify your email to get started.\n\n"
        f"Need help? Reply to this message."
    )


def onboarding_message(contact_name):
    return (
        f"Hey {contact_name}! ✅\n\n"
        f"Your AXpress account is now fully verified and ready to go!\n"
        f"You can start sending deliveries right away.\n\n"
        f"Log in at send.axpress.net to get started."
    )


def order_created_message(order_number, pickup_address, total_amount, delivery_count=1):
    return (
        f"📦 *Order #{order_number} Created*\n\n"
        f"Pickup: {pickup_address}\n"
        f"Deliveries: {delivery_count}\n"
        f"Total: ₦{total_amount:,.2f}\n\n"
        f"We're finding a rider for you now."
    )


def rider_assigned_message(order_number, rider_name, rider_phone):
    return (
        f"🏍️ *Rider Assigned — Order #{order_number}*\n\n"
        f"Rider: {rider_name}\n"
        f"Phone: {rider_phone}\n\n"
        f"Your rider is heading to the pickup location."
    )


def rider_assigned_to_rider_message(order_number, pickup_address):
    return (
        f"📦 *New Order Assigned — #{order_number}*\n\n"
        f"Head to pickup: {pickup_address}\n\n"
        f"Open your app for full details."
    )


def order_picked_up_message(order_number):
    return (
        f"🚀 *Order #{order_number} Picked Up*\n\n"
        f"Your delivery is on the move! "
        f"You'll be notified when the rider arrives."
    )


def order_delivered_message(order_number):
    return (
        f"✅ *Order #{order_number} Delivered!*\n\n"
        f"Your delivery has been completed successfully.\n"
        f"Thank you for using AXpress!"
    )


def order_cancelled_message(order_number, cancelled_by):
    return (
        f"❌ *Order #{order_number} Cancelled*\n\n"
        f"Cancelled by: {cancelled_by}\n"
        f"If funds were held in escrow, a refund will be processed."
    )


def relay_leg_assigned_message(parent_order_number, leg_number, pickup_address):
    return (
        f"🔁 *Relay Leg Assigned*\n\n"
        f"Order: #{parent_order_number}\n"
        f"Leg: {leg_number}\n"
        f"Pickup: {pickup_address}\n\n"
        f"Please ensure you're ready for pickup."
    )


def dispatcher_onboarded_message(contact_name, phone, password):
    return (
        f"Welcome to AXpress, {contact_name}! 🎉\n\n"
        f"Your dispatcher account is ready.\n"
        f"Phone: {phone}\n"
        f"Password: {password}\n\n"
        f"Log in at dispatcherx.axpress.net"
    )


def referral_commission_message(rider_name, amount, order_number):
    return (
        f"💰 *Referral Commission Earned!*\n\n"
        f"Hey {rider_name}, you earned ₦{amount:,.2f} "
        f"from order #{order_number}.\n\n"
        f"Keep referring merchants to earn more!"
    )


def drip_campaign_message(contact_name, campaign_tag, body_text):
    return (
        f"Hi {contact_name},\n\n"
        f"{body_text}"
    )


def weekly_report_message(contact_name, total_orders, total_spent):
    return (
        f"📊 *Your Weekly AXpress Summary*\n\n"
        f"Hey {contact_name},\n"
        f"Orders this week: {total_orders}\n"
        f"Total spent: ₦{total_spent:,.2f}\n\n"
        f"Keep the momentum going! 🚀"
    )


def rider_order_offer_message(order_number, pickup_address, estimated_earnings):
    return (
        f"🏍️ *New Order Available — #{order_number}*\n\n"
        f"Pickup: {pickup_address}\n"
        f"Estimated earnings: ₦{estimated_earnings:,.2f}\n\n"
        f"Open the app to accept."
    )
