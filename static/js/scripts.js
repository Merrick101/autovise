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

  // Review form: scroll to reviews section if errors
  (function scrollToReviewsIfErrors() {
    const reviews = document.getElementById('reviews');
    if (!reviews) return;

    // Look for typical Django error markers inside the reviews section
    const hasErrors = reviews.querySelector('.text-danger, .invalid-feedback, .is-invalid');
    if (!hasErrors) return;

    // Scroll the section into view (stays on page; no jump to top)
    reviews.scrollIntoView({ behavior: 'auto', block: 'start' });

    // Brief highlight so eyes land there
    reviews.classList.add('review-error-highlight');
    setTimeout(() => reviews.classList.remove('review-error-highlight'), 1500);
  })();

  document.querySelectorAll('form.review-form').forEach(formEl => {
    formEl.addEventListener('submit', e => {
      const hasRating = !!formEl.querySelector('input[name="rating"]:checked');
      if (!hasRating) {
        e.preventDefault();
        const err = formEl.querySelector('[data-rating-error]');
        if (err) {
          err.textContent = 'Please select a star rating (1–5) before submitting.';
          err.classList.remove('d-none');
        }
        const stars = formEl.querySelector('.rating-stars');
        if (stars) stars.classList.add('border','border-danger','rounded','px-2');
      }
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
    if (errBox) errBox.textContent = msg || "";
    console.error("[Checkout]", msg);
  };

  if (!pk || !createUrl || !successUrl) return fail("Missing data-* config");
  if (typeof Stripe !== "function") return fail("Stripe.js not loaded");

  const stripe = Stripe(pk);

  let creatingPI = false;

  // Submit gating & state
  const submitBtn = form.querySelector("#submit");
  const spinner = document.getElementById("spinner");
  const guestEmailInput = form.querySelector("#guest_email");
  let elementReady = false;   // flips true after Payment Element mounts
  let mounted = false;        // prevent multiple mounts
  let paymentIntentId = null; // captured from backend
  let elements = null;        // outer variable used by confirmPayment

  function updateSubmitState() {
    const ok = form.checkValidity() && elementReady;
    if (submitBtn) submitBtn.disabled = !ok;
  }

  form.addEventListener("input", updateSubmitState);
  form.addEventListener("change", updateSubmitState);

  // Build payload from current form values
  function buildPayload() {
    const p = {};

    if (guestEmailInput && guestEmailInput.value.trim()) {
      p.guest_email = guestEmailInput.value.trim();
    }

    const saveBox = form.querySelector("#save_shipping");
    if (saveBox && saveBox.checked) p.save_shipping = "1";

    [
      "shipping_name",
      "shipping_line1",
      "shipping_line2",
      "shipping_city",
      "shipping_postcode",
      "shipping_country",
      "shipping_phone",
    ].forEach((name) => {
      const el = form.querySelector(`#${name}`);
      if (!el) return;
      const val = el.value.trim();
      if (!val) return;
      p[name] = name === "shipping_country" ? val.toUpperCase() : val;
    });

    return p;
  }

  // Create PI + mount Stripe Element once address is valid
  async function maybeCreateAndMount() {
    if (mounted || creatingPI) return;

    if (!form.checkValidity()) { 
      updateSubmitState(); 
      return; 
    }

    creatingPI = true;                 // <— lock
    try {
      const resp = await fetch(createUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": getCookie("csrftoken") || "",
          "Accept": "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(buildPayload()),
      });

      if (!resp.ok) {
        const text = await resp.text();
        fail(text || "Error creating payment intent");
        return;
      }

      const data = await resp.json();
      const clientSecret = data.client_secret || data.clientSecret;
      paymentIntentId = data.payment_intent_id || data.paymentIntentId || null;
      if (!clientSecret) { fail("Missing client secret"); return; }

      const latestEmail = (guestEmailInput?.value || "").trim() || undefined;

      elements = stripe.elements({
        clientSecret,
        wallets: { link: "never" },
        fields: {
          billingDetails: { address: "never", name: "never", email: "never", phone: "never" },
        },
        defaultValues: { billingDetails: { email: latestEmail } },
      });

      const paymentElement = elements.create("payment");
      paymentElement.mount("#payment-element");

      elementReady = true;
      mounted = true;
      updateSubmitState();

      form.removeEventListener("input", maybeCreateAndMount);
      form.removeEventListener("change", maybeCreateAndMount);

      // Prevent double confirmation with a tiny lock
      let confirming = false;

      // Submit handler (added only once, after mount)
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (confirming) return;       // <— guard
        confirming = true;

        if (!form.checkValidity()) {
          form.reportValidity();
          updateSubmitState();
          confirming = false;
          return;
        }

        if (submitBtn) submitBtn.disabled = true;
        if (spinner) spinner.classList.remove("d-none");

        try {
          const latestEmailNow = guestEmailInput && guestEmailInput.value.trim();
          if (updateUrl && paymentIntentId && latestEmailNow) {
            await fetch(updateUrl, {
              method: "POST",
              credentials: "same-origin",
              headers: {
                "X-CSRFToken": getCookie("csrftoken") || "",
                "Accept": "application/json",
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                pi_id: paymentIntentId,
                guest_email: latestEmailNow,
              }),
            });
          }
        } catch (e) {
          console.warn("[Checkout] update-intent failed:", e);
        }

        const result = await stripe.confirmPayment({ elements, redirect: "if_required" });

        if (result.error) {
          fail(result.error.message || "Payment failed");
          if (submitBtn) submitBtn.disabled = false;
          if (spinner) spinner.classList.add("d-none");
          confirming = false;          // allow retry
          return;
        }

        const pi = result.paymentIntent;
        if (pi && pi.status === "succeeded") {
          window.location.href = `${successUrl}?pi=${encodeURIComponent(pi.id)}`;
          return;
        }

        fail("Payment is processing. You’ll be redirected once it completes.");
        confirming = false;
      });
    } catch (err) {
      fail(err?.message || "Unexpected error");
    } finally {
      creatingPI = false;              // <— release lock
    }
  }

  // Initial state (handles autofill), and re-attempt on any input/change
  updateSubmitState();
  maybeCreateAndMount();
  form.addEventListener("input", maybeCreateAndMount);
  form.addEventListener("change", maybeCreateAndMount);
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
