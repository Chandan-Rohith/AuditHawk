import graphene
from datetime import datetime

# ============================================
# GraphQL Types (Business Entities)
# ============================================

class AuditReportType(graphene.ObjectType):
    """Represents an uploaded audit file and its processing status"""
    id = graphene.ID()
    file_name = graphene.String()
    uploaded_at = graphene.String()
    total_transactions = graphene.Int()
    flagged_count = graphene.Int()
    status = graphene.String()


class FlaggedTransactionType(graphene.ObjectType):
    """Represents a suspicious transaction detected by the system"""
    id = graphene.ID()
    transaction_id = graphene.String()
    amount = graphene.Float()
    risk_score = graphene.Float()
    decision = graphene.String()


# ============================================
# Mock Data (In-Memory Storage)
# ============================================

MOCK_AUDIT_REPORTS = [
    {
        "id": "1",
        "file_name": "january_transactions.csv",
        "uploaded_at": "2026-01-15T10:30:00",
        "total_transactions": 5420,
        "flagged_count": 23,
        "status": "completed"
    },
    {
        "id": "2",
        "file_name": "december_transactions.csv",
        "uploaded_at": "2026-01-10T14:20:00",
        "total_transactions": 4890,
        "flagged_count": 18,
        "status": "completed"
    },
    {
        "id": "3",
        "file_name": "february_transactions.csv",
        "uploaded_at": "2026-02-05T09:15:00",
        "total_transactions": 6100,
        "flagged_count": 31,
        "status": "processing"
    }
]

MOCK_FLAGGED_TRANSACTIONS = {
    "1": [
        {
            "id": "101",
            "transaction_id": "TXN-2026-00542",
            "amount": 45000.00,
            "risk_score": 0.92,
            "decision": "review_required"
        },
        {
            "id": "102",
            "transaction_id": "TXN-2026-01203",
            "amount": 8500.50,
            "risk_score": 0.78,
            "decision": "review_required"
        },
        {
            "id": "103",
            "transaction_id": "TXN-2026-02134",
            "amount": 120000.00,
            "risk_score": 0.95,
            "decision": "escalate"
        }
    ],
    "2": [
        {
            "id": "201",
            "transaction_id": "TXN-2025-12890",
            "amount": 32000.00,
            "risk_score": 0.85,
            "decision": "review_required"
        },
        {
            "id": "202",
            "transaction_id": "TXN-2025-13421",
            "amount": 15000.00,
            "risk_score": 0.72,
            "decision": "monitor"
        }
    ]
}


# ============================================
# Query Resolvers
# ============================================

class Query(graphene.ObjectType):
    """Root query for AuditHawk GraphQL API"""
    
    # Health check
    hello = graphene.String(default_value="Hello AuditHawk!")
    
    # Business queries
    audit_reports = graphene.List(AuditReportType)
    flagged_transactions = graphene.List(
        FlaggedTransactionType,
        report_id=graphene.ID(required=True)
    )
    
    def resolve_audit_reports(root, info):
        """Returns all audit reports"""
        return [AuditReportType(**report) for report in MOCK_AUDIT_REPORTS]
    
    def resolve_flagged_transactions(root, info, report_id):
        """Returns flagged transactions for a specific audit report"""
        transactions = MOCK_FLAGGED_TRANSACTIONS.get(report_id, [])
        return [FlaggedTransactionType(**txn) for txn in transactions]


# ============================================
# Schema Export
# ============================================

schema = graphene.Schema(query=Query)