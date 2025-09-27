import React from "react";
import "../Pages/UserProfile.css";

const ToastNotification = ({ message, type = "info" }) => {
  if (!message) return null;

  return (
    <div className={`toast-notification ${type}`}>
      {message}
    </div>
  );
};

export default ToastNotification;
