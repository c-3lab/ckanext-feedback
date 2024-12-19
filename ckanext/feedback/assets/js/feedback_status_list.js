const targetCheckboxAll = document.getElementById('target-checkbox-all');
targetCheckboxAll.addEventListener('change', changeAllCheckbox);

function changeAllCheckbox(e){
    let rows;
    rows = document.querySelectorAll('.target');

    rows.forEach(row => {
        const targetCheckbox = row.querySelector('input[type="checkbox"]');
        targetCheckbox.checked = e.target.checked;
    })
}

function runBulkAction(action) {
    const form = document.getElementById('comments-form');
    form.setAttribute("action", action);

    const resourceCommentRows = document.querySelectorAll('input[name="resource-comments-checkbox"]:checked').length;
    const utilizationRows = document.querySelectorAll('input[name="utilization-checkbox"]:checked').length;
    const utilizationCommentRows = document.querySelectorAll('input[name="utilization-comments-checkbox"]:checked').length;
    const countRows = resourceCommentRows + utilizationRows + utilizationCommentRows;

    if (countRows === 0) {
        alert(ckan.i18n._('Please select at least one checkbox'));
        return;
    }

    let bulkButtonList = document.getElementsByClassName('bulk-button');

    let message;
    if (action.includes('approve')) {
        bulkButtonList[0].style.pointerEvents = 'none';
        message = ckan.i18n.translate('Is it okay to approve checked %d item(s)?').fetch(countRows);
    } else  {
        bulkButtonList[1].style.pointerEvents = 'none';
        message = ckan.i18n.translate('Is it okay to delete checked %d item(s)?').fetch(countRows);
    }

    if (!confirm(message)) {
        bulkButtonList[0].style.pointerEvents = '';
        bulkButtonList[1].style.pointerEvents = '';
        return;
    }
    form.submit();
}

function updateSortParameter() {
    const selectElement = document.getElementById('field-order-by');

    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('sort', selectElement.value);

    window.location.href = currentUrl.toString();
}
