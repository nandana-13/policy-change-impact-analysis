import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8001/api/auth/login",
        {
          username: username.trim(),
          password: password,
        }
      );

      const data = response.data;

      // Store authentication information
      localStorage.setItem(
        "access_token",
        data.access_token
      );

      localStorage.setItem(
        "user",
        JSON.stringify({
          user_id: data.user_id,
          username: data.username,
          role: data.role,
        })
      );

      // Role-based navigation
      if (data.role === "admin") {
        navigate("/admin");
      } else {
        navigate("/dashboard");
      }

    } catch (error) {
      if (error.response) {
        setError(
          error.response.data?.detail ||
          "Invalid username or password."
        );
      } else {
        setError(
          "Unable to connect to the authentication server."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">

      <div className="login-container">

        {/* BRAND */}
        <div className="login-brand">
          <div className="login-brand-mark">PL</div>

          <div>
            <h1>PolicyLens</h1>
            <p>Regulatory Intelligence</p>
          </div>
        </div>


        {/* LOGIN CARD */}
        <div className="login-card">

          <div className="login-header">
            <div className="login-eyebrow">
              SECURE WORKSPACE ACCESS
            </div>

            <h2>Sign in</h2>

            <p>
              Sign in to access your PolicyLens workspace.
            </p>
          </div>


          <form onSubmit={handleSubmit}>

            {/* USERNAME */}
            <div className="login-field">

              <label htmlFor="username">
                Username
              </label>

              <input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
              />

            </div>


            {/* PASSWORD */}
            <div className="login-field">

              <label htmlFor="password">
                Password
              </label>

              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />

            </div>


            {/* ERROR */}
            {error && (
              <div className="login-error">
                {error}
              </div>
            )}


            {/* SIGN IN */}
            <button
              type="submit"
              className="login-submit"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign In"}

              {!loading && <span>→</span>}
            </button>

          </form>


          {/* BACK */}
          <button
            className="back-to-overview"
            onClick={() => navigate("/")}
            disabled={loading}
          >
            ← Back to overview
          </button>

        </div>


        {/* FOOTER */}
        <div className="login-footer">
          PolicyLens · Enterprise Regulatory Intelligence Workspace
        </div>

      </div>

    </div>
  );
}