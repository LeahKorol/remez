import React, { useEffect, useRef } from "react";
import { FaCheckCircle, FaExclamationTriangle, FaInfoCircle, FaTimesCircle } from 'react-icons/fa';
import "./ToastNotification.css";

const ToastNotification = ({ id, message, type = "info", duration = 8000, onClose, index = 0 }) => {
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!message) return () => { };

    timeoutRef.current = setTimeout(() => {
      onClose && onClose(id);
    }, duration);

    return () => {
      clearTimeout(timeoutRef.current);
    };
  }, [id, message, duration, onClose]);

  const handleMouseEnter = () => {
    clearTimeout(timeoutRef.current);
  };

  const handleMouseLeave = () => {
    // begin a new timeout when the mouse leaves
    timeoutRef.current = setTimeout(() => {
      onClose && onClose(id);
    }, duration);
  };

  const getIcon = () => {
    switch (type) {
      case "success":
        return <FaCheckCircle className="toast-icon success" />;
      case "error":
        return <FaTimesCircle className="toast-icon error" />;
      case "warning":
        return <FaExclamationTriangle className="toast-icon warning" />;
      default:
        return <FaInfoCircle className="toast-icon info" />;
    }
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
        animationDelay: `${index * 0.05}s`,
        ["--duration"]: `${duration / 1000}s`,
      }}
    >
      {getIcon()}
      <span className="toast-message">{message}</span>
    </div>
  );
};

export default ToastNotification;