
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Navbar } from "@/components/Navbar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await login(email, password);
    } catch (error) {
      // Error is already handled in the AuthContext
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 relative pb-20">
      <Navbar />
      <div className="container mx-auto px-4 pt-32">
        <Card className="max-w-md mx-auto animate-fade-in">
          <CardHeader>
            <CardTitle>Welcome Back</CardTitle>
            <CardDescription>
              Please login to access your personal area
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email
                </label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Logging in...
                  </>
                ) : (
                  "Login"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
      
      <footer className="fixed bottom-0 left-0 right-0 bg-white bg-opacity-90 backdrop-blur-sm border-t border-gray-200 py-4 text-sm text-gray-500 text-center animate-fade-in delay-500">
        <div className="container mx-auto px-4">
          <p className="mb-1">
            Created by Eng. Lea Korol and Eng. Talia Kaziof
          </p>
          <p>
            In collaboration with Dr. Boris Gorlik
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Login;
