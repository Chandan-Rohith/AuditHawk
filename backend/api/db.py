import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["audithawk"]

audit_reports_col = db["audit_reports"]
transactions_col = db["transactions"]
flagged_transactions_col = db["flagged_transactions"]
