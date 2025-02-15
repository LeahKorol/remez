
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Navbar } from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const Profile = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
    }
  }, [isAuthenticated, navigate]);

  const savedSearches = [
    {
      id: 1,
      date: "2024-03-10",
      medications: ["Aspirin", "Ibuprofen"],
      sideEffect: "Headache",
    },
    {
      id: 2,
      date: "2024-03-09",
      medications: ["Paracetamol", "Codeine"],
      sideEffect: "Dizziness",
    },
  ];

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <Navbar />
      <div className="container mx-auto px-4 pt-32">
        <div className="max-w-4xl mx-auto space-y-8">
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-500">Username</label>
                  <p className="text-lg font-medium">{user.username}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Email</label>
                  <p className="text-lg font-medium">{user.email}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="animate-fade-in delay-100">
            <CardHeader>
              <CardTitle>Saved Searches</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {savedSearches.map((search) => (
                  <div
                    key={search.id}
                    className="p-4 rounded-lg border hover:border-purple-500 transition-colors cursor-pointer"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm text-gray-500">{search.date}</p>
                        <p className="font-medium">
                          {search.medications.join(" + ")}
                        </p>
                        <p className="text-sm text-gray-600">
                          Side Effect: {search.sideEffect}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        onClick={() => navigate(`/results?id=${search.id}`)}
                      >
                        View Results
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-center">
            <Button
              size="lg"
              onClick={() => navigate("/search")}
              className="animate-fade-in delay-200"
            >
              New Search
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
