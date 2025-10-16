import React, { useEffect, useRef } from "react";
import "../Pages/UserProfile.css";

const ToastNotification = ({ id, message, type = "info", duration = 8000, onClose, index = 0 }) => {
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!message) return () => {};

    timeoutRef.current = setTimeout(() => {
      onClose && onClose(id);
    }, duration);

    return () => {
      clearTimeout(timeoutRef.current);
    };
  }, [id, message, duration, onClose]);

  const offset = index * -10; // the oldest toast is at the bottom
  const zIndex = 1000 + (50 - index);

  const handleMouseEnter = () => {
    clearTimeout(timeoutRef.current);
  };

  const handleMouseLeave = () => {
    // begin a new timeout when the mouse leaves
    timeoutRef.current = setTimeout(() => {
      onClose && onClose(id);
    }, duration);
  };

  return (
    <div
      className={`toast-notification ${type}`}
      role="status"
      aria-live="polite"
      title={message}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{
        zIndex: 2000 + index,
        ["--duration"]: `${duration / 1000}s`,
      }}
    >
      {message}
    </div>
  );
};

export default ToastNotification;