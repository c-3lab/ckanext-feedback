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
    const runExecute = function() {
      grecaptcha.ready(function() {
        let execPromise;
        try {
          if (typeof feedbackRecaptchaPublickey === 'string' && feedbackRecaptchaPublickey.length > 0) {
            execPromise = grecaptcha.execute(feedbackRecaptchaPublickey, {action: action});
          } else {
            execPromise = grecaptcha.execute({action: action});
          }
        } catch (e) {
          execPromise = grecaptcha.execute({action: action});
        }

        execPromise.then(function(token) {
          const tokenInput = document.createElement('input');
          tokenInput.type = 'hidden';
          tokenInput.name = 'g-recaptcha-response';
          tokenInput.value = token;
          formElement.appendChild(tokenInput);
          const actionInput = document.createElement('input');
          actionInput.type = 'hidden';
          actionInput.name = 'action';
          actionInput.value = action;
          formElement.appendChild(actionInput);
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

// Defensive: capture submit globally in case onsubmit was not attached
document.addEventListener('submit', function(event) {
  const target = event.target;
  if (!(target && target.tagName === 'FORM')) return;

  const configured = (function() {
    if (window.feedbackRecaptchaForms && Array.isArray(window.feedbackRecaptchaForms)) {
      return window.feedbackRecaptchaForms.some(cfg => cfg.name === target.getAttribute('name'));
    }
    const tn = (typeof window.feedbackRecaptchaTargetForm === 'string' && window.feedbackRecaptchaTargetForm)
      || (typeof feedbackRecaptchaTargetForm === 'string' && feedbackRecaptchaTargetForm)
      || null;
    return tn && target.getAttribute('name') === tn;
  })();

  if (!configured) return;
  if (target.querySelector('input[name="g-recaptcha-response"]')) return; // already has token

  event.preventDefault();

  const action = (function() {
    if (window.feedbackRecaptchaForms && Array.isArray(window.feedbackRecaptchaForms)) {
      const found = window.feedbackRecaptchaForms.find(cfg => cfg.name === target.getAttribute('name'));
      if (found) return found.action;
    }
    const ta = (typeof window.feedbackRecaptchaAction === 'string' && window.feedbackRecaptchaAction)
      || (typeof feedbackRecaptchaAction === 'string' && feedbackRecaptchaAction)
      || 'resource_comment_check';
    return ta;
  })();

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
        const tokenInput = document.createElement('input');
        tokenInput.type = 'hidden';
        tokenInput.name = 'g-recaptcha-response';
        tokenInput.value = token;
        target.appendChild(tokenInput);
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = action;
        target.appendChild(actionInput);
        target.submit();
      });
    });
  };

  if (window.grecaptcha && typeof grecaptcha.execute === 'function') {
    runExecute();
  } else {
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
      }
    }, intervalMs);
  }
}, true);
