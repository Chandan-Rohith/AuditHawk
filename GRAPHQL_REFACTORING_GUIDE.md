# AuditHawk: GraphQL-Only Refactoring Guide

## 📋 Overview
AuditHawk has been refactored to use **GraphQL exclusively** for all API interactions. All REST endpoints have been removed per faculty requirements.

---

## 🔄 What Changed

### **Before (REST + GraphQL Hybrid)**
- REST endpoint: `POST /api/upload-csv/` for file uploads
- REST endpoint: `GET /api/health/` for health checks
- GraphQL for queries only
- views.py contained REST API logic

### **After (GraphQL Only)**
- ✅ Single GraphQL endpoint: `/graphql/`
- ✅ All operations (queries, mutations) through GraphQL
- ✅ CSV upload via GraphQL mutation
- ✅ No REST endpoints
- ✅ No Django REST Framework

---

## 📁 Files Modified

### 1. **`backend/api/schema.py`** ✅ UPDATED
**Changes:**
- Imported `csv_parser` module
- Updated `UploadAuditFile` mutation:
  - Added `csv_content` argument (accepts entire CSV as string)
  - Parses CSV using `csv_parser.py`
  - Validates data and handles errors
  - Stores transactions in `MOCK_TRANSACTIONS`
  - Returns detailed success/error messages

### 2. **`backend/audithawk_core/urls.py`** ✅ CLEANED
**Changes:**
- Removed REST API routes (`/api/upload-csv/`, `/api/health/`)
- Removed `from api import views` import
- Only GraphQL and admin routes remain
- Added clear comments about GraphQL-only architecture

### 3. **`backend/api/views.py`** ✅ DEPRECATED
**Changes:**
- Removed all REST endpoint functions
- Replaced with note explaining GraphQL-only architecture
- Can be safely deleted (kept for documentation)

### 4. **`test_upload.py`** ✅ UPDATED
**Changes:**
- Replaced REST API calls with GraphQL mutation
- Uses `requests` to POST GraphQL query
- Reads CSV file and sends content as string
- Demonstrates proper GraphQL mutation usage

### 5. **`CSV_UPLOAD_GUIDE.md`** ⚠️ NEEDS UPDATE
**Action:** Can be deleted or updated with GraphQL examples

---

## 🚀 How to Use GraphQL CSV Upload

### **Method 1: GraphQL Playground (Manual Testing)**

1. Start Django server:
   ```powershell
   python manage.py runserver
   ```

2. Go to: `http://127.0.0.1:8000/graphql/`

3. Copy your CSV content, then run this mutation:
   ```graphql
   mutation {
     uploadAuditFile(
       fileName: "my_transactions.csv"
       csvContent: """transaction_id,date,amount,merchant,category,account_id
TXN-001,2026-02-01T10:00:00,500.00,Amazon,Shopping,ACC-001
TXN-002,2026-02-01T11:00:00,1500.00,Apple,Electronics,ACC-002"""
     ) {
       success
       message
       report {
         id
         fileName
         uploadedAt
         totalTransactions
         flaggedCount
         status
       }
     }
   }
   ```

### **Method 2: Python Script (Automated Testing)**

Run the updated test script:
```powershell
python test_upload.py
```

This will:
- Read `sample_transactions.csv`
- Send it via GraphQL mutation
- Display report details

### **Method 3: Frontend Integration**

Use any GraphQL client library (Apollo, urql, etc.):

```javascript
const UPLOAD_CSV = gql`
  mutation UploadCSV($fileName: String!, $csvContent: String!) {
    uploadAuditFile(fileName: $fileName, csvContent: $csvContent) {
      success
      message
      report {
        id
        fileName
        totalTransactions
      }
    }
  }
`;

// In your component:
const [uploadCSV] = useMutation(UPLOAD_CSV);

const handleUpload = async (file) => {
  const csvContent = await file.text();
  
  const { data } = await uploadCSV({
    variables: {
      fileName: file.name,
      csvContent: csvContent
    }
  });
  
  if (data.uploadAuditFile.success) {
    console.log("Uploaded:", data.uploadAuditFile.report);
  }
};
```

---

## 🗂️ Complete GraphQL Schema

### **Queries**
```graphql
{
  # List all audit reports
  auditReports {
    id
    fileName
    uploadedAt
    totalTransactions
    flaggedCount
    status
  }
  
  # Get all transactions for a report
  transactions(reportId: "1") {
    id
    transactionId
    date
    amount
    merchant
    category
    accountId
  }
  
  # Get flagged (suspicious) transactions
  flaggedTransactions(reportId: "1") {
    id
    transactionId
    amount
    riskScore
    decision
    explanation
  }
}
```

### **Mutations**
```graphql
mutation {
  # Upload CSV file (NEW - GraphQL only)
  uploadAuditFile(
    fileName: "transactions.csv"
    csvContent: "transaction_id,date,amount,..."
  ) {
    success
    message
    report {
      id
      fileName
      totalTransactions
    }
  }
  
  # Update decision on flagged transaction
  updateTransactionDecision(
    reportId: "1"
    transactionId: "TXN-123"
    decision: "approved"
  ) {
    success
    message
    transaction {
      transactionId
      decision
    }
  }
}
```

---

## ✅ Testing Checklist

### **1. Server Status**
```bash
python manage.py runserver
# Should start without errors
# Only /graphql/ and /admin/ endpoints
```

### **2. GraphQL Interface**
- Go to `http://127.0.0.1:8000/graphql/`
- GraphiQL playground should load
- Test: `{ hello }`
- Should return: `"Hello AuditHawk!"`

### **3. CSV Upload**
```bash
python test_upload.py
# Should show: ✅ CSV uploaded successfully via GraphQL!
```

### **4. Query Uploaded Data**
```graphql
{
  auditReports {
    id
    fileName
    totalTransactions
  }
}
# Should include newly uploaded report
```

### **5. View Transactions**
```graphql
{
  transactions(reportId: "4") {  # Use new report ID
    transactionId
    amount
    merchant
  }
}
# Should show all 10 transactions from sample CSV
```

---

## 🧹 Files You Can Delete

### **Safe to Delete:**
1. ❌ `backend/api/views.py` - No longer used (already cleaned)
2. ❌ `CSV_UPLOAD_GUIDE.md` - REST-focused (outdated)

### **Keep These:**
1. ✅ `backend/api/schema.py` - Core GraphQL schema
2. ✅ `backend/api/csv_parser.py` - Used by GraphQL mutation
3. ✅ `backend/audithawk_core/urls.py` - GraphQL routing
4. ✅ `sample_transactions.csv` - Test data
5. ✅ `test_upload.py` - GraphQL upload test

---

## 🎓 Faculty Explanation Points

### **Why GraphQL Only?**
1. **Single Endpoint:** Simpler architecture, easier to secure
2. **Type Safety:** GraphQL schema validates all data
3. **Flexible Queries:** Frontend requests exactly what it needs
4. **Better Documentation:** Self-documenting via GraphQL introspection
5. **Industry Standard:** Modern API design pattern

### **How CSV Upload Works (GraphQL)**
1. Frontend reads CSV file as text
2. Sends text content via GraphQL mutation
3. Backend receives string, parses with `csv_parser.py`
4. Validates columns and data types
5. Stores in memory (later: database)
6. Returns report with transaction count

### **Error Handling**
- Invalid CSV format → GraphQL returns `success: false` with error message
- Missing columns → Detailed validation error
- Parse errors → Clear error description
- All errors returned in GraphQL response (no HTTP error codes)

---

## 🔜 Next Steps

### **Immediate:**
1. Test CSV upload via GraphQL ✅
2. Verify transactions are queryable ✅
3. Test error handling (invalid CSV) ✅

### **Future Enhancements:**
1. Add ML fraud detection (Isolation Forest)
2. Generate SHAP explanations
3. Replace in-memory storage with MongoDB
4. Add user authentication (GraphQL mutations)
5. Build React frontend with Apollo Client

---

## 📞 Support

**Testing Issues?**
```bash
# Restart server
python manage.py runserver

# Check GraphQL endpoint
curl http://127.0.0.1:8000/graphql/

# Run test script
python test_upload.py
```

**Common Errors:**
- `Module not found: requests` → Run `pip install requests`
- `CSRF verification failed` → GraphQL endpoint has `csrf_exempt`
- `File not found` → Ensure `sample_transactions.csv` exists

---

## ✨ Summary

**Before:** REST endpoints + GraphQL queries  
**After:** 100% GraphQL (queries + mutations)  

**Key Achievement:** Clean, academic-friendly architecture with single API paradigm.

**Faculty-Ready:** Easy to explain, no complex routing, type-safe schema.

🎓 **Perfect for viva defense!**
