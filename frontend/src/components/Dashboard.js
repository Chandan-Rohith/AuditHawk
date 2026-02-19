import React from "react";
import { Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

const Dashboard = ({
  transactions,
  frauds,
  riskScore,
  onUploadClick,
  onAccept,
  onReject,
  hideDownloadButton = false,
}) => {
  const total = transactions.length;
  const fraudCount = frauds.filter(f => f.status !== "rejected").length;
  const legitCount = total - fraudCount;

  if (total === 0) {
    return (
      <div>
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-extrabold">
            Dashboard
          </h2>
          <p className="text-gray-500 mt-1">
            Real-time fraud detection and transaction analysis.
          </p>
        </div>

        {/* Metrics */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">
          <MetricCard title="Total Transactions" value="0" />
          <MetricCard title="Fraud Count" value="0" />
          <MetricCard title="Risk Score" value="0%" />
        </div>

        {/* Empty State */}
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 bg-white rounded-xl border p-12 text-center shadow-sm">
            <div className="mb-6">
              <div className="w-40 h-40 mx-auto rounded-full border-4 border-dashed border-gray-200 flex items-center justify-center">
                <span className="text-5xl text-gray-300">⬆</span>
              </div>
            </div>

            <h3 className="text-2xl font-bold mb-3">
              No Data Uploaded Yet
            </h3>

            <p className="text-gray-500 mb-6">
              Get started by importing your transaction records
              for automated fraud detection.
            </p>

            <button
              onClick={onUploadClick}
              className="bg-[#1152d4] hover:bg-[#0e44b3] text-white font-bold py-3 px-8 rounded-lg shadow-lg"
            >
              Upload CSV to start analysis
            </button>
          </div>

          <div className="bg-white rounded-xl border p-8 shadow-sm">
            <h4 className="text-lg font-bold mb-6">
              Visual Summary
            </h4>

            <div className="h-64 flex items-center justify-center text-gray-400">
              No Data Available
            </div>
          </div>
        </div>
      </div>
    );
  }

  const chartData = {
    labels: ["Legitimate", "Flagged"],
    datasets: [
      {
        data: [legitCount, fraudCount],
        backgroundColor: ["#1152d4", "#ef4444"],
        borderWidth: 0,
      },
    ],
  };

  return (
    <div className="space-y-8">

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black">
            Post-Analysis Dashboard
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Audit complete for current session
          </p>
        </div>

        {!hideDownloadButton && (
          <button className="bg-[#1152d4] text-white px-5 py-2 rounded-lg font-bold shadow-lg">
            Download Dashboard
          </button>
        )}
      </div>

      {/* Metrics */}
      <div className="grid md:grid-cols-3 gap-6">
        <MetricCard title="Total Transactions" value={total} />
        <MetricCard title="Fraud Count" value={fraudCount} highlight="red" />
        <MetricCard title="Risk Score" value={`${riskScore}%`} highlight="amber" />
      </div>

      {/* Middle Section */}
      <div className="grid lg:grid-cols-3 gap-6">

        {/* Pie Chart */}
        <div className="bg-white p-6 rounded-xl border shadow-sm">
          <h3 className="font-bold mb-4">Transaction Integrity</h3>
          <Doughnut data={chartData} />
        </div>

        {/* Summary */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border shadow-sm">
          <h3 className="font-bold mb-3">Analysis Summary</h3>
          <p className="text-gray-600 text-sm">
            AuditHawk processed the dataset using hybrid detection.
            High-value segments triggered rule-based alerts while
            ML logic detected behavioral irregularities.
          </p>

          <div className="grid grid-cols-2 gap-4 mt-6">
            <InfoBox
              label="Top Logic Signal"
              value="Hybrid ML + Threshold"
            />
            <InfoBox
              label="Avg Flag Value"
              value={`$${Math.round(
                frauds.reduce((sum, f) => sum + f.amount, 0) /
                  (fraudCount || 1)
              )}`}
            />
          </div>
        </div>
      </div>

      {/* Fraud Table */}
      <FraudTable
        frauds={frauds}
        onAccept={onAccept}
        onReject={onReject}
      />

    </div>
  );
};

const MetricCard = ({ title, value, highlight }) => {
  const color =
    highlight === "red"
      ? "text-red-600"
      : highlight === "amber"
      ? "text-amber-600"
      : "text-[#1152d4]";

  return (
    <div className="bg-white p-6 rounded-xl border shadow-sm">
      <p className="text-xs font-bold text-gray-500 uppercase mb-1">
        {title}
      </p>
      <h3 className={`text-3xl font-black ${color}`}>
        {value}
      </h3>
    </div>
  );
};

const InfoBox = ({ label, value }) => (
  <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
    <p className="text-xs font-bold uppercase text-blue-600 mb-1">
      {label}
    </p>
    <p className="text-sm font-bold text-gray-800">
      {value}
    </p>
  </div>
);

const FraudTable = ({ frauds, onAccept, onReject }) => (
  <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
    <div className="px-6 py-4 border-b bg-gray-50 flex justify-between">
      <h3 className="font-bold">Fraud Review Queue</h3>
      <span className="text-xs font-bold text-[#1152d4] uppercase">
        {frauds.length} Items Pending
      </span>
    </div>

    <table className="w-full text-left text-sm">
      <thead className="bg-gray-50 text-xs uppercase font-bold text-gray-500">
        <tr>
          <th className="px-6 py-3">Transaction</th>
          <th className="px-6 py-3">Merchant</th>
          <th className="px-6 py-3">Amount</th>
          <th className="px-6 py-3">Category</th>
          <th className="px-6 py-3">Reason</th>
          <th className="px-6 py-3 text-right">Actions</th>
        </tr>
      </thead>

      <tbody>
        {frauds.map(tx => (
          <tr key={tx.id} className="border-t hover:bg-gray-50">
            <td className="px-6 py-4 font-mono">
              {tx.transaction_id || `TX-${tx.id}`}
            </td>

            <td className="px-6 py-4">
              {tx.merchant || "—"}
            </td>

            <td className="px-6 py-4 font-bold">
              ${tx.amount}
            </td>

            <td className="px-6 py-4 text-xs">
              {tx.category || "—"}
            </td>

            <td className="px-6 py-4 text-xs text-blue-600">
              {tx.reason}
            </td>

            <td className="px-6 py-4 text-right space-x-2">
              <button
                onClick={() => onAccept(tx.id)}
                className="px-3 py-1 bg-[#1152d4] text-white rounded text-xs font-bold"
              >
                Accept
              </button>

              <button
                onClick={() => onReject(tx.id)}
                className="px-3 py-1 border text-gray-600 rounded text-xs font-bold"
              >
                Reject
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export default Dashboard;
