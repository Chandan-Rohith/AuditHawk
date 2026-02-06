"""
GraphQL CSV Upload Test for AuditHawk

This script demonstrates how to upload CSV files via GraphQL mutation.
All uploads now go through GraphQL - no REST endpoints are used.
"""
import requests

# GraphQL endpoint
url = "http://127.0.0.1:8000/graphql/"

# Read CSV file content
with open("sample_transactions.csv", "r") as f:
    csv_content = f.read()

# GraphQL mutation to upload CSV
mutation = """
mutation UploadCSV($fileName: String!, $csvContent: String!) {
  uploadAuditFile(fileName: $fileName, csvContent: $csvContent) {
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
"""

# Variables for the mutation
variables = {
    "fileName": "sample_transactions.csv",
    "csvContent": csv_content
}

# Send GraphQL request
response = requests.post(
    url,
    json={
        "query": mutation,
        "variables": variables
    }
)

# Parse response
result = response.json()

if "errors" in result:
    print("❌ GraphQL Error:")
    for error in result["errors"]:
        print(f"  - {error['message']}")
else:
    data = result["data"]["uploadAuditFile"]
    if data["success"]:
        print("✅ CSV uploaded successfully via GraphQL!")
        print(f"\nMessage: {data['message']}")
        print(f"\nReport Details:")
        print(f"  ID: {data['report']['id']}")
        print(f"  File Name: {data['report']['fileName']}")
        print(f"  Total Transactions: {data['report']['totalTransactions']}")
        print(f"  Status: {data['report']['status']}")
    else:
        print(f"❌ Upload failed: {data['message']}")

