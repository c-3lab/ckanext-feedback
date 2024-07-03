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

  let countRows;
  if (form['tab-menu'].value === "utilization-comments") {
    countRows = document.querySelectorAll('input[name="utilization-comments-checkbox"]:checked').length;
  } else {
    countRows = document.querySelectorAll('input[name="resource-comments-checkbox"]:checked').length;
  }
  if (countRows === 0) {
    alert(ckan.i18n._('Please select at least one checkbox'));
    return;
  }
  let message;
  if (action.includes('approve')) {
    message = ckan.i18n.translate('Is it okay to approve checked %d item(s)?').fetch(countRows);
  } else  {
    message = ckan.i18n.translate('Is it okay to delete checked %d item(s)?').fetch(countRows);
  }
  if (!confirm(message)) {
    return;
  }
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
  const statusCell = row.getElementsByTagName('td')[8];
  const isWaiting = document.getElementById('waiting').checked && statusCell.dataset.waiting;
  const isApproval = document.getElementById('approval').checked && statusCell.dataset.approval;
  const categoryCell = row.getElementsByTagName('td')[6];
  const categories = Array.from(document.querySelectorAll('.category-checkbox'));
  const isMatchedCategory = categories.filter(element => element.checked)
                                      .some(element => element.getAttribute('name') === categoryCell.dataset.category);
  return (isWaiting || isApproval) && (isMatchedCategory || !categoryCell.dataset.category);
}
