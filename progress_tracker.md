# Autovise Progress Tracker

## EPIC 05: Shopping Cart & Checkout Flow

### Tasks

1. Cart model & Session Handling ✔️
2. Add to Cart Functionality ✔️
3. Cart Page with Summary ✔️
4. Discount Application ✔️
5. Shipping & Delivery Rules ✔️
6. Stripe Integration for Checkout ✔️
7. Order Confirmation & Thank You Page ✔️
8. Apply Tier & Bundle Rules in Backend ✔️
9. (Optional) Cart Analytics or Admin Monitoring
10. Admin Panel Setup ✔️
11. Basic Frontend for Checkout Flow ✔️

---

### Completion Notes

**Task 3 - Cart Page with Summary:** 

Key Actions:
- Cart page implemented with full interactivity, pricing logic, and accessible controls.
- Template supports future discount display and aligns with UX requirements.

---

**Task 4 - Discount Application:**

Completed automatic discount handling for first-time users and bundle items.

Key Actions:
- First-time buyer status is determined via the Order model
- Bundle discounts apply based on product type or attribute check
- Total calculation now supports both discounts with correct stacking order
- Cart view updated to reflect savings using clear messaging
- Discount messaging is accessible and ARIA-compliant

Ready for integration into checkout flow in EPIC 05 Task 6.

---

**Task 5 - Shipping & Delivery Rules:**

Implemented delivery logic based on business rules:

Key Actions:
- Free delivery applied if cart total ≥ £40 or user is a first-time buyer
- Default £4.99 delivery fee added when no free conditions are met
- Estimated delivery date calculated as 2 days from the current date

All logic is handled within the cart summary helper, making it reusable for checkout and confirmation views. Delivery status, fee, and estimated date are clearly shown in the cart view.

---

**Task 6 - Stripe Integration for Checkout:**

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

**Task 7 - Order Confirmation & Thank You Page:**

Implemented post-payment confirmation flow to display order details, contact links, and send an optional receipt via email after successful Stripe checkout.

Key Actions:
- Created checkout_success_view to display order summary by session ID
- Designed user-friendly success template with order info and support links
- Added plaintext email confirmation template using Django’s console backend
- Sent confirmation email upon webhook-triggered order creation

---

**Task 10 - Admin Panel Setup:**

Configured Django admin for efficient management and testing of products, carts, and orders. Admin panel now supports filtering, inline editing, and visibility into all key data models.

Key Actions:
- Registered Product, Cart, CartItem, Order, and OrderItem models
- Customized admin list views with filters, search, and date hierarchy
- Added inline OrderItem editing within Order admin
- Prepared admin with test data to support checkout and webhook testing

---

**Task 11 - Basic Frontend for Checkout Flow:**

Implemented a minimal frontend interface to support manual testing of the cart and Stripe checkout flow. Product listings and cart functionality are now testable through basic templates and views.

Key Actions:
- Created product list view with “Add to Cart” buttons
- Rendered product name and price with quantity inputs
- Updated cart page to show full item breakdown and a checkout link
- Connected cart and checkout logic with clean template integration

---

**Task 8 - Apply Tier & Bundle Rules in Backend:**

Key Actions:
- Implemented 10% automatic discount for predefined bundle products using product.type.name == "bundle"
- Added tier and bundle flags (tier, is_bundle) to cart item data for display and analytics
- Applied 10% first-time user discount for authenticated users (single-use logic)
- Delivery fee logic added with conditional free shipping for first-time buyers or totals ≥ £40
- Final cart summary includes subtotal, discounts, delivery, and grand total
- Logging added for cart calculations to support debugging and admin review
- Manual multi-item bundle detection is out of scope for this phase (deferred)

---

**Task 9 - (Optional) Cart Analytics or Admin Monitoring:**

Key Actions:
- Cart model registered in admin with user, created_at, updated_at, and is_active fields
- Added custom admin filter for abandoned carts (inactive for 30+ minutes)
- Signal-based logging implemented for Cart and CartItem creation/updates
- Session-to-DB cart merge events logged on user login
- Documented cart storage behavior, expiration rules, and analytics potential in README
- Future enhancements (e.g., recovery emails, cron cleanup) noted but out of scope for this phase

---

## EPIC 06: User Accounts & Authentication

### Tasks

1. Install & Configure Django Allauth ✔️
2. Signup, Login, Logout Flow ✔️
3. Custom User Model & Profile Extension ✔️
4. Profile Page (Logged-In Users)
5. Authentication Tests
6. Discount Logic Hook
7. Optional Enhancements

---

### Completion Notes

**Task 1 - Install & Configure Django Allauth:**

Key Actions:
- Installed and integrated django-allauth into the project
- Registered required apps and authentication backends in settings.py
- Updated deprecated ACCOUNT_* settings to modern ACCOUNT_LOGIN_METHODS and ACCOUNT_SIGNUP_FIELDS
- Configured redirect URLs for login and logout flows
- Included allauth URLs in the main urls.py
- Verified working /accounts/login/ and /accounts/signup/ views
- Custom template overrides to be handled in Task 2

---

**Task 2 - Signup, Login, Logout Flow:**

Key Actions:
- Custom Allauth templates created for signup, login, and logout views
- All forms styled using Bootstrap 5 and integrated into base layout
- Form fields structured with accessible labels and ARIA attributes
- Success and error messages displayed via Bootstrap alerts with screen reader support
- Placeholder logic added for “first-time buyer” flag (to be linked to profile in Task 3)
- Authentication flow now visually consistent with Autovise branding and UX

---

**Task 3 - Custom User Model & Profile Extension:**

Key Actions:
- Created `UserProfile` model with a OneToOne relationship to Django’s `User`
- Added key fields: `is_first_time_buyer`, `address`, `phone_number`, and `preferences`
- Implemented `post_save` signal to automatically create a profile on user registration
- Registered signal via `UsersConfig.ready()` and confirmed proper app config usage
- Applied migrations successfully with all new fields in place

---

**Task 4 - Profile Page (Logged-In Users):**

Key Actions:
