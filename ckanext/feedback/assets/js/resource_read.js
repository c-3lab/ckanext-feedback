async function like_toggle() {
  const resourceId = document.getElementById('resource-id').value;
  const likeButtons = document.querySelectorAll('.like-button');
  const likeIcon = document.getElementById('like-icon');
  let likeCount = parseInt(document.getElementById('like-count').textContent);
  let likeStatus = '';

  if (likeIcon.classList.toggle('liked')) {
    likeStatus = true;
    likeCount++;
  } else {
    likeStatus = false;
    likeCount--;
  }

  likeButtons.forEach((button) => {
    const buttonIcon = button.querySelector('.like-icon');
    const likeCountElement = button.querySelector('.like-count');

    if (likeStatus) {
      buttonIcon.classList.add('liked');
    } else {
      buttonIcon.classList.remove('liked');
    }

    likeCountElement.textContent = likeCount;
  });

  await fetch(`${resourceId}/like_toggle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      likeStatus: likeStatus,
    }),
  });
}
document.querySelectorAll('.download-modal-show').forEach((button) => {
  button.addEventListener('click', function () {
    $('#download-modal').modal('show');
  });
});

document.querySelectorAll('.like-button').forEach((button) => {
  button.addEventListener('click', like_toggle);
});
