import React, { useState, useRef } from "react";
import AppNavbar from "../components/AppNavbar";
import Dashboard from "../components/Dashboard";
import UploadModal from "../components/UploadModal";
import HistoryPage from "../components/HistoryPage";
import TrustedVendorsPage from "../components/TrustedVendorsPage";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

const MainPage = () => {
  const [showUpload, setShowUpload] = useState(false);

  // Core audit state
  const [transactions, setTransactions] = useState([]);
  const [frauds, setFrauds] = useState([]);
  const [riskScore, setRiskScore] = useState(0);

  const [history, setHistory] = useState([]);
  const [trustedVendors, setTrustedVendors] = useState([]);
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
  /*     REAL CSV ANALYSIS         */
  /* ============================= */

  const handleAnalysis = async (threshold, file) => {
    if (!file) {
      alert("No file provided.");
      return;
    }

    try {
      const csvText = await file.text();
      const lines = csvText.trim().split("\n");
      if (lines.length < 2) {
        alert("CSV file is empty or has no data rows.");
        return;
      }

      const headers = lines[0].split(",").map(h => h.trim().toLowerCase());
      const amountIdx = headers.indexOf("amount");
      const txnIdIdx = headers.indexOf("transaction_id");
      const merchantIdx = headers.indexOf("merchant");
      const categoryIdx = headers.indexOf("category");
      const dateIdx = headers.indexOf("date");
      const accountIdx = headers.indexOf("account_id");

      if (amountIdx === -1 || txnIdIdx === -1) {
        alert("CSV must contain at least 'transaction_id' and 'amount' columns.");
        return;
      }

      const parsedTransactions = lines.slice(1).map((line, i) => {
        const cols = line.split(",").map(c => c.trim());
        const amount = parseFloat(cols[amountIdx]) || 0;
        const merchant = merchantIdx !== -1 ? cols[merchantIdx] : "";
        const isTrusted = trustedVendors.some(
          v => v.toLowerCase() === merchant.toLowerCase()
        );
        const flagged = !isTrusted && amount > threshold;

        return {
          id: i + 1,
          transaction_id: cols[txnIdIdx] || `TX-${i + 1}`,
          date: dateIdx !== -1 ? cols[dateIdx] : "",
          amount,
          merchant,
          category: categoryIdx !== -1 ? cols[categoryIdx] : "",
          account_id: accountIdx !== -1 ? cols[accountIdx] : "",
          mlRisk: 0, // ML not wired yet
          flagged,
          reason: flagged ? "Exceeds Threshold" : isTrusted ? "Trusted Vendor" : "",
          status: "pending",
        };
      });

      const flagged = parsedTransactions.filter(tx => tx.flagged);
      const risk = parsedTransactions.length
        ? Math.round((flagged.length / parsedTransactions.length) * 100)
        : 0;

      const session = {
        id: Date.now(),
        fileName: file.name,
        date: new Date().toLocaleDateString(),
        transactions: parsedTransactions,
        frauds: flagged,
        riskScore: risk,
      };

      setTransactions(parsedTransactions);
      setFrauds(flagged);
      setRiskScore(risk);
      setHistory(prev => [session, ...prev]);

      setSelectedSession(null);
      setActiveView("dashboard");
      setShowUpload(false);
    } catch (err) {
      console.error("CSV parsing error:", err);
      alert("Failed to parse the CSV file. Please check the format.");
    }
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
          if (view === "dashboard") {
            setTransactions([]);
            setFrauds([]);
            setRiskScore(0);
          }
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

        {/* TRUSTED VENDORS VIEW */}
        {activeView === "vendors" && (
          <TrustedVendorsPage
            vendors={trustedVendors}
            onAddVendor={(name) => setTrustedVendors(prev => [...prev, name])}
            onRemoveVendor={(name) => setTrustedVendors(prev => prev.filter(v => v !== name))}
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
