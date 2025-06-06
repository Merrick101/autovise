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
4. Profile Page (Logged-In Users) ✔️
5. Authentication Tests
6. Discount Logic Hook ✔️
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
- Created UserForm and UserProfileForm for updating core and extended user data
- Implemented profile_view with @login_required to ensure secure access
- Added display logic for is_first_time_buyer flag in the template
- Built responsive profile.html with Bootstrap styling and error feedback
- Registered URL path /users/profile/ to handle profile access and edits
- Confirmed successful form handling, validation, and data persistence

---

**Task 5 - Authentication Tests:**

Key Actions:

---

**Task 6 - Discount Logic Hook:**

Integrated the is_first_time_buyer flag from the UserProfile model into the cart and checkout flow. Applied a secure 10% discount logic for authenticated first-time buyers, applied after bundle discounts and before delivery. Profile flag is reset only after successful order creation to avoid race conditions. Added logging for discount application and profile update.

Key Actions:
- Linked profile logic into calculate_cart_summary()
- Discount displayed in the final cart summary context
- Profile flag reset in create_order_from_stripe_session only after order saved
- Server-side validation only (no client-side spoofing risk)
- Logged discount application and user state change

Optional enhancements (e.g., usage timestamp, profile banner) can be added later if time permits.

---

**Task 7 - Optional Enhancements:**

Key Actions:

---

## EPIC 09: Responsive Front-End UI

### Tasks

---

### Completion Notes

**Task 1 – Responsive Grid Layout:**

Key Actions:
- Implemented a fully responsive Bootstrap 5 grid using container, row, and col-* classes. Verified layout behavior across all key breakpoints:
  - Mobile (<768px)
  - Tablet (768px–1024px)
  - Desktop (>1024px)
- Product cards stack and resize correctly at each breakpoint
- Layout tested with Chrome DevTools on iPhone SE, iPad Mini, Galaxy S20, and 1440px desktop
- No layout overflow, horizontal scrolling, or clipping issues detected

---

**Task 2 – Implement Mobile-First Navigation:**

Implemented a fully responsive, accessible Bootstrap 5 navbar featuring a sticky top layout, logo, search bar, cart link, and profile dropdown. Navigation structure adapts across breakpoints with a hamburger toggle for mobile and horizontal menu layout for both mobile and desktop. Search input is always visible and adjusts width based on viewport. All focusable elements are keyboard-accessible and styled using :focus-visible for accessibility compliance.

Key Actions:
- Structured responsive layout using navbar-expand-lg, container-fluid, d-flex, and Bootstrap utility classes
- Integrated hamburger toggler with aria-expanded, aria-controls, and aria-label for accessibility
- Search bar made mobile-first (w-100) and adaptive to desktop width (w-lg-50)
- Replaced Login/Logout links with a Profile dropdown (conditionally rendered by auth state)
- Applied :focus-visible outline styling to .nav-link, .form-control, and .dropdown-item
- Verified tab order and screen-reader compatibility using semantic HTML and Bootstrap defaults

Optional enhancements (e.g., profile avatar, dynamic categories in dropdown) may be added later if time permits.

---

## Epic 07 - Admin Panel & Product Management

### Tasks

---

### Completion Notes

**Task 1 - Admin Interface for Product Management:**

Set up and refined the Django Admin interface for managing core catalog models: Product, Category, ProductType, Bundle, and ProductBundle. Enhanced form usability and layout for efficient catalog updates.

Key Actions:
- Verified and registered all core models in admin
- Enabled search, filters, and autocomplete fields across relevant models
- Added filters for tier, type, category, and stock to ProductAdmin
- Enabled inline bundle editing via ProductBundleInline
- Integrated image thumbnail preview into ProductAdmin list and detail views
- Switched description fields to use a WYSIWYG editor via django-ckeditor
- Organized Product and Bundle admin forms using grouped and collapsible fieldsets for clarity
Outcome:
- Admin users can manage the full product catalog efficiently with visual feedback, filters, and structured forms. Interface is optimized for both usability and data integrity.

---

**Task 2 - Admin Roles & Permissions Setup:**

Configured role-based access control within Django Admin, clearly separating superuser and staff responsibilities. Implemented group-based permissions for catalog management while restricting order access to superusers only.

Key Actions:
- Created a dedicated Catalog Editors group with permissions for Product, Category, Bundle, Tag, and ProductType
- Assigned staff users to the group using the Django Admin interface
- Verified staff can manage catalog data but cannot access Orders
- Implemented OrderAdmin permission overrides to enforce superuser-only access
- Confirmed admin visibility and field access reflects assigned role
Outcome:
- Staff users can manage product and bundle data, but not orders
- Superusers retain full access to all admin features
- Permissions are enforced securely and tested across user roles
- Admin dashboard visibility aligns with assigned permissions

---

**Task 3 – Register Core Models in Django Admin:**

Registered all core product models in the Django Admin, including Product, Category, ProductType, Tag, Bundle, and ProductBundle. Enhanced admin usability through filters, ordering, and custom list displays.

Key Actions:
- Registered all relevant models with @admin.register decorators
- Configured list_display, list_filter, and search_fields for improved visibility
- Enabled autocomplete_fields and filter_horizontal where helpful
- Customized ProductAdmin and BundleAdmin for efficient editing and catalog review
- Excluded Brand and ImageType models as they were deemed unnecessary for this project scope
Outcome:
- Admin interface is now fully usable for catalog review, filtering, and search, streamlining product management.

---

**Task 4 – Streamlined Product Editing & Inline Tools:**

This task was completed alongside earlier admin enhancements. No additional changes were required.

Key Outcomes:
- Admins can edit all core product fields (type, tier, variant, price, category, SKU, stock)
- ProductAdmin uses grouped fieldsets, readonly_fields, and autocomplete_fields for efficient input
- ProductBundleInline enables seamless inline editing of bundle-product relationships in BundleAdmin
- No new flags or variant models were necessary, as tagging and field structure already support all intended functionality
- Admin workflows are optimized for speed and accuracy. No redundant steps or excessive model hopping required. Task closed without additional migrations.

---

**Task 5 – Bundle Management Tools:**

Enhanced the Django Admin to support robust creation, validation, and editing of product bundles. Implemented pricing logic, bundle type assignment, and UI improvements to streamline the admin workflow for managing cross-category bundles.

Key Actions:
- Registered Bundle with inline editing via ProductBundleInline for adding products directly within the bundle form
- Enforced minimum 3-product requirement using custom BundleAdminForm with clean validation error handling
- Implemented auto-discount logic: 10% off total product prices when no discount_percentage is provided
- Allowed manual override of discount_percentage while showing a calculated preview in a collapsible "Preview" section
- Added bundle_type field to support Standard, Pro, and Special bundles, with list filter and admin visibility
- Organized BundleAdmin with grouped fieldsets and clear list displays including product count

Key Outcomes:
- Admins can confidently create and manage bundles with pricing control, rule validation, and visual clarity.
- Cross-category product relationships and flexible bundle typing are now supported, improving catalog configurability and consistency.

---

**Task 6 – Category & Subgroup Organization:**

Expanded the Django admin interface to support structured product categorization, enhanced filtering, and product status flag management. This improves visibility and control over catalog data for large inventories.

Key Actions:
- Registered and enabled CRUD access for Subcategory alongside Category and ProductType
- Added subcategory field to Product model with full admin integration
- Introduced product-level Boolean flags: featured, image_ready, and is_draft
- Displayed these flags in ProductAdmin.list_display and added them to list_filter
- Grouped the new flags into a collapsible Status Flags fieldset for visual clarity
- Verified all tag-based fields use filter_horizontal and remain editable

Key Outcomes:
- Admins can manage product categorization and subgroup structure
- Product flags and tags are visible, editable, and filterable
- Status filters (e.g., Featured, Draft, Image Ready) improve admin efficiency for large catalogs

---

**Task 7 - Optional Styling & UX Improvements:**

Key Actions:
- Enhanced the Django admin interface for improved usability and navigation using optional styling tools
- Installed and configured django-jazzmin with the flatly theme for a cleaner, responsive admin UI
- Enabled horizontal tab layout for Product and Bundle models using changeform_format and fieldset classes
- Reviewed and refined collapsible fieldsets to reduce visual clutter in long forms
- Implemented TabularInline for managing related models (ProductBundle in BundleAdmin)
- Added contextual help_text and inline titles for better admin readability and guidance

Key Outcomes:
- Admin interface is more user-friendly and visually polished
- Optional themes improve navigation and layout organization
- Long forms and inlines are logically grouped and simplified for faster management

---

**Task 8 - Admin Testing & Validation:**

Status: 
- Deferred

Reason: 
- Postponed until after initial database population and catalog setup. Full admin validation will occur during EPIC 17 (Testing) and EPIC 22 (Final Integration).

---

**Task 9 – Admin Dashboard Overview:** 

Status:
- Deferred  

Reason:
- Optional enhancement. Can be revisited during EPIC 22 (Final Polish) if time permits. Current admin layout is functional and visually modern using django-jazzmin.

---

## EPIC 08 

### Tasks

---

### Completion Notes

**Task 1 – Define Bundle Model Structure**


Key Actions:
- Implemented full Bundle model with all required fields including name, slug, description, discount percentage, price, and bundle type
- Added ManyToMany relationship to Product via custom through model `ProductBundle`
- Configured admin panel with inline product editing, auto-calculated discount preview, and product count display
- Enabled slug generation with fallback to prevent collisions
- Deferred optional bundle grouping field to future enhancement list

Key Actions:
- Bundle model is fully defined with discount logic and ManyToMany linkage
- Admin panel supports preview and editing
- Model is visible, tested, and filterable by bundle type

Future Enhancement: Bundle Grouping Field
- Description:
Add a category or tag field to the Bundle model to support logical grouping of bundles for admin filtering or storefront organization.

- Rationale:
Deferred for now due to the small number of bundles planned. Current filtering by bundle_type (Standard, Pro, Special) is sufficient. This enhancement can be revisited if bundle volume grows or if storefront filtering by bundle theme becomes necessary.

---

