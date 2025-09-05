document.addEventListener('DOMContentLoaded', function () {
  // Bundle Card Tooltip
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));

  // Cart Spinner
  const form = document.querySelector('form[action*="checkout"]');
  const button = document.getElementById('checkout-btn');
  const spinner = document.getElementById('checkout-spinner');
  if (form && button && spinner) {
    form.addEventListener('submit', function () {
      button.disabled = true;
      spinner.classList.remove('d-none');
    });
  }

  // Prevent multiple “Add to Cart” submissions
  document.querySelectorAll('.prevent-multi-submit').forEach(formEl => {
    formEl.addEventListener('submit', e => {
      const btn = formEl.querySelector('button[type="submit"]');
      if (btn.disabled) {
        e.preventDefault();
        return;
      }
      btn.disabled = true;
      btn.innerText = 'Adding…';
    });
  });
});

// Stripe Payment Element
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

async function initInlineCheckout() {
  const root = document.getElementById("inline-checkout");
  const form = document.getElementById("payment-form");
  const container = document.getElementById("payment-element");
  const errBox = document.getElementById("error-message");
  if (!root || !form || !container) return;

  const pk = root.dataset.pk;
  const createUrl = root.dataset.createUrl;
  const updateUrl = root.dataset.updateUrl;
  const successUrl = root.dataset.successUrl;

  const fail = (msg) => {
    if (errBox) errBox.textContent = msg;
    console.error("[Checkout]", msg);
  };

  if (!pk || !createUrl || !successUrl) return fail("Missing data-* config");
  if (typeof Stripe !== "function") return fail("Stripe.js not loaded");

  const stripe = Stripe(pk);

  try {
    // Build JSON payload (guest email optional)
    const guestEmailInput = form.querySelector("#guest_email");
    const payload = {};
    if (guestEmailInput && guestEmailInput.value.trim()) {
      payload.guest_email = guestEmailInput.value.trim();
    }

    // Create PaymentIntent
    const resp = await fetch(createUrl, {
      method: "POST",
      credentials: "same-origin", // ensure cookies (CSRF/session) are sent
      headers: {
        "X-CSRFToken": getCookie("csrftoken") || "",
        "Accept": "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const text = await resp.text();
      return fail(text || "Error creating payment intent");
    }

    // Backend returns { client_secret, payment_intent_id, order_id }
    const data = await resp.json();
    const clientSecret = data.client_secret || data.clientSecret; // tolerate old shape
    const paymentIntentId = data.payment_intent_id || data.paymentIntentId;
    if (!clientSecret) return fail("Missing client secret");

    // Mount Payment Element
    const elements = stripe.elements({ clientSecret });
    const paymentElement = elements.create("payment");
    paymentElement.mount("#payment-element");

    // Enable submit after mount
    const submitBtn = form.querySelector('button[type="submit"]');
    const spinner = document.getElementById("spinner");
    if (submitBtn) submitBtn.disabled = false;

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (submitBtn) submitBtn.disabled = true;
      if (spinner) spinner.classList.remove("d-none");

      try {
        const latestEmail = guestEmailInput && guestEmailInput.value.trim();
        if (latestEmail && paymentIntentId && updateUrl) {
          console.debug("[Checkout] Updating PI with guest email…", latestEmail);
          await fetch(updateUrl, {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "X-CSRFToken": getCookie("csrftoken") || "",
              "Accept": "application/json",
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ pi_id: paymentIntentId, guest_email: latestEmail }),
          });
        }
      } catch (e) {
        console.warn("[Checkout] update-intent failed:", e);
      }

      const result = await stripe.confirmPayment({
        elements,
        redirect: "if_required", // Stripe handles 3DS inline if needed
      });

      if (result.error) {
        fail(result.error.message || "Payment failed");
        if (submitBtn) submitBtn.disabled = false;
        if (spinner) spinner.classList.add("d-none");
        return;
      }

      const pi = result.paymentIntent;
      if (pi && pi.status === "succeeded") {
        // JS redirect to success page with the PI id
        window.location.href = `${successUrl}?pi=${encodeURIComponent(pi.id)}`;
        return;
      }

      // PI requires additional processing on Stripe’s side (rare with test cards)
      fail("Payment is processing. You’ll be redirected once it completes.");
    });
  } catch (e) {
    fail(e?.message || "Unexpected error");
  }
}

document.addEventListener("DOMContentLoaded", initInlineCheckout);

// Filter functionality remains in global scope
function updateFilterParam(key, value) {
  const params = new URLSearchParams(window.location.search);
  if (value) {
    params.set(key, value);
  } else {
    params.delete(key);
  }
  params.delete('page');
  window.location.search = params;
}
