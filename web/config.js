// Runtime config for the static frontend.
// - Set `backendOrigin` to the origin (scheme+host+optional port+optional base path)
//   of your FastAPI server, e.g. "https://api.example.com" or "https://example.com/core".
// - Leave it as an empty string to talk to the same origin (useful for local dev).
//
// Note: When deployed on Vercel as a purely static site, you typically want this to
//       point to the separately hosted backend, since Vercel does not run this
//       project's Python/FastAPI + WebSocket server.
// Runtime config for the static frontend.
// Auto-detect local dev vs deployed frontend so both cases "just work":
// - When running locally (served by FastAPI at http://127.0.0.1:8000 or http://localhost:8000),
//   talk to the same origin to avoid CORS and ensure you use your local backend.
// - When opened from a public site (e.g. GitHub Pages), default to the deployed backend origin.
//   You can still override at runtime with ?backend=https://your-backend.example.com
window.RR = window.RR || {};
(function () {
  try {
    var host = (typeof location !== 'undefined') ? String(location.hostname || '').toLowerCase() : '';
    var isLocal = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(host);
    // Deployed backend default (used when not on localhost)
    var REMOTE_DEFAULT = "https://funk-encouraged-sprint-liz.trycloudflare.com";
    // Same-origin for local dev; remote default otherwise
    window.RR.backendOrigin = isLocal ? "" : REMOTE_DEFAULT;
  } catch (e) {
    // Fallback to previous deployed default if detection fails
    window.RR.backendOrigin = "https://funk-encouraged-sprint-liz.trycloudflare.com";
  }
})();
