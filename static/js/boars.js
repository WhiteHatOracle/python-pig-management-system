// for the search inputs
let debounceTimer;

function filterBoars() {
    // Clear the previous debounce timer
    clearTimeout(debounceTimer);

    // Set a new debounce timer
    debounceTimer = setTimeout(function () {
        const searchInput = document.getElementById('searchInput').value.toLowerCase();
        const table = document.getElementById('BoarTable');
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
            const cells = rows[i].getElementsByTagName('th');
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
    row.style.backgroundColor = '#62a7f2 '; 
    row.style.fontWeight = 'bold';
}

// Function to reset highlights when the search is cleared
function resetHighlights() {
    const table = document.getElementById('BoarTable');
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

document.addEventListener("DOMContentLoaded", function () {
        // Select all three-dot buttons
        const menuButtons = document.querySelectorAll(".menu-btn");

        menuButtons.forEach(button => {
            button.addEventListener("click", function (event) {
                event.stopPropagation(); // Prevent click from bubbling up

                // Close any other open menus before opening a new one
                document.querySelectorAll(".dropdown-menu").forEach(menu => {
                    if (menu !== button.nextElementSibling) {
                        menu.classList.remove("show");
                    }
                });

                // Toggle the dropdown menu for this specific button
                const dropdown = button.nextElementSibling;
                dropdown.classList.toggle("show");
            });
        });

        // Close the dropdown when clicking anywhere outside
        document.addEventListener("click", function () {
            document.querySelectorAll(".dropdown-menu").forEach(menu => {
                menu.classList.remove("show");
            });
        });
});
