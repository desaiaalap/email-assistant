// config.js
CONFIG = {
  // OAuth Configuration
  CLIENT_ID:
    "673808915782-hgbcr3o8tjjct8pvgej9uq4599pc4k0g.apps.googleusercontent.com",
  REDIRECT_URI: "https://ekdobdpkjgjndnhdhmbijjjdbidemdao.chromiumapp.org",
  SCOPES:
    "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email",

  // API Endpoints
  SERVER_URL:
    "https://test-email-assistant-673808915782.us-central1.run.app/fetch_gmail_thread",
  LOCAL_SERVER_URL: "http://127.0.0.1:8000/fetch_gmail_thread", // For development

  // Feedback API Endpoint
  FEEDBACK_URL:
    "https://test-email-assistant-673808915782.us-central1.run.app/store_feedback",
  LOCAL_FEEDBACK_URL: "http://127.0.0.1:8000/store_feedback",
};
