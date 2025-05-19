function confirmDelete() {
    return confirm('Are you sure you want to delete this sow? This action cannot be undone.');
}

function fetchTotals() {
    fetch('/expense_totals')
        .then(response => response.json())
        .then(data => {
            document.getElementById('totalExpense').innerText = data.total_expenses;
        })
        .catch(error => console.error('Error fetching totals:', error));
}

// Fetch totals on page load
document.addEventListener('DOMContentLoaded', fetchTotals);

// Refresh every 10 seconds
setInterval(fetchTotals, 10000);



document.querySelector('.form-fields').addEventListener('submit', function(event) {
  const amountInput = document.querySelector('input[name="amount"]');
  let value = amountInput.value.trim().toLowerCase();

  // Remove currency symbols and letters like "k", "$"
  value = value.replace(/[^0-9.,]/g, '');

  // Count commas and dots
  const commaCount = (value.match(/,/g) || []).length;
  const dotCount = (value.match(/\./g) || []).length;

  // Case: comma as thousand separator, dot as decimal
  if (commaCount >= 1 && dotCount <= 1) {
    value = value.replace(/,/g, ''); // remove all commas
  }
  // Case: comma as decimal, dot as thousand separator (unlikely in your region)
  else if (commaCount === 1 && dotCount > 1) {
    value = value.replace(/\./g, '');
    value = value.replace(',', '.');
  }
  // Case: only comma used, assume it's decimal
  else if (commaCount === 1 && dotCount === 0) {
    value = value.replace(',', '.');
  }
  // Otherwise: remove all thousand separators (commas or dots)
  else {
    value = value.replace(/[,\.](?=\d{3}(?:[^\d]|$))/g, '');
  }

  const amount = parseFloat(value);
  if (isNaN(amount)) {
    alert("Invalid amount entered.");
    event.preventDefault();
    return;
  }

  amountInput.value = amount.toFixed(2); // optional: keep 2 decimal places
});
