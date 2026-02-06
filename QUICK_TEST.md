# GraphQL CSV Upload - Quick Test Guide

## How to Test the New GraphQL-Only Upload

### Option 1: GraphQL Playground

1. Start server:
   ```bash
   python manage.py runserver
   ```

2. Go to: http://127.0.0.1:8000/graphql/

3. Paste this mutation:
   ```graphql
   mutation {
     uploadAuditFile(
       fileName: "test.csv"
       csvContent: """transaction_id,date,amount,merchant,category,account_id
TXN-001,2026-02-01T10:00:00,500.00,Amazon,Shopping,ACC-001
TXN-002,2026-02-01T11:00:00,1500.00,Apple,Electronics,ACC-002
TXN-003,2026-02-01T12:00:00,250.50,Starbucks,Food,ACC-001"""
     ) {
       success
       message
       report {
         id
         fileName
         totalTransactions
         status
       }
     }
   }
   ```

4. Click Play ▶️

5. Expected result:
   ```json
   {
     "data": {
       "uploadAuditFile": {
         "success": true,
         "message": "Successfully uploaded and parsed 3 transactions",
         "report": {
           "id": "4",
           "fileName": "test.csv",
           "totalTransactions": 3,
           "status": "processing"
         }
       }
     }
   }
   ```

### Option 2: Python Script

Run:
```bash
python test_upload.py
```

Should see:
```
✅ CSV uploaded successfully via GraphQL!

Message: Successfully uploaded and parsed 10 transactions

Report Details:
  ID: 4
  File Name: sample_transactions.csv
  Total Transactions: 10
  Status: processing
```

### Verify Upload

Query to see the uploaded data:
```graphql
{
  auditReports {
    id
    fileName
    totalTransactions
  }
  
  transactions(reportId: "4") {
    transactionId
    amount
    merchant
  }
}
```

## Error Testing

Test invalid CSV (missing columns):
```graphql
mutation {
  uploadAuditFile(
    fileName: "invalid.csv"
    csvContent: "id,name\n1,John"
  ) {
    success
    message
  }
}
```

Expected:
```json
{
  "data": {
    "uploadAuditFile": {
      "success": false,
      "message": "CSV parsing error: Missing required columns: transaction_id, date, amount, merchant, category, account_id"
    }
  }
}
```
