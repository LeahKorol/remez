import React, { createContext, useState, useContext } from "react";

const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
  const [userId, setUserId] = useState(null);

  const login = (id) => {
    setUserId(id);
    localStorage.setItem("user_id", id); // keep user logged in across sessions
  };

  const logout = () => {
    setUserId(null);
    localStorage.removeItem("user_id");
  };

  return (
    <UserContext.Provider value={{ userId, login, logout }}>
      {children}
    </UserContext.Provider>
  );
};

// hook to use the UserContext
export const useUser = () => useContext(UserContext);
