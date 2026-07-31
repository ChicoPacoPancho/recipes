import App from './App.svelte';
import './app.css';

const app = new App({
  target: document.getElementById('app'),
});

export default app;

// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // Service worker registration failed - app still works
    });
  });
}
