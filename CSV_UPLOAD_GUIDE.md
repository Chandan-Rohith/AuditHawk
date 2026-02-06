# CSV Upload Testing Guide

## What's Been Added

### 1. **New GraphQL Types**
- `TransactionType` - Individual transaction data
- Updated `FlaggedTransactionType` - Now includes XAI explanations

### 2. **New GraphQL Queries**
```graphql
# Get all transactions for a report
transactions(reportId: ID!)

# View explanations for flagged transactions
flaggedTransactions(reportId: ID!) {
  explanation  # Now includes SHAP-style reasoning
}
```

### 3. **New GraphQL Mutations**
```graphql
# Update decision on flagged transaction
updateTransactionDecision(
  reportId: ID!
  transactionId: String!
  decision: String!  # approved, rejected, escalate, review_required, monitor
)
```

### 4. **REST API Endpoints**
- `POST /api/upload-csv/` - Upload and parse CSV files
- `GET /api/health/` - Health check endpoint

### 5. **CSV Parser**
- Validates CSV format
- Parses transaction data
- Provides summary statistics
- Error handling with detailed messages

---

## Testing Instructions

### Test 1: Query All Transactions

Open GraphQL interface at `http://127.0.0.1:8000/graphql` and run:

```graphql
{
  transactions(reportId: "1") {
    id
    transactionId
    date
    amount
    merchant
    category
    accountId
  }
}
```

### Test 2: View Flagged Transactions with Explanations

```graphql
{
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

### Test 3: Update Transaction Decision

```graphql
mutation {
  updateTransactionDecision(
    reportId: "1"
    transactionId: "TXN-2026-00542"
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

### Test 4: Upload CSV File (cURL)

Open a new terminal and run:

```powershell
curl -X POST http://127.0.0.1:8000/api/upload-csv/ `
  -F "file=@sample_transactions.csv"
```

Or using Python:

```python
import requests

url = "http://127.0.0.1:8000/api/upload-csv/"
files = {'file': open('sample_transactions.csv', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

### Test 5: Verify Uploaded Data

After uploading, query the new report:

```graphql
{
  auditReports {
    id
    fileName
    uploadedAt
    totalTransactions
    status
  }
}
```

Then view its transactions:

```graphql
{
  transactions(reportId: "4") {  # Use the new report ID
    transactionId
    amount
    merchant
    date
  }
}
```

### Test 6: Health Check

```powershell
curl http://127.0.0.1:8000/api/health/
```

---

## Sample CSV Format

Your CSV must have these columns:
```
transaction_id,date,amount,merchant,category,account_id
```

Example (see `sample_transactions.csv`):
```csv
transaction_id,date,amount,merchant,category,account_id
TXN-2026-00001,2026-02-01T09:30:00,250.50,Amazon,Online Shopping,ACC-001
TXN-2026-00002,2026-02-01T10:15:00,1500.00,Dell Technologies,Electronics,ACC-002
```

---

## What's Next?

1. **ML Integration** - Add Isolation Forest for fraud detection
2. **SHAP Explanations** - Generate real XAI explanations
3. **MongoDB** - Replace in-memory storage with database
4. **Batch Processing** - Queue system for large CSV files
5. **Frontend** - React dashboard for visualization

---

## Architecture

```
CSV Upload → Parser → Storage → [Future: ML Pipeline] → Flagged Transactions → GraphQL API → Frontend
```

Current state: ✅ CSV Upload, ✅ Parser, ✅ Storage (mock), ✅ GraphQL API
