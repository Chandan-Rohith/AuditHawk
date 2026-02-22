import React from "react";
import { useNavigate } from "react-router-dom";

const AppNavbar = ({ setActiveView, onUploadClick }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/auth");
  };

  return (
    <header className="bg-white border-b border-primary/10 px-8 py-4 flex justify-between items-center">

      {/* Logo */}
      <h1
        onClick={() => setActiveView("dashboard")}
        className="text-xl font-bold text-[#1152d4] cursor-pointer"
      >
        AuditHawk
      </h1>

      {/* Navigation */}
      <div className="flex gap-8 text-sm font-semibold items-center">

        {/* History */}
        <button
          onClick={() => setActiveView("history")}
          className="hover:text-[#1152d4] transition-colors"
        >
          History
        </button>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="text-red-500 hover:text-red-700 transition-colors"
        >
          Logout
        </button>

      </div>

    </header>
  );
};

export default AppNavbar;

