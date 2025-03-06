function toggleMenu() {
    const menu = document.getElementById("mobile-menu");
    const menuIcon = document.getElementById("menu-icon");
    const closeIcon = document.getElementById("close-icon");
    
    if (menu.classList.contains("hidden")) {
        menu.classList.remove("hidden");
        menuIcon.style.display = "none";
        closeIcon.style.display = "block";
        document.addEventListener("click", closeMenuOutside);
    } else {
        menu.classList.add("hidden");
        menuIcon.style.display = "block";
        closeIcon.style.display = "none";
        document.removeEventListener("click", closeMenuOutside);
    }
}

function closeMenuOutside(event) {
    const menu = document.getElementById("mobile-menu");
    const menuIcon = document.querySelector(".mobile-menu-icon");
    
    if (!menu.contains(event.target) && !menuIcon.contains(event.target)) {
        menu.classList.add("hidden");
        document.getElementById("menu-icon").style.display = "block";
        document.getElementById("close-icon").style.display = "none";
        document.removeEventListener("click", closeMenuOutside);
    }
}