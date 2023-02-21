function filter() {
    // Declare variables
    var waiting, approval, table, tr, count;
    waiting = document.getElementById("waiting");
    approval = document.getElementById("approval");
    table = document.getElementById("results-table");
    tr = table.getElementsByTagName("tr");
    count = 0;
    
    // Loop through all table rows, and hide those who don't match the search query
    for (i = 0; i < tr.length; i++) {
      td = tr[i].getElementsByTagName("td")[4]
      if (td) {
        value = td.textContent || td.innerText;
        if(waiting.checked || approval.checked) {
          if (value == '承認待ち' && waiting.checked) {
            tr[i].style.display = "";
            count = count + 1;
          } else if (value == '承認済' && approval.checked) {
            tr[i].style.display = "";
            count = count + 1;
          } else {
            tr[i].style.display = "none";
          }
        } else {
          tr[i].style.display = "";
          count = count + 1;
        } 
      }
    }
    document.getElementById("data-count").innerText = '検索結果：' + count + '件';
  }
