/**
 * main.jsx
 * React application entry point.
 * Mounts the HoldMeltDashboard component into the #root div.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
