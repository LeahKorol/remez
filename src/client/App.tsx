
import { Toaster } from "../client/components/ui/toaster";
import { Toaster as Sonner } from "../client/components/ui/sonner";
import { TooltipProvider } from "../client/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "../client/pages/Index";
import Login from "../client/pages/Login";
import Profile from "../client/pages/Profile";
import Search from "../client/pages/Search";
import Results from "../client/pages/Results";
import NotFound from "../client/pages/NotFound";
import { AuthProvider } from "./context/AuthContext";
import React from "react";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/login" element={<Login />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/search" element={<Search />} />
            <Route path="/results" element={<Results />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </TooltipProvider>
      </AuthProvider>
    </BrowserRouter>
  </QueryClientProvider>
);

export default App;
