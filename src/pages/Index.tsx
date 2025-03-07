import { useAuth } from "@/context/AuthContext";  
import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/Navbar";
import { useNavigate } from "react-router-dom"; // navigate in the app
import { BeakerIcon, ShieldCheckIcon, ActivityIcon } from "lucide-react";

const Index = () => {
  const { isAuthenticated } = useAuth(); // checks if the user is already connected
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 relative pb-20">
      <Navbar />
      <div className="container mx-auto px-4 pt-32">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-block mb-4 px-4 py-1 rounded-full bg-purple-100 text-purple-700 text-sm font-medium animate-fade-in">
            Welcome to REMEZ
          </div>
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-blue-500 bg-clip-text text-transparent animate-fade-in delay-100">
            Advanced Medication Interaction Analysis
          </h1>
          <p className="text-xl text-gray-600 mb-8 animate-fade-in delay-200">
            Discover potential interactions between medications and their side effects using our sophisticated analysis tools.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 mt-16 animate-fade-in delay-300">
            <div className="p-6 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow border border-gray-100">
              <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
                <BeakerIcon className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Advanced Analysis</h3>
              <p className="text-gray-600 text-sm">
                Precise medication interaction evaluation using modern algorithms
              </p>
            </div>
            
            <div className="p-6 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow border border-gray-100">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                <ShieldCheckIcon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Evidence-Based</h3>
              <p className="text-gray-600 text-sm">
                Research-backed data analysis for reliable results
              </p>
            </div>
            
            <div className="p-6 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow border border-gray-100">
              <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center mx-auto mb-4">
                <ActivityIcon className="w-6 h-6 text-indigo-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Real-Time Results</h3>
              <p className="text-gray-600 text-sm">
                Instant visualization of interaction analysis
              </p>
            </div>
          </div>

          <Button
            onClick={() => navigate(isAuthenticated ? "/search" : "/login")}
            size="lg"
            className="animate-fade-in delay-400"
          >
            {isAuthenticated ? "Start New Search" : "Login to Begin"}
          </Button>
        </div>
      </div>
      
      <footer className="fixed bottom-0 left-0 right-0 bg-white bg-opacity-90 backdrop-blur-sm border-t border-gray-200 py-4 text-sm text-gray-500 text-center animate-fade-in delay-500">
        <div className="container mx-auto px-4">
          <p className="mb-1">
            Created by Eng. Leah Korol and Eng. Talya Kazayof
          </p>
          <p>
            In collaboration with Dr. Boris Gorelik
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
