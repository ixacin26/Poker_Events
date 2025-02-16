 // Script to handle the "Check All" checkbox functionality
 document.getElementById('check_all').addEventListener('click', function () {
  const checkboxes = document.querySelectorAll('input[name="players"]')
  checkboxes.forEach((checkbox) => (checkbox.checked = this.checked));
});