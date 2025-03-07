import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/client/context/AuthContext";
import { Navbar } from "@/client/components/Navbar";
import { Button } from "@/client/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/client/components/ui/card";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceArea 
} from "recharts";
import { toast } from "sonner";
import { Pencil, Search, ZoomIn, ZoomOut } from "lucide-react";
import { searchService, SearchInput } from "@/client/services/searchService";

const Results = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [showChart, setShowChart] = useState(false);
  const [data, setData] = useState<Array<{ name: string; value: number }>>([]);
  const [isFromSaved, setIsFromSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Zoom functionality state
  const [leftX, setLeftX] = useState<string | null>(null);
  const [rightX, setRightX] = useState<string | null>(null);
  const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null);
  const [refAreaRight, setRefAreaRight] = useState<string | null>(null);
  const [originalData, setOriginalData] = useState<Array<{ name: string; value: number }>>([]);

  useEffect(() => {
    if (!location.state) {
      navigate("/search");
      return;
    }
    
    // Check if we're viewing a saved result or generating a new one
    const { savedResult } = location.state;
    
    if (savedResult) {
      // Display saved result directly
      setData(savedResult.data);
      setOriginalData(savedResult.data);
      setIsLoading(false);
      setShowChart(true);
      setIsFromSaved(true);
    } else {
      // Generate new result with animation
      const finalData = [
        { name: "Jan", value: 65 },
        { name: "Feb", value: 59 },
        { name: "Mar", value: 80 },
        { name: "Apr", value: 55 },
        { name: "May", value: 72 },
        { name: "Jun", value: 68 },
      ];

      setOriginalData(finalData);

      setTimeout(() => {
        setIsLoading(false);
        setShowChart(true);
      }, 1000);

      finalData.forEach((point, index) => {
        setTimeout(() => {
          setData(prev => [...prev, point]);
        }, 1500 + (index * 300));
      });
    }

  }, [location.state, navigate]);

  const handleSave = async () => {
    if (!user) {
      toast.error("You must be logged in to save searches");
      navigate("/login");
      return;
    }

    const { medication1, medication2, sideEffect } = location.state;
    
    setIsSaving(true);
    
    try {
      const searchData: SearchInput = {
        medication1,
        medication2,
        sideEffect,
        result: {
          likelihood: "moderate", // This would be dynamic in a real app
          data: originalData
        }
      };
      
      await searchService.saveSearch(user.uid, searchData);
      toast.success("Search results saved successfully!");
      navigate("/profile");
    } catch (error) {
      console.error("Failed to save search:", error);
      toast.error("Failed to save search");
    } finally {
      setIsSaving(false);
    }
  };

  const handleEdit = () => {
    const { medication1, medication2, sideEffect } = location.state;
    navigate("/search", { 
      state: { 
        medication1, 
        medication2, 
        sideEffect,
        isEditing: true 
      } 
    });
  };

  // Zoom functionality
  const getAxisYDomain = (from: string, to: string, ref: string, offset: number) => {
    const refData = data.slice(
      data.findIndex(d => d.name === from),
      data.findIndex(d => d.name === to) + 1
    );
    
    let [bottom, top] = [
      Math.min(...refData.map(d => d.value)) - offset,
      Math.max(...refData.map(d => d.value)) + offset
    ];
    
    return [bottom, top];
  };

  const zoomIn = () => {
    if (refAreaLeft === refAreaRight || refAreaRight === null || refAreaLeft === null) {
      setRefAreaLeft(null);
      setRefAreaRight(null);
      return;
    }

    // Ensure left is always less than right
    const leftName = refAreaLeft;
    const rightName = refAreaRight;

    const [bottom, top] = getAxisYDomain(
      leftName!,
      rightName!,
      'value',
      5
    );

    setLeftX(leftName);
    setRightX(rightName);

    const zoomedData = data.slice(
      data.findIndex(d => d.name === leftName),
      data.findIndex(d => d.name === rightName) + 1
    );

    setData(zoomedData);
    setRefAreaLeft(null);
    setRefAreaRight(null);
  };

  const zoomOut = () => {
    setData(originalData);
    setLeftX(null);
    setRightX(null);
    setRefAreaLeft(null);
    setRefAreaRight(null);
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
              <CardTitle className="animate-fade-in delay-200">
                Interaction Analysis: {medication1} + {medication2}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-gray-600 animate-fade-in delay-300">
                Based on our analysis, the combination of {medication1} and{" "}
                {medication2} shows a moderate likelihood of causing {sideEffect}.
                Please consult with your healthcare provider for personalized
                advice.
              </p>

              <div 
                className={`h-[400px] w-full transition-all duration-1000 
                  ${showChart ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}
              >
                <div className="flex justify-end mb-2 space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={zoomOut}
                    disabled={!leftX && !rightX}
                  >
                    <ZoomOut className="h-4 w-4 mr-1" /> Reset Zoom
                  </Button>
                  <p className="text-sm text-gray-500 italic">Tip: Drag on chart to zoom into a specific area</p>
                </div>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart 
                    data={data}
                    onMouseDown={e => e && e.activeLabel && setRefAreaLeft(e.activeLabel)}
                    onMouseMove={e => refAreaLeft && e && e.activeLabel && setRefAreaRight(e.activeLabel)}
                    onMouseUp={zoomIn}
                  >
                    <CartesianGrid 
                      strokeDasharray="3 3" 
                      className="animate-fade-in delay-400"
                    />
                    <XAxis 
                      dataKey="name" 
                      allowDataOverflow
                      className="animate-fade-in delay-500"
                    />
                    <YAxis 
                      allowDataOverflow
                      className="animate-fade-in delay-500" 
                    />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 8 }}
                      className="animate-data-point"
                    />
                    {refAreaLeft && refAreaRight && (
                      <ReferenceArea 
                        x1={refAreaLeft} 
                        x2={refAreaRight} 
                        strokeOpacity={0.3} 
                        fill="#8884d8" 
                        fillOpacity={0.3} 
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                {isFromSaved ? (
                  <>
                    <Button 
                      variant="outline" 
                      onClick={handleEdit}
                      className="animate-fade-in delay-700"
                    >
                      <Pencil className="mr-2 h-4 w-4" /> עריכה
                    </Button>
                    <Button 
                      onClick={() => navigate("/search")}
                      className="animate-fade-in delay-800"
                    >
                      <Search className="mr-2 h-4 w-4" /> חיפוש חדש
                    </Button>
                  </>
                ) : (
                  <>
                    <Button 
                      variant="outline" 
                      onClick={() => navigate("/search")}
                      className="animate-fade-in delay-700"
                    >
                      New Search
                    </Button>
                    <Button 
                      onClick={handleSave}
                      disabled={isSaving}
                      className="animate-fade-in delay-800"
                    >
                      {isSaving ? 'Saving...' : 'Save Results'}
                    </Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Results;
