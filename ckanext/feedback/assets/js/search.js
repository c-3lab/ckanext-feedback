function refreshTable() {
  // Declare variables
  const isWaiting = document.getElementById('waiting').checked;
  const isApproval = document.getElementById('approval').checked;
  const rows = document.querySelectorAll('#results-table tbody tr')
  let count = 0;

  // Loop through all table rows, and hide those who don't match the search query
  rows.forEach(row => {
    const statusCell = row.getElementsByTagName('td')[7]
    if (statusCell.dataset.waiting && isWaiting) {
      row.style.display = 'table-row';
      ++count
    } else if (statusCell.dataset.approval && isApproval) {
      row.style.display = 'table-row';
      ++count
    } else {
      row.style.display = 'none';
    }
  })
  document.getElementById('utilization-results-count').innerText = count;
}
