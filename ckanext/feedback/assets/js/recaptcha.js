window.addEventListener('pageshow', function(event) {
  if (event.persisted || (performance.getEntriesByType("navigation")[0]?.type === "back_forward")) {
    const existingTokenInput = document.querySelector('input[name="g-recaptcha-response"]');
    if (existingTokenInput) existingTokenInput.remove();
  }
});

const contentForms = document.getElementsByName(feedbackRecaptchaTargetForm);
contentForms.forEach(contentForm => {
  contentForm.onsubmit = function(event) {
    event.preventDefault();
    grecaptcha.ready(function() {
      grecaptcha.execute(feedbackRecaptchaPublickey, {action: feedbackRecaptchaAction}).then(function(token) {
        const tokenInput = document.createElement('input');
        tokenInput.type = 'hidden';
        tokenInput.name = 'g-recaptcha-response';
        tokenInput.value = token;
        contentForm.appendChild(tokenInput);
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = feedbackRecaptchaAction;
        contentForm.appendChild(actionInput);
        contentForm.submit();
      });
    });
  }
});
