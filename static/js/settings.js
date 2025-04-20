function clearCache() {
    alert("Cache cleared successfully!");
    // Real logic would clear cached data from localStorage, service worker, etc.
  }
  
  function resetSettings() {
    const confirmReset = confirm("Are you sure you want to reset all settings to default?");
    if (confirmReset) {
      alert("Settings reset to default.");
      // Real logic would reset settings stored in localStorage, send a request to backend, etc.
    }
  }