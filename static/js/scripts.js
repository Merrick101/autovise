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
  const successUrl = root.dataset.successUrl;

  const fail = (msg) => {
    if (errBox) errBox.textContent = msg;
    console.error("[Checkout]", msg);
  };

  if (!pk || !createUrl || !successUrl) return fail("Missing data-* config");
  if (typeof Stripe !== "function") return fail("Stripe.js not loaded");

  const stripe = Stripe(pk);

  try {
    // Build POST body (guest email optional)
    const fd = new FormData();
    const guestEmailInput = form.querySelector("#guest_email");
    if (guestEmailInput && guestEmailInput.value) {
      fd.append("guest_email", guestEmailInput.value.trim());
    }

    // Create PaymentIntent
    const resp = await fetch(createUrl, {
      method: "POST",
      credentials: "same-origin", // <- ensure session/CSRF cookies are sent
      headers: {
        "X-CSRFToken": getCookie("csrftoken") || "",
        "Accept": "application/json",
      },
      body: fd,
    });

    if (!resp.ok) {
      const text = await resp.text();
      return fail(text || "Error creating payment intent");
    }

    // Backend returns { client_secret, payment_intent_id, order_id }
    const contentType = resp.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await resp.json() : {};
    const clientSecret = data.client_secret || data.clientSecret; // tolerate old shape

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

      const result = await stripe.confirmPayment({
        elements,
        redirect: "if_required",
      });

      if (result.error) {
        fail(result.error.message || "Payment failed");
        if (submitBtn) submitBtn.disabled = false;
        if (spinner) spinner.classList.add("d-none");
        return;
      }

      const pi = result.paymentIntent;
      if (pi && pi.status === "succeeded") {
        window.location.href = `${successUrl}?pi=${encodeURIComponent(pi.id)}`;
        return;
      }

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
