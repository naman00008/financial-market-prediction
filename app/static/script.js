document.addEventListener("DOMContentLoaded", () => {
    const navItems = document.querySelectorAll(".nav-links li");
    const tabContents = document.querySelectorAll(".tab-content");

    // Tab switching logic
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            // Remove active class from all nav items
            navItems.forEach(nav => nav.classList.remove("active"));
            
            // Add active class to clicked item
            item.classList.add("active");
            
            // Hide all tab contents
            tabContents.forEach(content => content.classList.remove("active"));
            
            // Show the targeted tab content
            const targetTabId = item.getAttribute("data-tab");
            document.getElementById(targetTabId).classList.add("active");
        });
    });
    
    // Test API connection
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log("API Status:", data.message);
        })
        .catch(error => {
            console.error("API Error:", error);
            document.querySelector(".status-indicator .dot").style.backgroundColor = "red";
            document.querySelector(".status-indicator").innerHTML += " (Error)";
        });
});
