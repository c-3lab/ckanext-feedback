function checkTitleAndDescriptionExists(button) {
  const title = document.getElementById('title').value;
  const description = document.getElementById('description').value;
  const titleNoneErrorElement = document.getElementById('title-none-error');
  const titleOverErrorElement = document.getElementById('title-over-error');
  const urlOverErrorElement = document.getElementById('url-over-error');
  const descriptionNoneErrorElement = document.getElementById('description-none-error');
  const descriptionOverElement = document.getElementById('description-over-error');
  
  // Reset display settings
  titleNoneErrorElement.style.display = 'none';
  titleOverErrorElement.style.display = 'none';
  urlOverErrorElement.style.display = 'none';
  descriptionNoneErrorElement.style.display = 'none';
  descriptionOverElement.style.display = 'none';
  
  if (!title) {
    titleNoneErrorElement.style.display = '';
    return false;
  }
  if (title.length>50) {
    titleOverErrorElement.style.display = '';
    return false;
  }
  if (url.length != 0 && url.length>2048) {
    urlOverErrorElement.style.display = '';
    return false;
  }
  if (!description) {
    descriptionNoneErrorElement.style.display = '';
    return false;
  }
  if (description.length>2000) {
    descriptionOverElement.style.display = '';
    return false;
  }

  button.style.pointerEvents = "none"
  return true;
}

function confirmDelete() {
  const message = document.getElementById('message').value;
  return confirm(message)
}

//文字数カウント
document.addEventListener('DOMContentLoaded', function() {
  const titleArea = document.getElementById('title');
  const titleCount = document.getElementById('title-count');

  const urlArea = document.getElementById('url');
  const urlCount = document.getElementById('url-count');

  const descriptionArea = document.getElementById('description');
  const descriptionCount = document.getElementById('description-count');

  function updateCharCount(textarea, charCount) {
    const currentLength = textarea.value.length;
    charCount.textContent = currentLength;
  }

  //初期値の文字数カウント
  updateCharCount(titleArea, titleCount);
  updateCharCount(urlArea, urlCount);
  updateCharCount(descriptionArea, descriptionCount);

  //入力時の文字数カウント
  titleArea.addEventListener('input', function() {
    updateCharCount(titleArea, titleCount);
  });

  urlArea.addEventListener('input', function() {
    updateCharCount(urlArea, urlCount);
  });

  descriptionArea.addEventListener('input', function() {
    updateCharCount(descriptionArea, descriptionCount);
  });
});