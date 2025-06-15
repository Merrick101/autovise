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

// Filter functionality remains in global scope so your inline onchange can see it:
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
