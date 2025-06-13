document.addEventListener('DOMContentLoaded', function () {
  // Bundle Card Tooltip
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });

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
});
  // Prevent multiple checkout submissions
 document.querySelectorAll('.prevent-multi-submit').forEach(form => {
    form.addEventListener('submit', e => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn.disabled) {
        e.preventDefault(); // prevent double submission
        return;
      }
      btn.disabled = true;
      btn.innerText = 'Adding...';
    });
  });
