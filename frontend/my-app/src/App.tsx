import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
// import Index from "./pages/Index";
// import Login from "./pages/Login";
// import Profile from "./pages/Profile";
// import Search from "./pages/Search";
// import Results from "./pages/Results";
// import NotFound from "./pages/NotFound";
// import { AuthProvider } from "./context/AuthContext";
// import { Toaster } from "@/client/components/ui/toaster";
// import { Toaster as Sonner } from "@/client/components/ui/sonner";
// import { TooltipProvider } from "@/client/components/ui/tooltip";

const queryClient = new QueryClient();

const MainApp = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {/* <AuthProvider>
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
        </AuthProvider> */}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default MainApp;
