import React from "react";

const HistoryPage = ({ history, onSelectSession }) => {
  return (
    <div className="max-w-7xl mx-auto">

      {/* Page Header */}
      <div className="flex flex-wrap justify-between items-end gap-6 mb-10">
        <div>
          <h1 className="text-4xl font-black text-[#0d121b]">
            Audit History
          </h1>
          <p className="text-gray-500 mt-2">
            Review and manage your past audit reports and flagged transactions.
          </p>
        </div>
      </div>

      {/* Empty State */}
      {history.length === 0 ? (
        <div className="flex flex-col items-center justify-center mt-24 text-gray-400">
          <div className="text-6xl mb-4">📂</div>
          <p className="text-lg font-medium">No audit history yet</p>
          <p className="text-sm mt-1">
            Upload and analyze transactions to see results here.
          </p>
        </div>
      ) : (
        /* History Grid */
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {history.map((session) => (
            <div
              key={session.id}
              onClick={() => onSelectSession(session)}
              className="group bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-lg hover:border-[#1152d4]/40 transition-all cursor-pointer"
            >
              {/* Top Section */}
              <div className="flex justify-between items-center mb-4">
                <div className="bg-[#1152d4]/10 p-2 rounded-lg">
                  <span className="text-[#1152d4] text-sm font-bold">
                    CSV
                  </span>
                </div>
                <span className="text-xs text-gray-400">
                  {session.date}
                </span>
              </div>

              {/* File Name */}
              <h3 className="font-bold text-[#0d121b] truncate group-hover:text-[#1152d4] transition-colors">
                {session.fileName}
              </h3>

              {/* Metrics */}
              <div className="mt-6 space-y-4">

                {/* Fraud Count */}
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500">
                    Fraud Count
                  </span>
                  <span
                    className={`font-semibold px-2 py-0.5 rounded ${
                      session.frauds.length > 0
                        ? "bg-red-50 text-red-600"
                        : "bg-green-50 text-green-600"
                    }`}
                  >
                    {session.frauds.length} Flagged
                  </span>
                </div>

                {/* Risk Score */}
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-500">
                      Risk Score
                    </span>
                    <span className="font-bold text-[#1152d4]">
                      {session.riskScore}%
                    </span>
                  </div>

                  <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-[#1152d4] h-full transition-all duration-500"
                      style={{
                        width: `${session.riskScore}%`,
                      }}
                    />
                  </div>
                </div>

              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryPage;
