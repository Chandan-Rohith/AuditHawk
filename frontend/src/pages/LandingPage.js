import React from "react";
import { useNavigate } from "react-router-dom";

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="bg-[#f6f6f8] text-[#0d121b] font-sans min-h-screen">

      {/* Navbar */}
      <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 flex h-16 items-center justify-between">
          
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="text-2xl font-extrabold tracking-tight">
              AuditHawk
            </span>
          </div>

          {/* Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/auth")}
              className="px-4 py-2 text-sm font-bold text-gray-800 hover:bg-blue-50 rounded-lg transition-all"
            >
              Login
            </button>

            <button
              onClick={() => navigate("/auth")}
              className="bg-[#1152d4] hover:bg-[#0e44b3] text-white px-5 py-2 text-sm font-bold rounded-lg shadow-lg shadow-blue-500/20 transition-all"
            >
              Signup
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-6 flex flex-col lg:flex-row items-center gap-16">

          {/* Left Content */}
          <div className="flex-1 lg:pr-12 text-center lg:text-left">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black leading-tight mb-6">
              AuditHawk: Intelligent{" "}
              <span className="text-[#1152d4]">Fraud Detection</span> &{" "}
              Financial Auditing
            </h1>

            <p className="text-lg lg:text-xl text-gray-600 leading-relaxed max-w-xl mx-auto lg:mx-0">
              Leverage batch processing, mock ML risk scoring, and rule-based
              detection to secure your transactions with Explainable AI
              transparency.
            </p>
          </div>

          {/* Right Mock Dashboard */}
          <div className="flex-1 w-full max-w-[600px]">
            <div className="relative rounded-2xl border border-gray-200 bg-white shadow-2xl overflow-hidden">

              {/* Browser Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-400"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                  <div className="w-3 h-3 rounded-full bg-green-400"></div>
                </div>
                <span className="text-xs text-gray-500 font-mono">
                  audithawk-dashboard-v1.0
                </span>
              </div>

              {/* Dashboard Content */}
              <div className="p-6 space-y-4">
                <div className="h-10 bg-blue-100 rounded animate-pulse"></div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="h-24 bg-green-100 rounded-lg"></div>
                  <div className="h-24 bg-red-100 rounded-lg"></div>
                  <div className="h-24 bg-yellow-100 rounded-lg"></div>
                </div>

                <div className="flex items-center justify-center h-40 bg-blue-50 rounded-lg border border-dashed border-blue-200">
                  <svg
                    className="w-14 h-14 text-[#1152d4]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6m4 0a2 2 0 002 2h2a2 2 0 002-2m-6 0V9a2 2 0 012-2h2a2 2 0 012 2v10m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Background Blur Decorations */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-blue-200/20 rounded-full blur-3xl -z-10"></div>
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-blue-200/20 rounded-full blur-3xl -z-10"></div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <h2 className="text-[#1152d4] font-bold uppercase text-xs tracking-widest mb-3">
            Enterprise Grade
          </h2>

          <h3 className="text-3xl md:text-4xl font-black mb-6">
            Advanced Financial Security
          </h3>

          <p className="text-gray-500 max-w-2xl mx-auto mb-14">
            Comprehensive tools designed for deep transparency and real-time
            protection across your entire financial ecosystem.
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <FeatureCard
              title="Fraud Detection"
              desc="Advanced ML models combined with custom rules for precise threat identification and real-time intervention."
            />
            <FeatureCard
              title="Risk Scoring"
              desc="Real-time analysis and numerical scoring of transaction risks to prioritize reviews and automate approvals."
            />
            <FeatureCard
              title="Explainable AI (XAI)"
              desc="Understand the reasoning behind every flag with transparent model interpretation and feature importance mapping."
            />
            <FeatureCard
              title="Audit Workflow"
              desc="Seamlessly review, manage, and resolve suspicious transactions in an optimized interface."
            />
          </div>
        </div>
      </section>
    </div>
  );
};

const FeatureCard = ({ title, desc }) => (
  <div className="group p-8 rounded-2xl border border-gray-200 bg-white hover:border-blue-300 hover:shadow-xl transition-all">
    <h4 className="text-lg font-bold mb-3">{title}</h4>
    <p className="text-sm text-gray-600 leading-relaxed">{desc}</p>
  </div>
);

export default LandingPage;
