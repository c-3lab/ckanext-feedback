const utilizationCheckboxAll = document.getElementById('utilization-comments-checkbox-all');
utilizationCheckboxAll.addEventListener('change', changeAllChekbox);

const resourceCheckboxAll = document.getElementById('resource-comments-checkbox-all');
resourceCheckboxAll.addEventListener('change', changeAllChekbox);


function truncate(str, length) {
  if (str.length > length) {
    return str.substring(0, length) + '...';
  }
  return str;
}

function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}/${month}/${day}`;
}

async function leadMoreData(url, tbody, rowCount) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      tbodyId: tbody.id,
      rowCount: rowCount,
    }),
  });

  const responseData = await response.json();
  updateHTML(responseData, tbody, tbody.id, rowCount);
}

function updateHTML(responseData, tbody, tbodyId, rowCount) {
  if (tbodyId === 'resource-comments-table-body') {
    responseData.forEach(row => {
      const date = new Date(row.created.created);
      let htmlContent = `
        <td class="small-column">
          <input type="checkbox" id="resource-comments-checkbox-${ row.check_box.id }" name="resource-comments-checkbox" value="${ row.check_box.id }" />
        </td>
        <td class="left-aligned-text">
          <a href="${ row.comments_body.url }">${ truncate(row.comments_body.content, 20) }</a>
        </td>
      `;
      if ( row.rating.is_enabled_rating ) {
        htmlContent += `
          <td>${ row.rating.rating ? row.rating.rating : '' }</td>
        `;
      }
      htmlContent += `
        <td>
          ${ truncate(row.organization.organization_name, 20) }
        </td>
        <td>
          <a href="${ row.dataset.url }${ row.dataset.package_name }">${ truncate(row.dataset.package_title, 20) }</a>
        </td>
        <td>
          <a href="${ row.resource.url }${ row.resource.package_name }/resource/${ row.resource.id }">${ row.resource.name }</a>
        </td>
        <td data-category="${ row.category.category }">${ row.category.category }</td>
        <td>${ formatDate(date) }</td>
      `;
      if (row.status.approval) {
        htmlContent += `<td data-approval="true">approval</td>`
      } else {
        htmlContent += `<td data-waiting="true">Waiting</td>`
      }

      const toggleSeparator = document.getElementById('resource-comments-toggle-separator');
      toggleSeparator.insertAdjacentHTML('beforebegin', htmlContent);

      const resultsCount = document.getElementById('resource-comments-results-count');
      const rowsCount = tbody.querySelectorAll('tr');
      const count = rowsCount.length;
      resultsCount.textContent = count-2;

      maxResourceComments = document.getElementById('resource-comments-max-results-count');
      toggleShow = document.getElementById('resource-comments-toggle-show');
      
      if (row.limit + rowCount >= maxResourceComments.textContent) {
        toggleSeparator.style.display = 'none';
        toggleShow.style.display = 'none';
      }
    });
  } else {
    responseData.forEach(row => {
      const date = new Date(row.created.created);
      let htmlContent = `
        <td class="small-column">
          <input type="checkbox" id="utilization-comments-checkbox-${ row.check_box.id }" name="utilization-comments-checkbox" value="${ row.check_box.id }"/>
        </td>
        <td class="left-aligned-text">
          <a href="${ row.comments_body.url }">${ truncate(row.comments_body.content, 20) }</a>
        </td>
        <td>
          <a href="${ row.utilization_title.url }">${ truncate(row.utilization_title.title, 20) }</a>
        </td>
        <td>
          ${ truncate(row.organization.organization_name, 20) }
        </td>
        <td>
          <a href="${ row.dataset.url }${ row.dataset.package_name }">${ truncate(row.dataset.package_title, 20) }</a>
        </td>
        <td>
          <a href="${ row.resource.url }${ row.resource.package_name }/resource/${ row.resource.id }">${ truncate(row.resource.name, 20) }</a>
        </td>
        <td data-category="${ row.category.category }">${ row.category.category }</td>
        <td>${ formatDate(date) }</td>
      `;
      if (row.status.approval) {
        htmlContent += `<td data-approval="true">approval</td>`
      } else {
        htmlContent += `<td data-waiting="true">Waiting</td>`
      }

      const toggleSeparator = document.getElementById('utilization-comments-toggle-separator');
      toggleSeparator.insertAdjacentHTML('beforebegin', htmlContent);

      const resultsCount = document.getElementById('utilization-comments-results-count');
      const rowsCount = tbody.querySelectorAll('tr');
      const count = rowsCount.length;
      resultsCount.textContent = count-2;

      maxUtilizationComments = document.getElementById('utilization-comments-max-results-count');
      toggleShow = document.getElementById('utilization-comments-toggle-show');

      if (row.limit + rowCount >= maxUtilizationComments.textContent) {
        toggleSeparator.style.display = 'none';
        toggleShow.style.display = 'none';
      }
    });
  }
}

function leadMoreResourceData() {
  const tbody = document.getElementById('resource-comments-table-body');
  const rows = tbody.querySelectorAll('tr');
  const rowCount = rows.length;
  leadMoreData("/management/get_lead_more_data_comments", tbody, (rowCount-2));
}

function leadMoreUtilizationData() {
  const tbody = document.getElementById('utilization-comments-table-body');
  const rows = tbody.querySelectorAll('tr');
  const rowCount = rows.length;
  leadMoreData("/management/get_lead_more_data_comments", tbody, (rowCount-2));
}


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

  rows.forEach(row => {
    if (isVisible(row)) {
      row.style.display = 'table-row';
    } else {
      row.style.display = 'none';
      row.querySelector('input[type="checkbox"]').checked = false;
    }
  });

  const visibleRows = Array.from(document.querySelectorAll(`#${activeTabName}-table tbody tr`)).filter(isVisible);
  const bulkCheckbox = document.getElementById(`${activeTabName}-checkbox-all`);
  bulkCheckbox.checked = visibleRows.every(row => row.querySelector('input[type="checkbox"]').checked) && visibleRows.length;
}


function isVisible(row){
  var cells = row.getElementsByTagName('td');
  if (cells.length == 1) {
    return false
  }

  const statusCell = row.getElementsByTagName('td')[8];
  const isWaiting = document.getElementById('waiting').checked && statusCell.dataset.waiting;
  const isApproval = document.getElementById('approval').checked && statusCell.dataset.approval;
  const categoryCell = row.getElementsByTagName('td')[6];
  const categories = Array.from(document.querySelectorAll('.category-checkbox'));
  const isMatchedCategory = categories.filter(element => element.checked)
                                      .some(element => element.getAttribute('name') === categoryCell.dataset.category);
  return (isWaiting || isApproval) && (isMatchedCategory || !categoryCell.dataset.category);
}
