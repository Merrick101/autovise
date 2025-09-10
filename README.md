# Autovise – E-Commerce Platform for Automotive Accessories

**Autovise** is a premium Django-based e-commerce site offering automotive accessories, cleaning kits, electronic gear, and curated bundles. Designed for a seamless user experience, Autovise features tiered products, dynamic bundles, user accounts, and Stripe-powered checkout.

## Table of Contents

1. (Features)[#features]
    
2. Tech Stack
    
3. Architecture & Data Model
    
4. Project Structure
    
5. E-Commerce Business Model
    
6. Marketing Strategy
    
7. Getting Started (Local)
    
8. Environment Variables
    
9. Deployment (Heroku)
    
10. Sitemaps & Robots
    
11. Testing
    
12. Validation Results (HTML / CSS / JS / Python)
    
13. Accessibility & SEO Notes
    
14. Troubleshooting
    

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

**Key Relationships (highlights):**

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

## Deployment Guide

### Getting Started (Local)

`git clone https://github.com/your-username/autovise.git cd autovise  python -m venv .venv # macOS/Linux source .venv/bin/activate # Windows .venv\Scripts\activate  pip install -r requirements.txt cp .env.example .env  # or create .env manually (see below)  python manage.py migrate python manage.py createsuperuser python manage.py runserver`

**Optional seed (shell):**

`from apps.products.models import Category, ProductType, Product, Bundle from decimal import Decimal cat,_ = Category.objects.get_or_create(name="Accessories", slug="accessories") ptype,_ = ProductType.objects.get_or_create(name="Mount") Product.objects.get_or_create(     name="Sample Product", variant="V", description="desc",     type=ptype, tier="Standard", category=cat,     price=Decimal("9.99"), stock=5, sku="SKU-SP", product_code="PC-SP", is_draft=False) Bundle.objects.get_or_create(     name="Sample Bundle", description="bundle desc",     discount_percentage=Decimal("10.00"), price=Decimal("0.00"), subtotal_price=Decimal("0.00"),     bundle_type="Standard", sku="BNDL-001", bundle_code="bundle-sample")`

### Environment Variables

Create `.env` in the project root (never commit). **Minimum** for local dev:

`# Django SECRET_KEY=change-me DEBUG=1 ALLOWED_HOSTS=127.0.0.1,localhost CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost SITE_ID=1 SITEMAP_PROTOCOL=http  # Email (dev) EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend DEFAULT_FROM_EMAIL=hello.autovise@gmail.com CONTACT_RECIPIENTS=hello.autovise@gmail.com  # Stripe (test keys) STRIPE_PUBLIC_KEY=pk_test_xxx STRIPE_SECRET_KEY=sk_test_xxx STRIPE_WEBHOOK_SECRET=whsec_xxx`

**Production (Heroku Config Vars):**

`DEBUG=0 ALLOWED_HOSTS=autovise.herokuapp.com,yourdomain.com CSRF_TRUSTED_ORIGINS=https://autovise.herokuapp.com,https://yourdomain.com SITEMAP_PROTOCOL=https DEFAULT_FROM_EMAIL=hello.autovise@gmail.com CONTACT_RECIPIENTS=hello.autovise@gmail.com # Stripe live or test (be consistent): STRIPE_PUBLIC_KEY=pk_live_or_test STRIPE_SECRET_KEY=sk_live_or_test STRIPE_WEBHOOK_SECRET=whsec_from_dashboard # Optional S3 AWS_STORAGE_BUCKET_NAME=your-bucket AWS_S3_REGION_NAME=eu-west-1 AWS_S3_ACCESS_KEY_ID=... AWS_S3_SECRET_ACCESS_KEY=...`

---

## Deployment (Heroku)

`heroku login heroku apps:create autovise-prod heroku buildpacks:add heroku/python -a autovise-prod heroku addons:create heroku-postgresql:hobby-dev -a autovise-prod  # Config Vars (see .env above) heroku config:set SECRET_KEY=... DEBUG=0 SITE_ID=1 SITEMAP_PROTOCOL=https -a autovise-prod heroku config:set ALLOWED_HOSTS=autovise-prod.herokuapp.com -a autovise-prod heroku config:set CSRF_TRUSTED_ORIGINS=https://autovise-prod.herokuapp.com -a autovise-prod heroku config:set STRIPE_PUBLIC_KEY=... STRIPE_SECRET_KEY=... STRIPE_WEBHOOK_SECRET=... -a autovise-prod heroku config:set DEFAULT_FROM_EMAIL=hello.autovise@gmail.com CONTACT_RECIPIENTS=hello.autovise@gmail.com -a autovise-prod  # Procfile echo "web: gunicorn config.wsgi" > Procfile  git push heroku main heroku run python manage.py migrate -a autovise-prod heroku run python manage.py collectstatic --noinput -a autovise-prod heroku run python manage.py createsuperuser -a autovise-prod heroku open -a autovise-prod`

### Stripe Webhooks (prod)

Create a Dashboard endpoint pointing to:

`https://<your-app>.herokuapp.com/orders/payments/webhook/`

Copy the signing secret into `STRIPE_WEBHOOK_SECRET`.

### Stripe Webhooks (local)

`stripe login stripe listen --forward-to http://127.0.0.1:8000/orders/payments/webhook/ # Paste displayed Signing secret into .env as STRIPE_WEBHOOK_SECRET`

---

## Sitemaps & Robots

Sitemap index and section routes:

`# config/urls.py from django.contrib.sitemaps.views import index as sitemap_index, sitemap as sitemap_section from apps.products.sitemaps import ProductSitemap, CategorySitemap, ProductTypeSitemap, BundleSitemap  sitemaps = {     "products": ProductSitemap,     "categories": CategorySitemap,     "product_types": ProductTypeSitemap,     "bundles": BundleSitemap, }  urlpatterns += [     path("sitemap.xml", sitemap_index, {"sitemaps": sitemaps, "sitemap_url_name": "sitemap_section"}, name="sitemap"),     path("sitemap-<section>.xml", sitemap_section, {"sitemaps": sitemaps}, name="sitemap_section"), ]`

`robots.txt` (prod):

`User-agent: * Disallow: /admin/ Disallow: /accounts/ Disallow: /checkout/ Disallow: /cart/ Disallow: /orders/ Disallow: /webhook/ Disallow: /media/ Allow: /  Sitemap: https://<your-domain>/sitemap.xml`

---

## Testing

**Run complete test suite:**

`pytest -q`

### Automated Coverage (highlights)

#### Orders App

#### Pages App

#### Products App

#### Users App

- **Reviews (frontend CRUD + permissions):** create/read, validation, single-review guard, admin update/delete UI & perms
    
- **Product & Bundle Lists:** filters, search, sort, pagination
    
- **Models & Admin Forms:** slugging, ratings aggregation, bundle price math, form behaviors
    
- **Checkout / Payments:** create PaymentIntent; success view; webhook marking orders paid (idempotent)
    
- **Sitemaps:** index & sections valid; robots references sitemap
    

### Manual QA (critical paths)

- Guest cart (add/update/remove/clear)
    
- Inline checkout (address → Payment Element mounts → success)
    
- Webhook marks order paid; confirmation email (prod)
    
- Reviews UX: inline errors, success messages
    
- Saved items: remove/clear all
    

> Tests are isolated (no real Stripe calls). A benign `staticfiles` warning may appear locally.

---

## Validation Results (HTML / CSS / JS / Python)

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

### Wireframes & Facebook Mockup

![Homepage (Desktop)](/docs/wireframes//homepage_desktop.png)
![Homepage (Mobile)](/docs/wireframes/homepage_mobile.png) 
![Cart & Checkout (Mobile)](/docs/wireframes/cart_checkout_mobile.png)  
![Product Detail (Mobile)](/docs/wireframes/product_detail_mobile.png)  
![User Dashboard (Mobile)](/docs/wireframes/user_dashboard_mobile.png)  
![Admin Panel (Desktop)](/docs/wireframes/admin_panel_desktop.png)  
![Facebook Mockup](/docs/facebook_mockup/autovise_facebook_mockup.png)

---

**Project value:** Autovise demonstrates a complete, production-ready Django stack with clean separation of concerns, role-based CRUD, real payment integration, SEO & accessibility considerations, and a thorough test/validation story suitable for assessment and hand-off.
