// Auto-dismiss flash alerts after 4 seconds
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert.fade.show').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 4000);
  });
});
