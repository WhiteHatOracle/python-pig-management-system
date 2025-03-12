let debounceTimer;

function filterInvoices() {
    // Clear the previous debounce timer
    clearTimeout(debounceTimer);

    // Set a new debounce timer
    debounceTimer = setTimeout(function () {
        const searchInput = document.getElementById('searchInput').value.toLowerCase();
        const table = document.getElementById('invoiceTable');
        const rows = table.getElementsByTagName('tr');

        // If search input is empty, just reset highlights and show all rows
        if (searchInput === '') {
            resetHighlights();
            showAllRows(rows);
            return;
        }

        // Reset any previous highlights
        resetHighlights();

        for (let i = 1; i < rows.length; i++) { // Skip the header row (i = 1)
            const cells = rows[i].getElementsByTagName('td');
            let match = false;

            // Check if any cell in the row matches the search input
            for (let j = 0; j < cells.length; j++) {
                if (cells[j]) {
                    const cellText = cells[j].textContent || cells[j].innerText;
                    if (cellText.toLowerCase().indexOf(searchInput) > -1) {
                        match = true;
                        // Highlight the entire row
                        highlightRow(rows[i]);
                    }
                }
            }

            // Show or hide the row based on the match
            if (match) {
                rows[i].style.display = '';
            } else {
                rows[i].style.display = 'none';
            }
        }
    }, 300); // 300ms debounce delay
}

// Function to highlight the entire row
function highlightRow(row) {
    row.style.backgroundColor = '#FFFF99'; // Light yellow highlight for the entire row
    row.style.fontWeight = 'bold';
}

// Function to reset highlights when the search is cleared
function resetHighlights() {
    const table = document.getElementById('invoiceTable');
    const rows = table.getElementsByTagName('tr');
    for (let i = 1; i < rows.length; i++) { // Skip the header row (i = 1)
        rows[i].style.backgroundColor = ''; // Remove row background color
        rows[i].style.fontWeight = ''; // Reset font weight
    }
}

// Function to show all rows
function showAllRows(rows) {
    for (let i = 1; i < rows.length; i++) {
        rows[i].style.display = ''; // Show all rows
    }
}
