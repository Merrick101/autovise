# Autovise – E-Commerce Platform for Automotive Accessories

**Autovise** is a Django-based e-commerce site offering automotive accessories, cleaning kits, electronic gear, and curated bundles. It features tiered products, dynamic bundles, user accounts, and Stripe-powered checkout with a focus on clean UX and production-ready practices.

## Table of Contents

1. [Features](#features)

2. [E-Commerce Business Model](#e-commerce-business-model)

3. [Marketing Strategy](#marketing-strategy)

4. [Wireframes & Facebook Mockup](#wireframes--facebook-mockup)

5. [Tech Stack](#tech-stack)

6. [Architecture & Data Model](#architecture--data-model)

7. [Project Structure](#project-structure) 

8. [Deployment Guide](#deployment-guide)

9. [Sitemaps & Robots](#sitemaps--robots)

10. [Testing](#testing)

11. [Validation Results](#validation-results-html--css--js--python)

12. [Accessibility & SEO Notes](#accessibility--seo-notes)

13. [Troubleshooting](#troubleshooting)



---

## Features

- **Product Catalog:** 150+ items, categorized by **Tier** (Standard/Pro), **Type**, **Category/Subcategory**
    
- **Curated Bundles:** Pre-defined sets with automatic **10% discount** vs combined RRP
    
- **Search & Filters:** Global search, tier filter, price sorting, pagination
    
- **User Accounts:** Django Allauth (+ Google), profile dashboard, saved items
    
- **Shopping Cart:** Session/DB backed, quantity updates, remove/clear
    
- **Checkout:** Stripe Payment Element (inline), success page, webhook updates
    
- **Admin Panel:** CRUD for products, bundles, orders; Jazzmin UI; review moderation
    
- **SEO & GDPR:** `robots.txt`, dynamic `sitemap.xml`, basic meta, cookie banner stub
    
- **Media & Static:** AWS S3 (prod) via `django-storages`; WhiteNoise for static files
    

### Frontend CRUD & Role-Based Controls

- **Reviews:**
	- _Create:_ Registered users can submit a product review.
	- _Read:_ Reviews display on product detail pages.
	- _Update/Delete:_ Admin-only controls for editing or removing reviews.
	
- **Saved Products:**
	- _Create/Delete:_ Logged-in users can add/remove products from their saved list.
	
- **Role-Based Access:**
	- Admin users see “Edit” and “Delete” buttons in product and review views.
	- Regular users are restricted to their own account actions and cannot see admin controls.

---

## E-Commerce Business Model

- **Revenue Streams:** single product sales, curated bundles (flat **10% off**), Pro tier up-sell
    
- **Delivery:** free for **first-time buyers** and for **orders ≥ £40**
    
- **Pricing:**
    
    - Standard: competitive
        
    - Pro: premium features/materials
        
    - Bundles: total of items minus fixed 10% discount
        
- **Audience:** car owners, detailing enthusiasts, everyday drivers
    

---

## Marketing Strategy

1. **Facebook Page:** brand presence, seasonal promos, bundle highlights
    
2. **Newsletter:** integrated signup; monthly offers, tips, new arrivals
    
3. **SEO:** descriptive titles/meta, `sitemap.xml` + `robots.txt`, image `alt` text
    
4. **UX:** clear categories, high-quality imagery, tiered presentation
    
---

### Wireframes & Facebook Mockup

![Homepage (Desktop)](/docs/wireframes/homepage_desktop.png)
![Homepage (Mobile)](/docs/wireframes/homepage_mobile.png) 
![Cart & Checkout (Mobile)](/docs/wireframes/cart_checkout_mobile.png)  
![Product Detail (Mobile)](/docs/wireframes/product_detail_mobile.png)  
![User Dashboard (Mobile)](/docs/wireframes/user_dashboard_mobile.png)  
![Admin Panel (Desktop)](/docs/wireframes/admin_panel_desktop.png)  
![Facebook Mockup](/docs/facebook_mockup/autovise_facebook_mockup.png)

---

## Tech Stack

- **Backend:** Django 5.x, Python 3.12
    
- **Database:** PostgreSQL (prod), SQLite (dev default)
    
- **Frontend:** Bootstrap 5, HTML5, CSS3
    
- **Auth:** Django Allauth (email + Google OAuth)
    
- **Payments:** Stripe (inline Payment Element)
    
- **Hosting:** Heroku
    
- **Storage:** AWS S3 (prod media)
    
- **Utilities:** Jazzmin, CKEditor/RichText, `django-widget-tweaks`
    

---

## Architecture & Data Model

### ERD Diagram

![ERD Diagram](/docs/erd/autovise_erd.png)

### Key Relationships (highlights):

- `auth_user` ↔ `user_profile` (**1–1**), `auth_user` → `shipping_address` (**1–M**, one default enforced in app)
    
- `product` belongs to `product_type`, `category`, optional `subcategory`; tags via **M2M**
    
- `bundle` ↔ `product` via **through** model `product_bundle`
    
- Saved items: M2M via `userprofile_saved_products` and `userprofile_saved_bundles`
    
- `review` targets **either** a product **or** a bundle (app validation ensures exactly one)
    
- `order` → `order_item` (**1–M**); item references product _or_ bundle; snapshot of price/subtotal
    
- Engagement: `newsletter_subscriber`, `contact_message` (status workflow + IP/UA)
    

> Keep the DBML source at `docs/erd/autovise.dbml` (optional) to regenerate the ERD on dbdiagram.io.

---

## Project Structure

```
autovise/                # project root
├── config/              # Django settings, URLs, WSGI
├── apps/                # Local Django apps
│   ├── products/        # Product, Category, Bundle models & views
│   ├── orders/          # Cart, checkout, Order models & views
│   ├── users/           # UserProfile, dashboard, saved items
│   ├── pages/           # Home, Contact, Privacy, etc.
├── templates/           # Base and app templates
├── static/              # Custom CSS, JS, images
├── media/               # User uploads (S3 in prod)
├── .env                 # Environment variables (not in VCS)
├── requirements.txt
└── manage.py
```

---

## Deployment Guide

### Getting Started (Local)

```bash
git clone https://github.com/your-username/autovise.git
cd autovise
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # or create .env from the next section
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Optional seed (shell):**

```bash
from decimal import Decimal
from apps.products.models import Category, ProductType, Product, Bundle

cat,_   = Category.objects.get_or_create(name="Accessories", slug="accessories")
ptype,_ = ProductType.objects.get_or_create(name="Mount")
Product.objects.get_or_create(
    name="Sample Product", variant="V", description="desc",
    type=ptype, tier="Standard", category=cat,
    price=Decimal("9.99"), stock=5, sku="SKU-SP", product_code="PC-SP", is_draft=False
)
Bundle.objects.get_or_create(
    name="Sample Bundle", description="bundle desc",
    discount_percentage=Decimal("10.00"), price=Decimal("0.00"), subtotal_price=Decimal("0.00"),
    bundle_type="Standard", sku="BNDL-001", bundle_code="bundle-sample"
)
```

### Environment Variables

Create `.env` in the project root (never commit). **Minimum** for local dev:

```bash
# Django
SECRET_KEY=change-me
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
SITE_ID=1
SITEMAP_PROTOCOL=http

# Email (dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=hello.autovise@gmail.com
CONTACT_RECIPIENTS=hello.autovise@gmail.com

# Stripe (test)
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

**Production (Heroku Config Vars):**

```
DEBUG=0
ALLOWED_HOSTS=autovise-<app>.herokuapp.com,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://autovise-<app>.herokuapp.com,https://yourdomain.com
SITE_ID=1
SITEMAP_PROTOCOL=https

DEFAULT_FROM_EMAIL=hello.autovise@gmail.com
CONTACT_RECIPIENTS=hello.autovise@gmail.com

# Stripe (live or test—be consistent)
STRIPE_PUBLISHABLE_KEY=pk_live_or_test
STRIPE_SECRET_KEY=sk_live_or_test
STRIPE_WEBHOOK_SECRET=whsec_from_dashboard_endpoint

# Optional S3 media
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=eu-west-1
AWS_S3_ACCESS_KEY_ID=...
AWS_S3_SECRET_ACCESS_KEY=...
```

---

## Deployment (Heroku)

```bash
heroku login
heroku apps:create autovise-prod
heroku buildpacks:add heroku/python -a autovise-prod
heroku addons:create heroku-postgresql:hobby-dev -a autovise-prod

# Config Vars (see Environment Variables)
heroku config:set SECRET_KEY=... DEBUG=0 SITE_ID=1 SITEMAP_PROTOCOL=https -a autovise-prod
heroku config:set ALLOWED_HOSTS=autovise-prod.herokuapp.com -a autovise-prod
heroku config:set CSRF_TRUSTED_ORIGINS=https://autovise-prod.herokuapp.com -a autovise-prod
heroku config:set STRIPE_PUBLISHABLE_KEY=... STRIPE_SECRET_KEY=... STRIPE_WEBHOOK_SECRET=... -a autovise-prod
heroku config:set DEFAULT_FROM_EMAIL=hello.autovise@gmail.com CONTACT_RECIPIENTS=hello.autovise@gmail.com -a autovise-prod

# Procfile
web: gunicorn config.wsgi:application --log-file -
release: python manage.py migrate && python manage.py collectstatic --noinput

git push heroku main
heroku run python manage.py migrate -a autovise-prod
heroku run python manage.py collectstatic --noinput -a autovise-prod
heroku run python manage.py createsuperuser -a autovise-prod
heroku open -a autovise-prod
```

### Stripe Webhooks (prod)

Create a Dashboard endpoint pointing to:

`https://<your-app>.herokuapp.com/orders/payments/webhook/`

Copy the signing secret into `STRIPE_WEBHOOK_SECRET`.

### Stripe Webhooks (local)

```bash
stripe login
stripe listen --forward-to http://127.0.0.1:8000/orders/payments/webhook/
# Paste the printed signing secret into STRIPE_WEBHOOK_SECRET in .env
```

---

## Sitemaps & Robots

Sitemap index and section routes:

```python
# config/urls.py
from django.urls import path
from django.contrib.sitemaps.views import index as sitemap_index, sitemap as sitemap_section
from apps.products.sitemaps import ProductSitemap, CategorySitemap, ProductTypeSitemap, BundleSitemap

sitemaps = {
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "product_types": ProductTypeSitemap,
    "bundles": BundleSitemap,
}

urlpatterns += [
    path("sitemap.xml", sitemap_index, {"sitemaps": sitemaps, "sitemap_url_name": "sitemap_section"}, name="sitemap"),
    path("sitemap-<section>.xml", sitemap_section, {"sitemaps": sitemaps}, name="sitemap_section"),
]
```

`robots.txt` (prod):

```makefile
User-agent: *
Disallow: /admin/
Disallow: /accounts/
Disallow: /checkout/
Disallow: /cart/
Disallow: /orders/
Disallow: /webhook/
Disallow: /media/
Allow: /

Sitemap: https://<your-domain>/sitemap.xml
```

---

## Testing

**Run complete test suite:**

`pytest -q`

### Automated Coverage (highlights)

#### Orders app

- Guest add-to-cart (product + bundle), inline checkout PaymentIntent creation
- Success view handling (?pi= or ?session_id=)
- Webhook marks orders paid; idempotent on replay

#### Products app

- Product & bundle list views: filters, search, sort, pagination
- Reviews (frontend CRUD + permissions): create/read, inline validation, single-review guard, admin update/delete
- Models & admin forms: slugging, rating aggregation, bundle price math, image path behavior

#### Sitemaps (SEO)

- Index & section sitemaps present and valid; robots.txt points to /sitemap.xml

#### Users app — Dashboard & Profile

- Login required redirects for profile/dashboard
- Dashboard context includes saved products/bundles and order count
- Save Product/Bundle requires login; toggling works
- Delete account removes the user and redirects to login

#### Pages app — Contact & Home

- Home view includes featured products/bundles + newsletter form
- Contact POST creates ContactMessage, captures IP/UA, and sends admin email
- Email failures are handled gracefully with a user-facing error message

Test suite passes locally; a benign staticfiles warning may appear when STATIC_ROOT isn’t present in dev.

### Manual QA (critical paths)

- Guest cart (add/update/remove/clear)
    
- Inline checkout (address → Payment Element mounts → success)

![Guest Cart](/docs/guest_checkout/guest_cart.png)

![Inline Checkout 1](/docs/guest_checkout/inline_checkout_001.png)

![Inline Checkout 2](/docs/guest_checkout/inline_checkout_002.png)
    
- Webhook marks order paid; confirmation email (prod)

![Checkout Success](/docs/guest_checkout/checkout_success_001.png)

![Checkout Confirmation](/docs/guest_checkout/checkout_success_002.PNG)
    
- Reviews UX: inline errors, success messages
    
- Saved items: remove/clear all
    
---

## Validation Results (HTML / CSS / JS / Python)

Full validation reports are accessible via (`docs/validators/reports`).

### HTML 

W3C Nu: **0 errors** across key templates exported by `tools/export_html.py`.  

### CSS

W3C Jigsaw: no errors (see `docs/validators/reports/report_css.pdf`).  

### JavaScript – JSHint (ES11, browser): 

Clean after small refactors and config header:

`/* jshint esversion: 11, browser: true, devel: true */ /* globals bootstrap, Stripe */ /* exported updateFilterParam */`

### Python – Flake8 (PEP8, 120 cols):

`flake8 apps config manage.py --max-line-length=120 # Result file empty ⇒ pass`

Evidence: before/after PDFs & text reports in `docs/validators/reports/`.

---

## Accessibility & SEO Notes

- WCAG-aware color contrast via Bootstrap defaults
    
- Descriptive `alt` text for product imagery
    
- ARIA on key form controls; label/field associations
    
- Sitemap + robots configured; descriptive titles/meta
    
---

## Troubleshooting

- **500 on add-to-cart (anon):** clear cookies or `python manage.py clearsessions`; ensure CSRF token present and `SessionMiddleware` enabled.
    
- **CSRF 403 (prod):** add full origin to `CSRF_TRUSTED_ORIGINS` (scheme + host).
    
- **DisallowedHost:** add domain to `ALLOWED_HOSTS`.
    
- **Static missing (Heroku):** WhiteNoise enabled; `collectstatic` not disabled.
    
- **Sitemap shows `example.com`:** configure **Sites** (Admin → Sites) and `SITEMAP_PROTOCOL`.
    
---

## Credits
- Developer: Merrick Minogue
- PostgreSQL Database Provider: Code Institute
- Payments: Stripe
- Hosting: Heroku
- Icons: Font Awesome
- Admin UI: Jazzmin
- Image Storage: AWS S3
