function confirmDelete() {
    return confirm('Are you sure you want to delete this sow? This action cannot be undone.');
}

function fetchTotals() {
    $.ajax({
        url: '/api/expenses/totals',
        type: 'GET',
        success: function(data) {
            $('#total-expenses').text(data.total_expenses);
            $('#total-revenue').text(data.total_revenue);
            $('#net-profit').text(data.net_profit);
        },
        error: function(xhr, status, error) {
            console.error('Error fetching totals:', error);
        }
    });
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