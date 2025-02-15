
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { toast } from "sonner";

const Results = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!location.state) {
      navigate("/search");
      return;
    }
    
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  }, [location.state, navigate]);

  const data = [
    { name: "Jan", value: 65 },
    { name: "Feb", value: 59 },
    { name: "Mar", value: 80 },
    { name: "Apr", value: 55 },
    { name: "May", value: 72 },
    { name: "Jun", value: 68 },
  ];

  const handleSave = () => {
    toast.success("Search results saved successfully!");
    navigate("/profile");
  };

  if (isLoading || !location.state) return null;

  const { medication1, medication2, sideEffect } = location.state;

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <Navbar />
      <div className="container mx-auto px-4 pt-32">
        <div className="max-w-4xl mx-auto space-y-8">
          <Card className="animate-fade-in">
            <CardHeader>
              <div className="inline-block mb-2 px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-sm">
                Analysis Results
              </div>
              <CardTitle>
                Interaction Analysis: {medication1} + {medication2}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-gray-600">
                Based on our analysis, the combination of {medication1} and{" "}
                {medication2} shows a moderate likelihood of causing {sideEffect}.
                Please consult with your healthcare provider for personalized
                advice.
              </p>

              <div className="h-[400px] w-full animate-fade-in delay-200">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                <Button variant="outline" onClick={() => navigate("/search")}>
                  New Search
                </Button>
                <Button onClick={handleSave}>Save Results</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Results;
