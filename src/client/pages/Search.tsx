import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Navbar } from "@/client/components/Navbar";
import { Input } from "@/client/components/ui/input";
import { Button } from "@/client/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/client/components/ui/card";
import { toast } from "sonner";

const Search = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [medication1, setMedication1] = useState("");
  const [medication2, setMedication2] = useState("");
  const [sideEffect, setSideEffect] = useState("");
  const [isCalculating, setIsCalculating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (location.state) {
      const { medication1, medication2, sideEffect, isEditing } = location.state;
      if (medication1) setMedication1(medication1);
      if (medication2) setMedication2(medication2);
      if (sideEffect) setSideEffect(sideEffect);
      if (isEditing) setIsEditing(true);
    }
  }, [location.state]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!medication1 || !medication2 || !sideEffect) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsCalculating(true);
    setProgress(0);

    const steps = [
      { message: "Initializing analysis...", delay: 0 },
      { message: "Processing medication data...", delay: 3000 },
      { message: "Analyzing interactions...", delay: 6000 },
      { message: "Generating visualization...", delay: 9000 },
      { message: "Finalizing results...", delay: 12000 }
    ];

    steps.forEach(({ message, delay }) => {
      setTimeout(() => {
        toast.info(message);
        setProgress((delay / 12000) * 100);
      }, delay);
    });

    setTimeout(() => {
      setIsCalculating(false);
      navigate("/results", {
        state: { medication1, medication2, sideEffect },
      });
    }, 15000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <Navbar />
      <div className="container mx-auto px-4 pt-32">
        <Card className="max-w-2xl mx-auto animate-fade-in">
          <CardHeader>
            <CardTitle>
              {isEditing ? "עריכת חיפוש" : "New Medication Interaction Search"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isCalculating ? (
              <div className="py-12 space-y-8">
                <div className="text-2xl font-medium text-purple-600 animate-pulse text-center">
                  Analyzing Interactions...
                </div>
                <div className="max-w-md mx-auto space-y-6">
                  <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="absolute inset-0 bg-purple-500 animate-progress"
                      style={{ 
                        width: `${progress}%`,
                        transition: 'width 1s ease-out'
                      }}
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className={`h-24 rounded-lg animate-pulse transition-all duration-1000 ease-in-out`}
                        style={{
                          animationDelay: `${i * 150}ms`,
                          backgroundColor: `rgba(${139}, ${104}, ${216}, ${0.3 + (i * 0.2)})`
                        }}
                      />
                    ))}
                  </div>
                  <div className="flex justify-center space-x-2 animate-pulse">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className="w-2 h-2 rounded-full bg-purple-500"
                        style={{
                          animationDelay: `${i * 200}ms`
                        }}
                      />
                    ))}
                  </div>
                </div>
                <div className="text-center space-y-2">
                  <div className="text-sm text-gray-500">
                    Estimated time remaining: {Math.ceil((15000 - (progress / 100 * 15000)) / 1000)} seconds
                  </div>
                  <div className="text-xs text-gray-400">
                    Processing your request...
                  </div>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">First Medication</label>
                  <Input
                    value={medication1}
                    onChange={(e) => setMedication1(e.target.value)}
                    placeholder="Enter first medication name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Second Medication</label>
                  <Input
                    value={medication2}
                    onChange={(e) => setMedication2(e.target.value)}
                    placeholder="Enter second medication name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Side Effect</label>
                  <Input
                    value={sideEffect}
                    onChange={(e) => setSideEffect(e.target.value)}
                    placeholder="Enter the side effect"
                    required
                  />
                </div>
                <Button type="submit" className="w-full">
                  {isEditing ? "עדכן תוצאות" : "Analyze Interaction"}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Search;
