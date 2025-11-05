import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import ErrorBoundary from "./components/ErrorBoundary";

const root = ReactDOM.createRoot(document.getElementById("root"));

// Add global error handler to prevent page reload
window.addEventListener('error', (event) => {
  console.error('🚨 Global error caught:', event.error);
  event.preventDefault(); // Prevent default browser error handling
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('🚨 Unhandled promise rejection:', event.reason);
  event.preventDefault();
});

root.render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);
