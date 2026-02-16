import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    // Dummy login - just navigate to app
    navigate("/app");
  };

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
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-2.5 text-sm font-semibold rounded-md transition-all ${
                  isLogin
                    ? "bg-white text-[#1152d4] shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Login
              </button>

              <button
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-2.5 text-sm font-semibold rounded-md transition-all ${
                  !isLogin
                    ? "bg-white text-[#1152d4] shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Sign Up
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
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
                  {isLogin && (
                    <span className="text-xs font-semibold text-[#1152d4] cursor-pointer">
                      Forgot password?
                    </span>
                  )}
                </div>

                <input
                  type="password"
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
                    placeholder="••••••••"
                    className="w-full px-4 py-3 border border-slate-200 rounded-lg bg-slate-50 focus:ring-2 focus:ring-[#1152d4] outline-none transition-all"
                  />
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                className="w-full bg-[#1152d4] hover:bg-[#0e44b3] text-white font-semibold py-3.5 rounded-lg shadow-lg shadow-blue-500/20 transition-all"
              >
                {isLogin ? "Sign In" : "Create Account"}
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

            {/* Google Button */}
            <button className="w-full py-3 border border-slate-200 rounded-lg hover:bg-slate-50 transition-all text-slate-700 text-sm font-medium">
              Google
            </button>

          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
