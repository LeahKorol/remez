
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import React from "react";

export const Navbar = () => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-500 bg-clip-text text-transparent">
          REMEZ
        </Link>
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <Link to="/profile">
                <Button variant="ghost">Profile</Button>
              </Link>
              <Link to="/search">
                <Button variant="ghost">New Search</Button>
              </Link>
              <Button onClick={logout} variant="outline">
                Logout
              </Button>
            </>
          ) : (
            <Link to="/login">
              <Button>Login</Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};
