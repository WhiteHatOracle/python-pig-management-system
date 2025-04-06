function confirmDelete() {
    return confirm('Are you sure you want to delete this litter record? This action cannot be undone.');
}
function goBack(service_id) {
    window.location.href = "/sows/" + service_id; 
}