
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/Navbar";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <Navbar />
      <div className="container mx-auto px-4 pt-32">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-block mb-4 px-4 py-1 rounded-full bg-purple-100 text-purple-700 text-sm font-medium">
            Welcome to REMEZ
          </div>
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-blue-500 bg-clip-text text-transparent">
            Advanced Medication Interaction Analysis
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Discover potential interactions between medications and their side effects using our sophisticated analysis tools.
          </p>
          <Button
            onClick={() => navigate(isAuthenticated ? "/search" : "/login")}
            size="lg"
            className="animate-fade-in"
          >
            {isAuthenticated ? "Start New Search" : "Login to Begin"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Index;
