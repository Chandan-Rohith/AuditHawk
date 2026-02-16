import React, { useState, useRef } from "react";
import AppNavbar from "../components/AppNavbar";
import Dashboard from "../components/Dashboard";
import UploadModal from "../components/UploadModal";
import HistoryPage from "../components/HistoryPage";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

const MainPage = () => {
  const [showUpload, setShowUpload] = useState(false);

  // Core audit state
  const [transactions, setTransactions] = useState([]);
  const [frauds, setFrauds] = useState([]);
  const [riskScore, setRiskScore] = useState(0);

  const [history, setHistory] = useState([]);
  const [activeView, setActiveView] = useState("dashboard");
  const [selectedSession, setSelectedSession] = useState(null);

  const dashboardRef = useRef(null);

  /* ============================= */
  /*        FRAUD ACTIONS          */
  /* ============================= */

  const handleAccept = (id) => {
    setFrauds(prev =>
      prev.map(tx =>
        tx.id === id ? { ...tx, status: "accepted" } : tx
      )
    );
  };

  const handleReject = (id) => {
    setFrauds(prev =>
      prev.map(tx =>
        tx.id === id ? { ...tx, status: "rejected" } : tx
      )
    );
  };

  /* ============================= */
  /*        MOCK ANALYSIS          */
  /* ============================= */

  const handleAnalysis = (threshold) => {
    const mockTransactions = Array.from({ length: 20 }, (_, i) => {
      const amount = Math.floor(Math.random() * 10000);
      const mlRisk = Math.random();

      const ruleBased = amount > threshold;
      const mlBased = mlRisk > 0.75;

      let reason = "";
      if (ruleBased && mlBased) reason = "Both Flags";
      else if (ruleBased) reason = "Rule-Based";
      else if (mlBased) reason = "ML-Based";

      return {
        id: i + 1,
        amount,
        mlRisk,
        flagged: ruleBased || mlBased,
        reason,
        status: "pending",
      };
    });

    const flagged = mockTransactions.filter(tx => tx.flagged);
    const risk = Math.round((flagged.length / mockTransactions.length) * 100);

    const session = {
      id: Date.now(),
      fileName: "transactions.csv",
      date: new Date().toLocaleDateString(),
      transactions: mockTransactions,
      frauds: flagged,
      riskScore: risk,
    };

    setTransactions(mockTransactions);
    setFrauds(flagged);
    setRiskScore(risk);
    setHistory(prev => [session, ...prev]);

    setSelectedSession(session);
    setActiveView("session");
    setShowUpload(false);
  };

  /* ============================= */
  /*        PDF DOWNLOAD           */
  /* ============================= */

  const handleDownloadPDF = async () => {
    if (!dashboardRef.current) return;

    const canvas = await html2canvas(dashboardRef.current);
    const imgData = canvas.toDataURL("image/png");

    const pdf = new jsPDF("p", "mm", "a4");

    const imgWidth = 210;
    const pageHeight = 295;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    let heightLeft = imgHeight;
    let position = 0;

    pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;

    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }

    const fileName = selectedSession?.fileName || "Audit_Report";
    pdf.save(`${fileName}_dashboard.pdf`);
  };

  return (
    <div className="min-h-screen bg-[#f6f6f8]">

      <AppNavbar
        setActiveView={(view) => {
          setActiveView(view);
          setSelectedSession(null);
        }}
        onUploadClick={() => setShowUpload(true)}
      />

      <main className="max-w-7xl mx-auto px-6 py-8">

        {/* DASHBOARD VIEW */}
        {activeView === "dashboard" && (
          <Dashboard
            transactions={transactions}
            frauds={frauds}
            riskScore={riskScore}
            onUploadClick={() => setShowUpload(true)}
            onAccept={handleAccept}
            onReject={handleReject}
          />
        )}

        {/* HISTORY VIEW */}
        {activeView === "history" && (
          <HistoryPage
            history={history}
            onSelectSession={(session) => {
              setTransactions(session.transactions);
              setFrauds(session.frauds);
              setRiskScore(session.riskScore);
              setSelectedSession(session);
              setActiveView("session");
            }}
          />
        )}

        {/* SESSION VIEW */}
        {activeView === "session" && selectedSession && (
          <div>

            {/* Breadcrumb + Download */}
            <div className="flex justify-between items-center mb-6">

              <div className="flex items-center gap-2 text-sm">
                <button
                  onClick={() => setActiveView("history")}
                  className="text-[#1152d4] hover:underline"
                >
                  History
                </button>
                <span className="text-gray-400">›</span>
                <span className="font-semibold text-gray-700">
                  {selectedSession.fileName}
                </span>
              </div>

              <button
                onClick={handleDownloadPDF}
                className="bg-[#1152d4] text-white px-5 py-2 rounded-lg font-semibold shadow hover:bg-blue-700 transition"
              >
                Download Dashboard
              </button>

            </div>

            {/* Wrapped Dashboard for PDF */}
            <div ref={dashboardRef}>
              <Dashboard
                transactions={transactions}
                frauds={frauds}
                riskScore={riskScore}
                onAccept={handleAccept}
                onReject={handleReject}
                hideUploadButton
                hideDownloadButton
              />
            </div>

          </div>
        )}

      </main>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onAnalyze={handleAnalysis}
        />
      )}

    </div>
  );
};

export default MainPage;
