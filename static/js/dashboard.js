document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("addPig").addEventListener("click", function() {
        alert("Adding a new pig...");
    });

    document.getElementById("viewReports").addEventListener("click", function() {
        alert("Viewing reports...");
    });

    const weightCtx = document.getElementById('weightChart').getContext('2d');
    new Chart(weightCtx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            datasets: [{
                label: 'Weight Trends',
                data: [60, 65, 70, 75, 80],
                borderColor: 'green',
                fill: false
            }]
        }
    });

    const healthCtx = document.getElementById('healthChart').getContext('2d');
    new Chart(healthCtx, {
        type: 'doughnut',
        data: {
            labels: ['Healthy', 'Sick', 'Underweight'],
            datasets: [{
                data: [70, 20, 10],
                backgroundColor: ['green', 'red', 'yellow']
            }]
        }
    });
});
