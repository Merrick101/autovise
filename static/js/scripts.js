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
  // Only run on pages that have the inline checkout component
  const root = document.getElementById("inline-checkout");
  const form = document.getElementById("payment-form");
  const container = document.getElementById("payment-element");
  if (!root || !form || !container) return;

  // Read scoped config from data-* attributes
  const pk = root.dataset.pk;
  const createUrl = root.dataset.createUrl;
  const successUrl = root.dataset.successUrl;

  if (!pk || !createUrl || !successUrl) {
    console.error("[Checkout] Missing data-* config");
    return;
  }
  if (typeof Stripe !== "function") {
    console.error("[Checkout] Stripe.js not loaded");
    return;
  }

  const stripe = Stripe(pk);

  // Create PaymentIntent and get clientSecret
  const resp = await fetch(createUrl, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken") || "",
      "Accept": "application/json",
    },
  });
  if (!resp.ok) {
    const msg = await resp.text();
    document.getElementById("error-message")?.insertAdjacentText(
      "beforeend",
      msg || "Error creating payment"
    );
    return;
  }

  const { clientSecret } = await resp.json();
  if (!clientSecret) {
    document.getElementById("error-message")?.insertAdjacentText(
      "beforeend",
      "Missing client secret"
    );
    return;
  }

  // Mount Payment Element
  const elements = stripe.elements({ clientSecret });
  const paymentElement = elements.create("payment");
  paymentElement.mount("#payment-element");

  // Submit
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: successUrl },
    });

    if (error) {
      document.getElementById("error-message").textContent =
        error.message || "Payment failed";
      if (submitBtn) submitBtn.disabled = false;
    }
  });
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
