
document.addEventListener('DOMContentLoaded', function () {
  const asopCheckbox = document.getElementById('asop')
  const hostPlayerGroup = document.getElementById('host_player_group')
  const hostPlayerSelect = document.getElementById('host_player')

  asopCheckbox.addEventListener('change', function () {
    if (asopCheckbox.checked) {
      // Hide and clear Host Player dropdown if ASOP is checked
      hostPlayerSelect.value = '' // Clear selection
      hostPlayerSelect.required = false // Make it non-mandatory
      hostPlayerGroup.style.display = 'none' // Hide the dropdown
    } else {
      // Show and make Host Player dropdown mandatory if ASOP is unchecked
      hostPlayerSelect.required = true
      hostPlayerGroup.style.display = 'block'
    }
  })
})