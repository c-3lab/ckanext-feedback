var content_form = document.getElementById(feedback_recaptcha_target_form);
content_form.onsubmit = function(event) {
  event.preventDefault();
  grecaptcha.ready(function() {
    grecaptcha.execute(feedback_recaptcha_publickey, {action: feedback_recaptcha_action}).then(function(token) {
      var token_input = document.createElement('input');
      token_input.type = 'hidden';
      token_input.name = 'g-recaptcha-response';
      token_input.value = token;
      content_form.appendChild(token_input);
      var action_input = document.createElement('input');
      action_input.type = 'hidden';
      action_input.name = 'action';
      action_input.value = feedback_recaptcha_action;
      content_form.appendChild(action_input);
      content_form.submit();
    });
  });
}
