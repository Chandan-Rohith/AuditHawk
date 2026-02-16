import React, { useState } from "react";

const UploadModal = ({ onClose, onAnalyze }) => {
  const [threshold, setThreshold] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file);
    } else {
      alert("Please select a valid CSV file.");
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file);
    } else {
      alert("Please select a valid CSV file.");
    }
  };

  const handleSubmit = () => {
    if (!selectedFile) {
      alert("Please upload a CSV file.");
      return;
    }

    if (!threshold || threshold <= 0) {
      alert("Please enter a valid threshold value.");
      return;
    }

    onAnalyze(Number(threshold), selectedFile);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm bg-black/10 p-4">
      <div className="bg-white w-full max-w-xl rounded-xl shadow-2xl border overflow-hidden">

        {/* Header */}
        <div className="px-8 pt-8 pb-4 border-b flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">
              Upload Transactions
            </h2>
            <p className="text-gray-500 text-sm mt-1">
              Prepare your data for automated auditing.
            </p>
          </div>
          <button onClick={onClose}>✕</button>
        </div>

        {/* Body */}
        <div className="p-8 space-y-8">

          {/* File Upload Area */}
          <div>
            <label className="text-sm font-bold block mb-2">
              Upload CSV File *
            </label>
            
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
                isDragging 
                  ? 'border-blue-500 bg-blue-100' 
                  : selectedFile 
                    ? 'border-green-500 bg-green-50' 
                    : 'border-blue-200 bg-blue-50 hover:border-blue-400'
              }`}
              onClick={() => document.getElementById('file-input').click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {selectedFile ? (
                <div>
                  <div className="text-5xl mb-3">📄</div>
                  <p className="text-lg font-bold text-green-700">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                    }}
                    className="mt-3 text-sm text-red-600 hover:underline"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div>
                  <div className="text-5xl mb-3">📁</div>
                  <p className="text-lg font-bold text-[#1152d4] mb-2">
                    Click to browse or drag & drop
                  </p>
                  <p className="text-sm text-gray-500">
                    Accepts CSV files only
                  </p>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="text-sm font-bold">
              Maximum Transaction Amount Threshold *
            </label>

            <input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              placeholder="e.g. 5000"
              className="w-full mt-2 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-[#1152d4] outline-none"
            />

            <p className="text-sm text-blue-600 mt-2">
              Transactions exceeding this value will be flagged.
            </p>
          </div>

        </div>

        {/* Footer */}
        <div className="px-8 py-6 bg-gray-50 border-t flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-500"
          >
            Cancel
          </button>

          <button
            onClick={handleSubmit}
            className="px-8 py-2 bg-[#1152d4] text-white font-bold rounded-lg shadow-lg"
          >
            Analyze Transactions
          </button>
        </div>

      </div>
    </div>
  );
};

export default UploadModal;
