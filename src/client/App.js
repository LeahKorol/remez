"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var toaster_1 = require("@/components/ui/toaster");
var sonner_1 = require("@/components/ui/sonner");
var tooltip_1 = require("@/components/ui/tooltip");
var react_query_1 = require("@tanstack/react-query");
var react_router_dom_1 = require("react-router-dom");
var Index_1 = require("./pages/Index");
var Login_1 = require("./pages/Login");
var Profile_1 = require("./pages/Profile");
var Search_1 = require("./pages/Search");
var Results_1 = require("./pages/Results");
var NotFound_1 = require("./pages/NotFound");
var AuthContext_1 = require("./context/AuthContext");
var queryClient = new react_query_1.QueryClient();
var App = function () { return (<react_query_1.QueryClientProvider client={queryClient}>
    <react_router_dom_1.BrowserRouter>
      <AuthContext_1.AuthProvider>
        <tooltip_1.TooltipProvider>
          <toaster_1.Toaster />
          <sonner_1.Toaster />
          <react_router_dom_1.Routes>
            <react_router_dom_1.Route path="/" element={<Index_1.default />}/>
            <react_router_dom_1.Route path="/login" element={<Login_1.default />}/>
            <react_router_dom_1.Route path="/profile" element={<Profile_1.default />}/>
            <react_router_dom_1.Route path="/search" element={<Search_1.default />}/>
            <react_router_dom_1.Route path="/results" element={<Results_1.default />}/>
            <react_router_dom_1.Route path="*" element={<NotFound_1.default />}/>
          </react_router_dom_1.Routes>
        </tooltip_1.TooltipProvider>
      </AuthContext_1.AuthProvider>
    </react_router_dom_1.BrowserRouter>
  </react_query_1.QueryClientProvider>); };
exports.default = App;
