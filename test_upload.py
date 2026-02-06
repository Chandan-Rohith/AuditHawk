"""
Quick test script for CSV upload
"""
import requests

# Upload the CSV file
url = "http://127.0.0.1:8000/api/upload-csv/"
file_path = "sample_transactions.csv"

with open(file_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)
    
print("Status Code:", response.status_code)
print("\nResponse:")
print(response.json())

if response.status_code == 201:
    print("\n✅ CSV uploaded successfully!")
    report_id = response.json()['report']['id']
    print(f"Report ID: {report_id}")
else:
    print("\n❌ Upload failed")
