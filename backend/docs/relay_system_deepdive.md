# AXpress Relay System Documentation

The AXpress Relay System is a specialized "hub-and-hold" delivery architecture designed for long-distance transport. It fragments a single order into multiple sequential "legs," each handled by a different rider and connected via physical handoff points called **Relay Nodes**.

---

## 🏗️ Architecture Overview

The system operates on a **hub-and-hold** model:
1.  **Pickup**: Rider A picks up the package from the sender.
2.  **Handoff**: Rider A drops the package at a designated **Relay Node** (Hub).
3.  **Hold**: The package remains at the hub until the next rider is available.
4.  **Chain**: This process repeats until the final rider delivers the package to the receiver.

### Key Concepts
-   **Multi-Hop**: Orders can be split into up to 12 legs.
-   **Leg Sequentiality**: Leg $N+1$ cannot start until Leg $N$ is marked as `AtHub`.
-   **Zoning**: Relay Nodes are assigned to geographical `Zones` within organizational `Verticals`.

---

## 📊 Data Models

### 1. `RelayNode` (dispatcher/models.py)
Represents a physical hub.
-   `name`: Unique identifier for the hub.
-   `latitude` / `longitude`: Precise coordinates for rider navigation.
-   `zone`: Foreign key to a `Zone` model.
-   `is_active`: Controls whether the node is included in routing.

### 2. `OrderLeg` (orders/models.py)
Represents a single segment of a relay journey.
-   `order`: Parent `Order` object.
-   `leg_number`: Sequential index (1, 2, 3...).
-   `start_relay_node`: The hub where the leg starts (Null for the first leg/pickup).
-   `end_relay_node`: The hub where the leg ends (Null for the last leg/delivery).
-   `rider`: The `Rider` assigned specifically to this segment.
-   `hub_pin`: A secure 6-digit code for handoff verification.
-   `status`: Tracks the leg state (`Pending`, `Assigned`, `PickedUp`, `AtHub`, `Completed`).

---

## 🧭 Routing & Logic

### Greedy Hop Selection
The routing logic resides in `dispatcher/tasks.py` and follows a greedy algorithm:
-   **Corridor Filtering**: Only considers hubs within a geographic corridor between pickup and dropoff (using triangle inequality: $d1 + d2 \le direct \times 1.6$).
-   **Leg Constraints**: Attempts to keep each leg length around **90km**, with a hard validation cap of **100km**.
-   **Google Maps Integration**: Uses the Directions API to calculate real-world road distances and durations.

### Triggering
Relay routing is **manually triggered** by a dispatcher via the `generate-relay-route` API action. This converts a standard order (`is_relay_order=False`) into a relay order.

---

## 🔒 Security & Handoff (The Hub PIN)

To prevent package theft or incorrect handoffs:
1.  Each `OrderLeg` generates a random `hub_pin`.
2.  When a rider arrives at a hub to pick up a package (Leg $N$), the **Hub Agent** must verify the `hub_pin` before releasing the item.
3.  The system records the `dropped_at_hub_at` timestamp for accountability.

---

## 💰 Settlement & Payouts

Riders are paid a portion of the total order amount proportional to the distance they traveled.
-   **Payout Pool**: 80% of the `total_amount` of the order.
-   **Formula**:
    $$Payout_{Leg} = \left( \frac{Distance_{Leg}}{Total\_Distance} \right) \times Payout\_Pool$$
-   **Zone Bonus**: An optional `zone_compliance_bonus` can be applied if riders stay within their assigned geographical zone.

---

## 🛠️ Management & Seeding

-   **Admin Interface**: Dispatchers can manage hubs via the Django admin under `Relay Nodes`.
-   **Seeding**: Management commands like `seed_relay_network.py` are used to initialize the production hub network in Lagos.
