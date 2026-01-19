import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "./components/theme-provider";
import { AuthProvider } from "./context/auth-context";
import { Toaster } from "@/components/ui/sonner";
import App from "./App";
import "./globals.css";
import "./index.css";
import { initTrafficSource } from "@/utils/traffic-source";

// 在渲染前初始化流量来源
initTrafficSource();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter basename="/znkfzs">
          <App />
          <Toaster />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
);
