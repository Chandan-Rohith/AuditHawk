import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";

const GRAPHQL_URL = "http://localhost:8000/graphql/";

// ── Replace with your real Google Client ID from console.cloud.google.com ──
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || "79604445384-4jrnbijh3cfqi5u1c057d4bheuchqhor.apps.googleusercontent.com";

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const googleBtnRef = useRef(null);

  // ── GraphQL helper ──
  const gql = async (query, variables) => {
    const res = await fetch(GRAPHQL_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, variables }),
    });
    const json = await res.json();
    if (json.errors) throw new Error(json.errors[0].message);
    return json.data;
  };

  // ── Handle email / password submit ──
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      let data;
      if (isLogin) {
        data = await gql(
          `mutation($email:String!,$password:String!){
            loginUser(email:$email,password:$password){
              success message token user{ id email provider }
            }
          }`,
          { email, password }
        );
        data = data.loginUser;
      } else {
        data = await gql(
          `mutation($email:String!,$password:String!){
            createUser(email:$email,password:$password){
              success message token user{ id email provider }
            }
          }`,
          { email, password }
        );
        data = data.createUser;
      }

      if (!data.success) {
        setError(data.message);
      } else {
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
        navigate("/app");
      }
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  // ── Google credential callback ──
  const handleGoogleResponse = useCallback(
    async (response) => {
      setError("");
      setLoading(true);
      try {
        const data = await gql(
          `mutation($idToken:String!){
            googleAuth(idToken:$idToken){
              success message token user{ id email provider }
            }
          }`,
          { idToken: response.credential }
        );
        const result = data.googleAuth;
        if (!result.success) {
          setError(result.message);
        } else {
          localStorage.setItem("token", result.token);
          localStorage.setItem("user", JSON.stringify(result.user));
          navigate("/app");
        }
      } catch (err) {
        setError(err.message || "Google sign-in failed.");
      } finally {
        setLoading(false);
      }
    },
    [navigate]
  );

  // ── Render Google button when SDK is ready ──
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    const interval = setInterval(() => {
      if (window.google && window.google.accounts) {
        clearInterval(interval);
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleResponse,
        });
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          theme: "outline",
          size: "large",
          width: "400",
          text: "continue_with",
        });
      }
    }, 200);
    return () => clearInterval(interval);
  }, [handleGoogleResponse]);

  return (
    <div className="bg-slate-50 min-h-screen flex items-center justify-center p-4 font-sans">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-xl overflow-hidden">
        <div className="p-8 md:p-12 flex flex-col justify-center">
          <div className="max-w-md mx-auto w-full">

            {/* Header */}
            <div className="mb-10 text-center">
              <h2 className="text-2xl font-bold text-slate-900">
                Welcome to AuditHawk
              </h2>
              <p className="text-slate-500 mt-2">
                Professional financial monitoring and fraud intelligence.
              </p>
            </div>

            {/* Tabs */}
            <div className="flex p-1 bg-slate-100 rounded-lg mb-8">
              <button
                onClick={() => { setIsLogin(true); setError(""); }}
                className={`flex-1 py-2.5 text-sm font-semibold rounded-md transition-all ${
                  isLogin
                    ? "bg-white text-[#1152d4] shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Login
              </button>

              <button
                onClick={() => { setIsLogin(false); setError(""); }}
                className={`flex-1 py-2.5 text-sm font-semibold rounded-md transition-all ${
                  !isLogin
                    ? "bg-white text-[#1152d4] shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Sign Up
              </button>
            </div>

            {/* Error message */}
            {error && (
              <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="auditor@company.com"
                  className="w-full px-4 py-3 border border-slate-200 rounded-lg bg-slate-50 focus:ring-2 focus:ring-[#1152d4] outline-none transition-all"
                />
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Password
                  </label>
                </div>

                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 border border-slate-200 rounded-lg bg-slate-50 focus:ring-2 focus:ring-[#1152d4] outline-none transition-all"
                />
              </div>

              {/* Confirm Password (Only Signup) */}
              {!isLogin && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 border border-slate-200 rounded-lg bg-slate-50 focus:ring-2 focus:ring-[#1152d4] outline-none transition-all"
                  />
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#1152d4] hover:bg-[#0e44b3] disabled:opacity-60 text-white font-semibold py-3.5 rounded-lg shadow-lg shadow-blue-500/20 transition-all"
              >
                {loading ? "Please wait…" : isLogin ? "Sign In" : "Create Account"}
              </button>
            </form>

            {/* Divider */}
            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-slate-500">
                  Or sign in with
                </span>
              </div>
            </div>

            {/* Google Button – rendered by Google Identity SDK */}
            <div ref={googleBtnRef} className="flex justify-center" />
            {!GOOGLE_CLIENT_ID && (
              <p className="text-xs text-center text-slate-400 mt-2">
                Google sign-in requires REACT_APP_GOOGLE_CLIENT_ID in .env
              </p>
            )}

          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
