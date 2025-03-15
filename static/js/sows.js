function confirmDelete() {
    return confirm('Are you sure you want to delete this sow? This action cannot be undone.');
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