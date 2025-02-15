
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

const Search = () => {
  const navigate = useNavigate();
  const [medication1, setMedication1] = useState("");
  const [medication2, setMedication2] = useState("");
  const [sideEffect, setSideEffect] = useState("");
  const [isCalculating, setIsCalculating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!medication1 || !medication2 || !sideEffect) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsCalculating(true);
    
    // Simulate calculation time with animation
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
            <CardTitle>New Medication Interaction Search</CardTitle>
          </CardHeader>
          <CardContent>
            {isCalculating ? (
              <div className="py-12 space-y-6 text-center">
                <div className="text-2xl font-medium text-purple-600 animate-pulse">
                  Analyzing Interactions...
                </div>
                <div className="max-w-md mx-auto h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 animate-[slide-in_15s_linear]" />
                </div>
                <div className="text-sm text-gray-500">
                  This may take up to 15 seconds
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
                  Analyze Interaction
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
