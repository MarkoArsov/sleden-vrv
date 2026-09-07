(() => {
  if (!('serviceWorker' in navigator) || !window.isSecureContext) return;

  window.addEventListener('load', () => {
    const scope = new URL('./', window.location.href).pathname;
    const worker = new URL('./service-worker.js?v=6', window.location.href);
    navigator.serviceWorker.register(worker.href, { scope, updateViaCache: 'none' }).catch(() => {
      // The website remains fully usable when service workers are unavailable.
    });
  });

  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'hikes-updated') {
      window.dispatchEvent(new Event('sleden-vrv:hikes-updated'));
    }
  });
})();
