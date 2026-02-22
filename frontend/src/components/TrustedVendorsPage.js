import React, { useState } from "react";

const TrustedVendorsPage = ({ vendors, onAddVendor, onRemoveVendor }) => {
  const [newVendor, setNewVendor] = useState("");

  const handleAdd = () => {
    const name = newVendor.trim();
    if (!name) return;
    if (vendors.some(v => v.toLowerCase() === name.toLowerCase())) {
      alert("This vendor is already in the trusted list.");
      return;
    }
    onAddVendor(name);
    setNewVendor("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleAdd();
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-extrabold">Trusted Vendors</h2>
        <p className="text-gray-500 mt-1">
          Transactions from trusted vendors will not be flagged during analysis.
        </p>
      </div>

      {/* Add Vendor */}
      <div className="bg-white rounded-xl border shadow-sm p-6 mb-8">
        <h3 className="font-bold mb-4">Add a Vendor</h3>
        <div className="flex gap-3">
          <input
            type="text"
            value={newVendor}
            onChange={(e) => setNewVendor(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter vendor name..."
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1152d4] focus:border-transparent"
          />
          <button
            onClick={handleAdd}
            className="bg-[#1152d4] hover:bg-[#0e44b3] text-white px-6 py-2.5 rounded-lg font-bold text-sm shadow-lg transition-all"
          >
            Add Vendor
          </button>
        </div>
      </div>

      {/* Vendor List */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b bg-gray-50 flex justify-between items-center">
          <h3 className="font-bold">Vendor List</h3>
          <span className="text-xs font-bold text-[#1152d4] uppercase">
            {vendors.length} {vendors.length === 1 ? "Vendor" : "Vendors"}
          </span>
        </div>

        {vendors.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full border-4 border-dashed border-gray-200 flex items-center justify-center">
              <span className="text-3xl text-gray-300">🏪</span>
            </div>
            <h3 className="text-lg font-bold mb-2 text-gray-700">No Trusted Vendors</h3>
            <p className="text-gray-500 text-sm">
              Add vendors above to whitelist them from fraud flagging.
            </p>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase font-bold text-gray-500">
              <tr>
                <th className="px-6 py-3">#</th>
                <th className="px-6 py-3">Vendor Name</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {vendors.map((vendor, idx) => (
                <tr key={vendor} className="border-t hover:bg-gray-50">
                  <td className="px-6 py-4 text-gray-400 font-mono">{idx + 1}</td>
                  <td className="px-6 py-4 font-semibold">{vendor}</td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => onRemoveVendor(vendor)}
                      className="px-3 py-1 border border-red-200 text-red-500 rounded text-xs font-bold hover:bg-red-50 transition-colors"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default TrustedVendorsPage;
