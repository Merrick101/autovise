"""
Tests for product and bundle reviews in the frontend.
These tests focus on the views and templates, ensuring that users can
submit reviews, see success/error messages, and that admin controls are
functioning as expected.
Located at apps/products/tests/test_reviews_frontend.py
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.products.models import Product, Bundle, Category, ProductType, Review

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="pw")


@pytest.fixture
def staff(db):
    return User.objects.create_user(username="admin", password="pw", is_staff=True)


@pytest.fixture
def category(db):
    return Category.objects.create(name="Accessories", slug="accessories")


@pytest.fixture
def ptype(db):
    return ProductType.objects.create(name="Accessory")


@pytest.fixture
def product(db, category, ptype):
    return Product.objects.create(
        name="Phone Mount",
        variant="Dash",
        description="desc",
        type=ptype,
        tier="Standard",
        category=category,
        price=9.99,
        stock=10,
        sku="PM-001",
        product_code="P-PM-001",
    )


@pytest.fixture
def bundle(db):
    return Bundle.objects.create(
        name="Starter Kit",
        description="Bundle desc",
        discount_percentage=10,
        price=0,
        subtotal_price=0,
        bundle_type="Standard",
        sku="BNDL-001",
        bundle_code="bundle-starter-kit",
    )


def get(content, needle):
    return needle in content.decode() if isinstance(content, (bytes, bytearray)) else needle in content


@pytest.mark.django_db
def test_anonymous_post_does_not_create_review_on_product(client, product):
    url = reverse("products:product_detail", kwargs={"pk": product.id})
    resp = client.post(url, {"rating": 5, "comment": "Nice!"})
    assert resp.status_code in (200, 302)  # no crash/redirect to login is fine
    assert Review.objects.count() == 0


@pytest.mark.django_db
def test_user_create_product_review_success_message_and_display(client, user, product):
    client.login(username="alice", password="pw")
    url = reverse("products:product_detail", kwargs={"pk": product.id})

    resp = client.post(url, {"rating": 4, "comment": "Solid value"}, follow=True)
    assert resp.status_code == 200
    assert Review.objects.filter(product=product, user=user, rating=4).exists()

    # success message rendered
    assert get(resp.content, "Your review has been submitted.")
    # review shows on page
    assert get(resp.content, "Solid value")
    assert get(resp.content, "Rating: 4/5")


@pytest.mark.django_db
def test_user_create_bundle_review(client, user, bundle):
    client.login(username="alice", password="pw")
    url = reverse("products:bundle_detail", kwargs={"bundle_id": bundle.id})
    resp = client.post(url, {"rating": 5, "comment": "Great kit"}, follow=True)
    assert resp.status_code == 200
    assert Review.objects.filter(bundle=bundle, user=user, rating=5).exists()
    assert get(resp.content, "Your review has been submitted.")
    assert get(resp.content, "Great kit")


@pytest.mark.django_db
def test_missing_rating_shows_inline_error_no_redirect(client, user, product, settings):
    client.login(username="alice", password="pw")
    url = reverse("products:product_detail", kwargs={"pk": product.id})

    resp = client.post(url, {"comment": "Forgot stars"}, follow=False)
    # stays on page with errors (no redirect)
    assert resp.status_code == 200
    # Either custom message or Django default—accept either to avoid fragility
    assert any(get(resp.content, msg) for msg in [
        "Please select a star rating (1–5) before submitting.",
        "This field is required."
    ])
    assert Review.objects.count() == 0


@pytest.mark.django_db
def test_second_review_is_not_created_and_user_sees_already_message(client, user, product):
    client.login(username="alice", password="pw")
    url = reverse("products:product_detail", kwargs={"pk": product.id})

    # first review
    client.post(url, {"rating": 3, "comment": "ok"}, follow=True)
    assert Review.objects.count() == 1

    # try a second POST (view should block silently and show info in template)
    resp = client.post(url, {"rating": 5, "comment": "again"}, follow=True)
    assert resp.status_code == 200
    assert Review.objects.count() == 1
    assert get(resp.content, "You have already submitted a review.")


@pytest.mark.django_db
def test_non_staff_cannot_update_or_delete_review(client, user, product):
    r = Review.objects.create(user=user, product=product, rating=2, comment="meh")
    client.login(username="alice", password="pw")

    edit_url = reverse("products:review_update", kwargs={"review_id": r.id})
    del_url = reverse("products:review_delete", kwargs={"review_id": r.id})

    resp_u = client.post(edit_url, {"rating": 5, "comment": "hacked"})
    resp_d = client.post(del_url)

    # staff_member_required redirects to admin login
    assert resp_u.status_code == 302 and "/admin/login" in resp_u.headers.get("Location", "")
    assert resp_d.status_code == 302 and "/admin/login" in resp_d.headers.get("Location", "")

    r.refresh_from_db()
    assert r.rating == 2


@pytest.mark.django_db
def test_staff_can_update_review_and_redirects_back(client, staff, user, product):
    r = Review.objects.create(user=user, product=product, rating=1, comment="bad")
    client.login(username="admin", password="pw")
    edit_url = reverse("products:review_update", kwargs={"review_id": r.id})

    resp = client.post(edit_url, {"rating": 5, "comment": "Edited"}, follow=False)
    # redirects back to product detail (with optional #reviews in Location)
    assert resp.status_code == 302
    loc = resp.headers.get("Location", "")
    assert reverse("products:product_detail", kwargs={"pk": product.id}) in loc

    r.refresh_from_db()
    assert r.rating == 5
    assert r.comment == "Edited"


@pytest.mark.django_db
def test_staff_can_delete_review_and_redirects_back(client, staff, user, product):
    r = Review.objects.create(user=user, product=product, rating=4, comment="to delete")
    client.login(username="admin", password="pw")
    del_url = reverse("products:review_delete", kwargs={"review_id": r.id})

    resp = client.post(del_url, follow=False)
    assert resp.status_code == 302
    loc = resp.headers.get("Location", "")
    assert reverse("products:product_detail", kwargs={"pk": product.id}) in loc
    assert not Review.objects.filter(pk=r.id).exists()


@pytest.mark.django_db
def test_admin_controls_visible_only_for_staff(client, product, user, staff):
    # Seed one review to render controls next to it
    r = Review.objects.create(user=user, product=product, rating=3, comment="seed")
    url = reverse("products:product_detail", kwargs={"pk": product.id})

    # as normal user -> no Edit/Delete buttons
    client.login(username="alice", password="pw")
    resp = client.get(url)
    assert resp.status_code == 200
    # Should not show admin-only controls
    assert not any(get(resp.content, frag) for frag in [f"reviews/{r.id}/edit", f"reviews/{r.id}/delete"])

    client.logout()
    client.login(username="admin", password="pw")
    resp2 = client.get(url)
    assert resp2.status_code == 200
    assert all(get(resp2.content, frag) for frag in [f"reviews/{r.id}/edit", f"reviews/{r.id}/delete"])
