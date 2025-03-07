
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Navbar } from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { searchService, SavedSearch } from "@/services/searchService";

const Profile = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }

    const fetchSavedSearches = async () => {
      if (user) {
        setIsLoading(true);
        try {
          const searches = await searchService.getSavedSearches(user.uid);
          setSavedSearches(searches);
        } catch (error) {
          console.error("Failed to fetch saved searches:", error);
          toast.error("Failed to load your saved searches");
        } finally {
          setIsLoading(false);
        }
      }
    };

    fetchSavedSearches();
  }, [isAuthenticated, navigate, user]);

  const handleDelete = async (id: string) => {
    if (!user) return;
    
    try {
      const success = await searchService.deleteSearch(user.uid, id);
      if (success) {
        setSavedSearches(prev => prev.filter(search => search.id !== id));
        toast.success("Search deleted successfully");
      }
    } catch (error) {
      console.error("Failed to delete search:", error);
      toast.error("Failed to delete search");
    }
  };

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
              {isLoading ? (
                <div className="py-10 text-center">
                  <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-purple-500 border-r-transparent"></div>
                  <p className="mt-2 text-gray-500">Loading saved searches...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {savedSearches.length === 0 ? (
                    <p className="text-center text-gray-500 py-4">No saved searches yet</p>
                  ) : (
                    savedSearches.map((search) => (
                      <div
                        key={search.id}
                        className="p-4 rounded-lg border hover:border-purple-500 transition-colors"
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
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(search.id)}
                              className="text-red-500 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              onClick={() => navigate("/results", { 
                                state: { 
                                  medication1: search.medication1,
                                  medication2: search.medication2,
                                  sideEffect: search.sideEffect,
                                  savedResult: search.result
                                } 
                              })}
                            >
                              View Results
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
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
