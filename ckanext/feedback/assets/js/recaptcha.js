const contentForm = document.getElementById(feedbackRecaptchaTargetForm);
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
