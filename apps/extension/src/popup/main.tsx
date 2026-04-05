import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./popup.css";

const container = document.getElementById("root");

if (!container) {
  throw new Error("Popup root element was not found.");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
