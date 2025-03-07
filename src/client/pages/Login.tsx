// import { useState } from "react";
// import { useAuth } from "@/context/AuthContext";
// import Layout from "@/components/Layout";
// import { Input } from "@/components/ui/input";
// import { Button } from "@/components/ui/button";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
// import { Loader2 } from "lucide-react";
// import { toast } from "sonner";

// const Login = () => {
//   const [email, setEmail] = useState(""); // Save the user's email
//   const [password, setPassword] = useState(""); // Save the user's password
//   const [isLoading, setIsLoading] = useState(false); // Check if the login request is in progress
//   const { login } = useAuth();

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault(); // Prevent page refresh on form submission
//     setIsLoading(true);
    
//     try {
//       if (!email || !password) {
//         toast.error("Please enter both email and password");
//         setIsLoading(false);
//         return;
//       }
      
//       await login(email, password);
//       toast.success("Login successful!");
//     } catch (error: any) {
//       console.error("Login submission error:", error);
//       const errorMessage = error.message || "Login failed. Please try again.";
//       toast.error(errorMessage);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <Layout>
//       <div className="container mx-auto px-4 pt-32">
//         <Card className="max-w-md mx-auto animate-fade-in">
//           <CardHeader>
//             <CardTitle>Welcome Back</CardTitle>
//             <CardDescription>
//               Please login to access your personal area
//             </CardDescription>
//           </CardHeader>
//           <CardContent>
//             <form onSubmit={handleSubmit} className="space-y-4"> {/* Handle form submission */}
//               <div className="space-y-2">
//                 <label htmlFor="email" className="text-sm font-medium">
//                   Email
//                 </label>
//                 <Input
//                   id="email"
//                   type="email"
//                   value={email}
//                   onChange={(e) => setEmail(e.target.value)} // Update email state
//                   required
//                   disabled={isLoading}
//                 />
//               </div>
//               <div className="space-y-2">
//                 <label htmlFor="password" className="text-sm font-medium">
//                   Password
//                 </label>
//                 <Input
//                   id="password"
//                   type="password" // Hide characters
//                   value={password}
//                   onChange={(e) => setPassword(e.target.value)}
//                   required
//                   disabled={isLoading}
//                 />
//               </div>
//               <Button type="submit" className="w-full" disabled={isLoading}>
//                 {isLoading ? (
//                   <>
//                     <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Logging in...
//                   </>
//                 ) : (
//                   "Login"
//                 )}
//               </Button>
//             </form>
//           </CardContent>
//         </Card>
//       </div>
//     </Layout>
//   );
// };

// export default Login;




import { useState } from "react";
import Layout from "@/client/components/Layout";
import { Input } from "@/client/components/ui/input";
import { Button } from "@/client/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/client/components/ui/card";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

const Login = () => {
  const [email, setEmail] = useState(""); // save the user email
  const [password, setPassword] = useState(""); // save the user password
  const [isLoading, setIsLoading] = useState(false); // Check if the login request is in progress
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevent page refresh on form submission
    
    if (!email || !password) {
      toast.error("Please enter both email and password");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:5000/sessionLogin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
        credentials: "include", // access the saving of the session
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Login failed");
      }

      toast.success("Login successful!");
    } catch (error: any) {
      toast.error(error.message || "An error occurred during login");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
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
                <label htmlFor="email" className="text-sm font-medium">Email</label>
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
                <label htmlFor="password" className="text-sm font-medium">Password</label>
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
    </Layout>
  );
};

export default Login;
