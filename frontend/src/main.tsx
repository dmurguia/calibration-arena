import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { ClerkRoot } from "./pilot/clerk";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ClerkRoot>
        <App />
      </ClerkRoot>
    </BrowserRouter>
  </React.StrictMode>,
);
