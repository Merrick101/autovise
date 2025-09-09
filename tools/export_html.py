"""
Export key HTML pages for validation purposes.

Run with:
python manage.py shell
Then:
from tools.export_html import main
main()

Outputs to: docs/validators/pages/*.html

Located at tools/export_html.py
"""

from pathlib import Path
from typing import Optional, Dict, Iterable, Tuple

from django.test import Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model

from apps.products.models import Product, Bundle, Category, ProductType, Review

OUTDIR = Path("docs/validators/pages")
OUTDIR.mkdir(parents=True, exist_ok=True)


def try_reverse(name: str, kwargs: Optional[Dict] = None) -> Optional[str]:
    try:
        return reverse(name, kwargs=kwargs or {})
    except NoReverseMatch:
        print(f"[-] Skipping missing route: {name}")
        return None


def save(client: Client, url: Optional[str], name: str) -> None:
    if not url:
        return
    resp = client.get(url, secure=True, follow=True)
    path = OUTDIR / f"{name}.html"
    path.write_bytes(resp.content)
    print(f"[{resp.status_code}] {url} -> {path}")


def ensure_sample_objects() -> Tuple[Product, Bundle]:
    cat = Category.objects.first() or Category.objects.create(name="Accessories", slug="accessories")
    ptype = ProductType.objects.first() or ProductType.objects.create(name="Mount")

    prod = Product.objects.first()
    if not prod:
        prod = Product.objects.create(
            name="Sample Product", variant="V", description="desc",
            type=ptype, tier="Standard", category=cat,
            price=9.99, stock=5, sku="SKU-SP", product_code="PC-SP"
        )

    bund = Bundle.objects.first()
    if not bund:
        bund = Bundle.objects.create(
            name="Sample Bundle", description="bundle desc",
            discount_percentage=10, price=0, subtotal_price=0,
            bundle_type="Standard", sku="BNDL-001", bundle_code="bundle-sample"
        )

    return prod, bund


def ensure_sample_reviews(author, product: Product, bundle: Bundle) -> Tuple[Review, Review]:
    """Create one product review and one bundle review by 'author' if they don't exist."""
    pr = Review.objects.filter(user=author, product=product).first()
    if not pr:
        pr = Review.objects.create(user=author, product=product, rating=4, comment="Looks good.")

    br = Review.objects.filter(user=author, bundle=bundle).first()
    if not br:
        br = Review.objects.create(user=author, bundle=bundle, rating=5, comment="Great bundle.")

    return pr, br


def login_sample_user(client: Client) -> None:
    """Login a normal user to capture authenticated navbar/profile states."""
    User = get_user_model()
    user, _ = User.objects.get_or_create(username="validator_user", defaults={"email": "validator@example.com"})
    if not user.check_password("pw"):
        user.set_password("pw")
        user.save()
    client.login(username="validator_user", password="pw")


def login_staff_user(client: Client):
    User = get_user_model()
    staff, _ = User.objects.get_or_create(
        username="validator_staff",
        defaults={"email": "validator_staff@example.com", "is_staff": True},
    )
    if not staff.is_staff:
        staff.is_staff = True
        staff.save()
    if not staff.check_password("pw"):
        staff.set_password("pw")
        staff.save()
    client.login(username="validator_staff", password="pw")
    return staff


def main() -> None:
    product, bundle = ensure_sample_objects()
    c = Client()

    # Anonymous pages
    anon_pages = [
        (try_reverse("home"), "home"),
        (try_reverse("products:product_list"), "products_list"),
        (try_reverse("products:bundle_list"), "bundles_list"),
        (try_reverse("products:product_detail", {"pk": product.id}), "product_detail"),
        (try_reverse("products:bundle_detail", {"bundle_id": bundle.id}), "bundle_detail"),
        (try_reverse("orders:cart"), "cart"),
        (try_reverse("orders:checkout"), "checkout"),
        (try_reverse("orders:inline_checkout"), "inline_checkout"),
        (try_reverse("orders:success"), "checkout_success"),
        (try_reverse("orders:order_history"), "order_history"),
        (try_reverse("pages:privacy"), "privacy"),
        (try_reverse("pages:terms"), "terms"),
        (try_reverse("pages:contact"), "contact"),
        (try_reverse("account_login"), "account_login"),     # allauth
        (try_reverse("account_signup"), "account_signup"),   # allauth
        (try_reverse("sitemap"), "sitemap"),
    ]
    for url, name in anon_pages:
        save(c, url, name)

    # Authenticated (normal user) variants
    login_sample_user(c)
    auth_pages = [
        (try_reverse("products:product_list"), "products_list_auth"),
        (try_reverse("products:bundle_list"), "bundles_list_auth"),
        (try_reverse("users:dashboard"), "dashboard_auth"),
        (try_reverse("users:profile"), "profile_auth"),
    ]
    for url, name in auth_pages:
        save(c, url, name)

    # Staff-only: review edit/delete pages (product & bundle)
    staff = login_staff_user(c)
    pr, br = ensure_sample_reviews(author=staff, product=product, bundle=bundle)

    review_pages = [
        (try_reverse("products:review_update", {"review_id": pr.id}), "review_edit_product"),
        (try_reverse("products:review_delete", {"review_id": pr.id}), "review_delete_product"),
        (try_reverse("products:review_update", {"review_id": br.id}), "review_edit_bundle"),
        (try_reverse("products:review_delete", {"review_id": br.id}), "review_delete_bundle"),
    ]
    for url, name in review_pages:
        save(c, url, name)


if __name__ == "__main__":
    main()
