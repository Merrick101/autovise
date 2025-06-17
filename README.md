# Autovise – E-Commerce Platform for Automotive Accessories

**Autovise** is a premium Django-based e-commerce site offering automotive accessories, cleaning kits, electronic gear, and curated bundles. Designed for a seamless user experience, Autovise features tiered products, dynamic bundles, user accounts, and Stripe-powered checkout.

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Environment Variables](#environment-variables)
6. [Deployment (Heroku)](#deployment-heroku)
7. [Testing](#testing)
8. [Contributing](#contributing)
9. [Security](#security)

---

## Features

* **Product Catalog**: Over 200 products, categorized by tier (Standard/Pro), type, and subcategory
* **Curated Bundles**: Pre-defined bundles with automatic 10% discount logic
* **Search & Filters**: Global search bar, tier filters, price sorting
* **User Accounts**: Registration, login (via Django Allauth + Google OAuth), profile dashboard
* **Shopping Cart**: Persistent cart (DB or session), cart preview dropdown, item counter badge
* **Checkout**: Stripe test-mode integration, order confirmation email
* **Admin Panel**: CRUD for products, bundles, orders; Jazzmin-enhanced UI
* **SEO & GDPR**: `robots.txt`, dynamic `sitemap.xml`, basic meta tags, cookie banner stub
* **Media Storage**: AWS S3 via `django-storages`; static files served with WhiteNoise

## Tech Stack

* **Backend:** Django 5.2, Python 3.12
* **Database:** PostgreSQL
* **Frontend:** Bootstrap 5, HTML5, CSS3
* **Authentication:** Django Allauth (email + Google OAuth)
* **Payments:** Stripe Checkout (test keys)
* **Hosting:** Heroku
* **Storage:** AWS S3
* **Other:** Jazzmin, CKEditor, django-widget-tweaks

## Project Structure

```
autovise/                # project root
├── config/              # Django settings, URLs, WSGI
├── apps/                # Local Django apps
│   ├── products/        # Product, Category, Bundle models & views
│   ├── orders/          # Cart, checkout, Order models & views
│   ├── users/           # UserProfile, dashboard, saved items
│   ├── pages/           # Home, Contact, Privacy, etc.
│   └── assets/          # Static asset management
├── templates/           # Base and app templates
├── static/              # Custom CSS, JS, images
├── media/               # User uploads (S3 in prod)
├── .env                 # Environment variables (not in VCS)
├── requirements.txt
└── manage.py
```

---

## Wireframes & Facebook Mockup

![Wireframe 1](/static/images/documentation/homepage_desktop.png)

![Wireframe 2](/static/images/documentation/homepage_mobile.png)

![Wireframe 3](/static/images/documentation/cart_checkout_mobile.png)

![Wireframe 4](/static/images/documentation/product_detail_mobile.png)

![Wireframe 5](/static/images/documentation/user_dashboard_mobile.png)

![Wireframe 6](/static/images/documentation/admin_panel_desktop.png)

![Facebook Mockup](/static/images/documentation/autovise_facebook_mockup.png)

## Getting Started

### Prerequisites

* Python 3.12+
* PostgreSQL
* Git

### Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/your-username/autovise.git
   cd autovise
   ```
2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .venv\Scripts\activate    # Windows
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Create and copy `.env`:

   ```bash
   cp .env.example .env
   ```

### Configuration

1. Fill in `.env` with your values (see [Environment Variables](#environment-variables)).
2. Apply migrations and create a superuser:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Running Locally

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the site and `http://127.0.0.1:8000/admin/` for the admin panel.

## Environment Variables

| Key                                | Description                        |
| ---------------------------------- | ---------------------------------- |
| SECRET\_KEY                        | Django secret key                  |
| DEBUG                              | `True` or `False`                  |
| ALLOWED\_HOSTS                     | Comma-separated hostnames          |
| DB\_NAME, DB\_USER, DB\_PASSWORD   | PostgreSQL credentials             |
| DB\_HOST, DB\_PORT                 | PostgreSQL host & port             |
| AWS\_ACCESS\_KEY\_ID               | AWS S3 access key ID               |
| AWS\_SECRET\_ACCESS\_KEY           | AWS S3 secret access key           |
| AWS\_STORAGE\_BUCKET\_NAME         | S3 bucket name                     |
| AWS\_S3\_REGION\_NAME              | S3 bucket region                   |
| AWS\_S3\_CUSTOM\_DOMAIN            | Custom domain for S3 (no protocol) |
| STRIPE\_SECRET\_KEY                | Stripe secret key (test/live)      |
| STRIPE\_PUBLISHABLE\_KEY           | Stripe publishable key             |
| STRIPE\_WEBHOOK\_SECRET            | Stripe webhook signing secret      |
| GOOGLE\_CLIENT\_ID                 | Google OAuth client ID             |
| GOOGLE\_CLIENT\_SECRET             | Google OAuth client secret         |
| EMAIL\_BACKEND, EMAIL\_HOST, PORT  | Email settings (e.g. SMTP)         |
| EMAIL\_HOST\_USER, EMAIL\_PASSWORD | SMTP credentials                   |
| DEFAULT\_FROM\_EMAIL               | Default sender email address       |
| SEND\_ORDER\_CONFIRMATION\_EMAIL   | `True` to send order emails        |
| USE\_CELERY\_FOR\_EMAIL            | `True` to queue emails via Celery  |

## Deployment (Heroku)

1. Set Heroku Config Vars (see [Environment Variables](#environment-variables)).
2. Push to Heroku:

   ```bash
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py collectstatic --noinput
   ```
3. Visit `https://<your-app>.herokuapp.com/`.

## Testing

Autovise includes unit tests and manual test summaries for each core app.

### Run All Tests

```bash
pytest
```

### Orders App – Unit Tests

* Total tests run: 16, Failures: 0
* Key tests: CartItem subtotal, cart total aggregation, OrderItem XOR constraints, checkout logic.

### Pages App – Unit Tests

* Total tests run: 8, Failures: 0
* Key tests: Home, Contact, Privacy, Terms views; Newsletter subscription.

### Products App – Unit Tests

* Total tests run: 26, Failures: 0
* Key tests: Bundle pricing logic, tier validation, product filtering and pagination.

### Users App – Unit Tests

* Total tests run: 6, Failures: 0
* Key tests: UserProfile **str**, dashboard view, save/unsave flows, account deletion.

### Manual Testing

* Verified checkout with Stripe test keys
* Cart preview and badge functionality
* OAuth login flows (Google)
* Static & media file serving
* Responsive design across breakpoints

## Validation

![HTML Validation - Base](/static/images/documentation/base_template_html_validation.png)

![HTML Validation - Home](/static/images/documentation/home_template_html_validation.png)

![CSS Validation](/static/images/documentation/autovise_css_validator.PNG)

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/YourFeature`
3. Commit changes: `git commit -m "Add feature..."`
4. Push to your branch: `git push origin feature/YourFeature`
5. Open a Pull Request.

Please follow existing code style and include tests for new features.

## Security

* **DEBUG=False** in production.
* Sensitive keys managed via environment variables.
* HTTPS enforced, secure cookies, HSTS when not in debug.

---

*This README provides a complete guide for setup, development, testing, and deployment of the Autovise platform.*
