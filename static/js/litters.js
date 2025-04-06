function confirmDelete() {
    return confirm('Are you sure you want to delete this litter record? This action cannot be undone.');
}
{/* <button onclick="goBackToServiceRecords()" class="btn btn-secondary">← Back to Service Record</button> */}


function goBackToServiceRecords() {
    const sowId = window.sowId;  // Get the sowId from the global JS variable
    window.location.href = `/sows/${sowId}`;
  }
  