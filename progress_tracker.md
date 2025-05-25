# Autovise Progress Tracker

## EPIC 05: Shopping Cart & Checkout Flow

### Tasks

- Task 1 – Cart model & Session Handling ✔️
- Task 2 – Add to Cart Functionality ✔️
- Task 3 – Cart Page with Summary ✔️
- Task 4 – Discount Application ✔️
- Task 5 - Shipping & Delivery Rules ✔️

---

### Completion Notes

**Task 3 Complete:** 
- Cart page implemented with full interactivity, pricing logic, and accessible controls.
- Template supports future discount display and aligns with UX requirements.

---

**Task 4 Complete:**

Completed automatic discount handling for first-time users and bundle items.

- First-time buyer status is determined via the Order model
- Bundle discounts apply based on product type or attribute check
- Total calculation now supports both discounts with correct stacking order
- Cart view updated to reflect savings using clear messaging
- Discount messaging is accessible and ARIA-compliant

Ready for integration into checkout flow in EPIC 05 Task 6.

---

**Task 5 Complete:**

Implemented delivery logic based on business rules:
- Free delivery applied if cart total ≥ £40 or user is a first-time buyer
- Default £4.99 delivery fee added when no free conditions are met
- Estimated delivery date calculated as 2 days from the current date

All logic is handled within the cart summary helper, making it reusable for checkout and confirmation views. Delivery status, fee, and estimated date are clearly shown in the cart view.

---

