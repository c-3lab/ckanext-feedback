window.addEventListener('pageshow', function(event) {
  if (event.persisted || (performance.getEntriesByType("navigation")[0]?.type === "back_forward")) {
    const existingTokenInput = document.querySelector('input[name="g-recaptcha-response"]');
    if (existingTokenInput) existingTokenInput.remove();
  }
});

function attachRecaptchaToForm(formElement, action) {
  if (!formElement) return;
  formElement.onsubmit = function(event) {
    event.preventDefault();
    if (formElement.dataset.recaptchaSubmitting === '1') return; // prevent double-submit
    const runExecute = function() {
      grecaptcha.ready(function() {
        let execPromise;
        try {
          if (typeof feedbackRecaptchaPublickey === 'string' && feedbackRecaptchaPublickey.length > 0) {
            execPromise = grecaptcha.execute(feedbackRecaptchaPublickey, {action: action});
          } else if (typeof window.feedbackRecaptchaPublickey === 'string' && window.feedbackRecaptchaPublickey.length > 0) {
            execPromise = grecaptcha.execute(window.feedbackRecaptchaPublickey, {action: action});
          } else {
            execPromise = grecaptcha.execute({action: action});
          }
        } catch (e) {
          execPromise = grecaptcha.execute({action: action});
        }

        execPromise.then(function(token) {
          // remove old hidden inputs if present
          const oldToken = formElement.querySelector('input[name="g-recaptcha-response"]');
          if (oldToken) oldToken.remove();
          const oldAction = formElement.querySelector('input[name="g-recaptcha-action"]');
          if (oldAction) oldAction.remove();
          const tokenInput = document.createElement('input');
          tokenInput.type = 'hidden';
          tokenInput.name = 'g-recaptcha-response';
          tokenInput.value = token;
          formElement.appendChild(tokenInput);
          const actionInput = document.createElement('input');
          actionInput.type = 'hidden';
          actionInput.name = 'g-recaptcha-action';
          actionInput.value = action;
          formElement.appendChild(actionInput);
          formElement.dataset.recaptchaSubmitting = '1';
          formElement.submit();
        });
      });
    };

    if (window.grecaptcha && typeof grecaptcha.execute === 'function') {
      runExecute();
    } else {
      // Wait for grecaptcha to be ready instead of falling back to normal submit
      let waited = 0;
      const intervalMs = 100;
      const timeoutMs = 3000;
      const timerId = setInterval(function() {
        waited += intervalMs;
        if (window.grecaptcha && typeof grecaptcha.execute === 'function') {
          clearInterval(timerId);
          runExecute();
        } else if (waited >= timeoutMs) {
          clearInterval(timerId);
          console.warn('reCAPTCHA is not ready yet. Please try submitting again in a moment.');
          // Do not submit without token for stability/safety
        }
      }, intervalMs);
    }
  }
}

if (window.feedbackRecaptchaForms && Array.isArray(window.feedbackRecaptchaForms)) {
  window.feedbackRecaptchaForms.forEach(cfg => {
    const forms = document.getElementsByName(cfg.name);
    Array.prototype.forEach.call(forms, form => attachRecaptchaToForm(form, cfg.action));
  });
} else {
  // Support both window.* and plain global variables defined via const in templates
  const targetName =
    (typeof window.feedbackRecaptchaTargetForm === 'string' && window.feedbackRecaptchaTargetForm)
    || (typeof feedbackRecaptchaTargetForm === 'string' && feedbackRecaptchaTargetForm)
    || null;
  const targetAction =
    (typeof window.feedbackRecaptchaAction === 'string' && window.feedbackRecaptchaAction)
    || (typeof feedbackRecaptchaAction === 'string' && feedbackRecaptchaAction)
    || 'resource_comment_check';

  if (targetName) {
    const forms = document.getElementsByName(targetName);
    Array.prototype.forEach.call(forms, form => attachRecaptchaToForm(form, targetAction));
  }
}
