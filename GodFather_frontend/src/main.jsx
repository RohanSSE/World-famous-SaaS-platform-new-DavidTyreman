import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import { AuthProvider } from "./context/AuthProvider.jsx";
import { OrbPresenceProvider } from "./context/OrbPresenceContext.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <OrbPresenceProvider>
          <App />
        </OrbPresenceProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
