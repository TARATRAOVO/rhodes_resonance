// Runtime config for the static frontend.
// - Set `backendOrigin` to the origin (scheme+host+optional port+optional base path)
//   of your FastAPI server, e.g. "https://api.example.com" or "https://example.com/core".
// - Leave it as an empty string to talk to the same origin (useful for local dev).
//
// Note: When deployed on Vercel as a purely static site, you typically want this to
//       point to the separately hosted backend, since Vercel does not run this
//       project's Python/FastAPI + WebSocket server.
window.RR = window.RR || {};
window.RR.backendOrigin = ""; // e.g. "https://your-backend.example.com"

