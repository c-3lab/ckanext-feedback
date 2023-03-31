const utilizationCheckboxAll = document.getElementById('utilization-comments-checkbox-all');
utilizationCheckboxAll.addEventListener('change', changeAllChekbox);

const resourceCheckboxAll = document.getElementById('resource-comments-checkbox-all');
resourceCheckboxAll.addEventListener('change', changeAllChekbox);


function changeAllChekbox(e) {
  let rows;
  if (e.target.id === 'utilization-comments-checkbox-all') {
    rows = document.querySelectorAll('#utilization-comments-table tbody tr');
  } else if (e.target.id === 'resource-comments-checkbox-all') {
    rows = document.querySelectorAll('#resource-comments-table tbody tr');
  }
  Array.from(rows).filter(isVisible).forEach(row => {
    row.querySelector('input[type="checkbox"]').checked = e.target.checked;
  });
}


function runBulkAction(action) {
  const form = document.getElementById('comments-form');
  form.setAttribute("action", action);
  form.submit();
}


function refreshTable() {
  const tabs = document.querySelectorAll('input[name="tab-menu"]');
  const activeTabName = Array.from(tabs).find(tab => tab.checked).value;
  const rows = document.querySelectorAll(`#${activeTabName}-table tbody tr`);
  let count = 0;

  rows.forEach(row => {
    if (isVisible(row)) {
      row.style.display = 'table-row';
      ++count;
    } else {
      row.style.display = 'none';
      row.querySelector('input[type="checkbox"]').checked = false;
    }
  });
  document.getElementById(`${activeTabName}-results-count`).innerText = count;

  const visibleRows = Array.from(document.querySelectorAll(`#${activeTabName}-table tbody tr`)).filter(isVisible);
  const bulkCheckbox = document.getElementById(`${activeTabName}-checkbox-all`);
  bulkCheckbox.checked = visibleRows.every(row => row.querySelector('input[type="checkbox"]').checked) && visibleRows.length;
}


function isVisible(row){
  const statusCell = row.getElementsByTagName('td')[7];
  const isWaiting = document.getElementById('waiting').checked && statusCell.dataset.waiting;
  const isApproval = document.getElementById('approval').checked && statusCell.dataset.approval;
  const categoryCell = row.getElementsByTagName('td')[5];
  const categories = Array.from(document.querySelectorAll('.category-checkbox'));
  const isMatchedCategory = categories.filter(element => element.checked)
                                      .some(element => element.getAttribute('name') === categoryCell.dataset.category);
  return (isWaiting || isApproval) && (isMatchedCategory || !categoryCell.dataset.category);
}
