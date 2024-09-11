document.addEventListener('DOMContentLoaded', function(){
  document.getElementById('waiting').disabled = false;
  document.getElementById('approval').disabled = false;
});

function refreshTable() {
  // Declare variables
  let isWaiting = document.getElementById('waiting').checked;
  let isApproval = document.getElementById('approval').checked;
  const rows = document.querySelectorAll('#results-table tbody tr')

  // Loop through all table rows, and hide those who don't match the search query
  rows.forEach(row => {
    const statusCell = row.getElementsByTagName('td')[7]
    if (statusCell.dataset.waiting && isWaiting) {
      row.style.display = 'table-row';
    } else if (statusCell.dataset.approval && isApproval) {
      row.style.display = 'table-row';
    } else {
      row.style.display = 'none';
    }
  })

  const pageLinks = document.querySelectorAll('.pagination .page-link');
  pageLinks.forEach((pageLink) => {
    let hrefValue = pageLink.getAttribute('href');

    if(isWaiting) {
      hrefValue = updateParam(hrefValue, 'waiting=off&', 'waiting=on&');
    } else {
      hrefValue = updateParam(hrefValue, 'waiting=on&', 'waiting=off&');
    }

    if(isApproval) {
      hrefValue = updateParam(hrefValue, 'approval=off&', 'approval=on&');
    } else {
      hrefValue = updateParam(hrefValue, 'approval=on&', 'approval=off&');
    }

    pageLink.setAttribute('href', hrefValue);
  });
}

function updateParam(href, deleteParam, additionalParam) {
  if (href.includes(deleteParam)) {
    href = href.replace(deleteParam, '');
  }

  if (!href.includes(additionalParam)) {
    href = href.replace('page=', `${additionalParam}page=`);
  }

  return href
}