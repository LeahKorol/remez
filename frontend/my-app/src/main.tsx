import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { UserProvider } from "./UserContext";
import LoginPage from "./LoginPage";
import WelcomePage from "./WelcomePage";

const App: React.FC = () => (
  <UserProvider>
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/welcome" element={<WelcomePage />} />
      </Routes>
    </Router>
  </UserProvider>
);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
