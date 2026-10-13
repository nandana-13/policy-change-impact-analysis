import {
  BrowserRouter,
  Routes,
  Route,
  Navigate
} from "react-router-dom";

import PolicyLanding from "./pages/dashboard/PolicyLanding";
import PolicyDashboard from "./pages/dashboard/PolicyDashboard";
import Login from "./pages/auth/Login";

import AdminDashboard from "./pages/admin/AdminDashboard";

import ProtectedRoute from "./components/ProtectedRoute";

import "./index.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* =========================
            PUBLIC ROUTES
        ========================= */}

        <Route
          path="/"
          element={<PolicyLanding />}
        />

        <Route
          path="/login"
          element={<Login />}
        />


        {/* =========================
            ANALYST ROUTES
        ========================= */}

        <Route element={<ProtectedRoute allowedRoles={["analyst"]} />}>

          <Route
            path="/dashboard"
            element={<PolicyDashboard />}
          />

        </Route>


        {/* =========================
            ADMIN ROUTES
        ========================= */}

        <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>

          <Route
            path="/admin"
            element={<AdminDashboard />}
          />

        </Route>


        {/* =========================
            FALLBACK
        ========================= */}

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;