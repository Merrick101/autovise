# Autovise Progress Tracker

## EPIC 05: Shopping Cart & Checkout Flow

### Tasks

1. Cart model & Session Handling ✔️
2. Add to Cart Functionality ✔️
3. Cart Page with Summary ✔️
4. Discount Application ✔️
5. Shipping & Delivery Rules ✔️
6. Stripe Integration for Checkout
7. Order Confirmation & Thank You Page
8. Checkout Testing
9. Apply Tier & Bundle Rules in Backend
10. (Optional) Cart Analytics or Admin Monitoring
11. Admin Panel Setup
12. Basic Frontend for Checkout Flow

---

### Completion Notes

**Task 3 Complete:** 

Key Actions:
- Cart page implemented with full interactivity, pricing logic, and accessible controls.
- Template supports future discount display and aligns with UX requirements.

---

**Task 4 Complete:**

Completed automatic discount handling for first-time users and bundle items.

Key Actions:
- First-time buyer status is determined via the Order model
- Bundle discounts apply based on product type or attribute check
- Total calculation now supports both discounts with correct stacking order
- Cart view updated to reflect savings using clear messaging
- Discount messaging is accessible and ARIA-compliant

Ready for integration into checkout flow in EPIC 05 Task 6.

---

**Task 5 Complete:**

Implemented delivery logic based on business rules:

Key Actions:
- Free delivery applied if cart total ≥ £40 or user is a first-time buyer
- Default £4.99 delivery fee added when no free conditions are met
- Estimated delivery date calculated as 2 days from the current date

All logic is handled within the cart summary helper, making it reusable for checkout and confirmation views. Delivery status, fee, and estimated date are clearly shown in the cart view.

---

**Task 6 Complete:**

Successfully implemented secure payment processing using Stripe Checkout, integrated with Django via a verified webhook that creates Order and OrderItem records post-payment.

Key Actions:
- Created dynamic Stripe Checkout Sessions with product line_items
- Passed user_id and product_ids as session metadata for webhook access
- Added /checkout/success/ and /checkout/cancel/ routes for user feedback
- Implemented stripe_webhook_view with signature verification and logging
- Created OrderItem model and create_order_from_stripe_session() function
- Tested local webhook delivery with stripe listen and trigger checkout.session.completed
- Verified cart clearance and secure order creation logic

---

**Task 7 Complete:**

Implemented post-payment confirmation flow to display order details, contact links, and send an optional receipt via email after successful Stripe checkout.

Key Actions:
- Created checkout_success_view to display order summary by session ID
- Designed user-friendly success template with order info and support links
- Added plaintext email confirmation template using Django’s console backend
- Sent confirmation email upon webhook-triggered order creation

---

**Task 11 Complete:**

Configured Django admin for efficient management and testing of products, carts, and orders. Admin panel now supports filtering, inline editing, and visibility into all key data models.

Key Actions:
- Registered Product, Cart, CartItem, Order, and OrderItem models
- Customized admin list views with filters, search, and date hierarchy
- Added inline OrderItem editing within Order admin
- Prepared admin with test data to support checkout and webhook testing

---

**Task 12 Complete:**

Implemented a minimal frontend interface to support manual testing of the cart and Stripe checkout flow. Product listings and cart functionality are now testable through basic templates and views.

Key Actions:
- Created product list view with “Add to Cart” buttons
- Rendered product name and price with quantity inputs
- Updated cart page to show full item breakdown and a checkout link
- Connected cart and checkout logic with clean template integration

---
