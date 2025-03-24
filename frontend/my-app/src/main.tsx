import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { UserProvider } from "./UserContext";
import LoginPage from "./LoginPage";
import WelcomePage from "./WelcomePage";
import MainApp from "./App";
import NotFound from "./NotFound";

const App: React.FC = () => (
  <UserProvider>
    <Router>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/welcome" element={<WelcomePage />} />
        <Route path="/*" element={<NotFound />} />
      </Routes>
    </Router>
  </UserProvider>
);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
