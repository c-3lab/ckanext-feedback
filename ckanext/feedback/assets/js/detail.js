function check_description() {
  error_message = document.getElementById('description-error');
  description = document.getElementById('description').value;

  if (!description) {
    error_message.style.display = '';
    return false;
  }
  return true;
}