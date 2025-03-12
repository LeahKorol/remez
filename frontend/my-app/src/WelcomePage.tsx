import React from "react";
import { useUser } from "./UserContext";
import { useNavigate } from "react-router-dom";

const WelcomePage: React.FC = () => {
  const { username } = useUser();
  const navigate = useNavigate();

  return (
    <div>
      <h2>Welcome, {username}!</h2>
      <button onClick={() => navigate("/")}>Logout</button>
    </div>
  );
};

export default WelcomePage;
