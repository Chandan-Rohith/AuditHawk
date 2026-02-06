import graphene
from datetime import datetime
from .csv_parser import parse_transaction_csv, CSVParserError

# ============================================
# GraphQL Types (Business Entities)
# ============================================

class TransactionType(graphene.ObjectType):
    """Represents a single transaction from CSV"""
    id = graphene.ID()
    transaction_id = graphene.String()
    date = graphene.String()
    amount = graphene.Float()
    merchant = graphene.String()
    category = graphene.String()
    account_id = graphene.String()


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
    explanation = graphene.String()  # XAI reasoning


# ============================================
# Mock Data (In-Memory Storage)
# ============================================

# Store all transactions by report_id
MOCK_TRANSACTIONS = {
    "1": [
        {
            "id": "1001",
            "transaction_id": "TXN-2026-00542",
            "date": "2026-01-15T14:30:00",
            "amount": 45000.00,
            "merchant": "Global Tech Supplies",
            "category": "Electronics",
            "account_id": "ACC-001"
        },
        {
            "id": "1002",
            "transaction_id": "TXN-2026-00543",
            "date": "2026-01-15T15:20:00",
            "amount": 250.00,
            "merchant": "Office Depot",
            "category": "Office Supplies",
            "account_id": "ACC-002"
        },
        {
            "id": "1003",
            "transaction_id": "TXN-2026-00544",
            "date": "2026-01-15T16:10:00",
            "amount": 8500.50,
            "merchant": "Midnight Transfers LLC",
            "category": "Wire Transfer",
            "account_id": "ACC-003"
        }
    ]
}

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
            "decision": "review_required",
            "explanation": "High amount ($45,000) + unusual merchant category + amount is 3.2 standard deviations above mean"
        },
        {
            "id": "102",
            "transaction_id": "TXN-2026-00544",
            "amount": 8500.50,
            "risk_score": 0.78,
            "decision": "review_required",
            "explanation": "Transaction at midnight (02:15 AM) + new merchant + high amount"
        }
    ]
}

class DashboardSummaryType(graphene.ObjectType):
    total_reports = graphene.Int()
    total_transactions = graphene.Int()
    total_flagged = graphene.Int()
    processing_count = graphene.Int()
    completed_count = graphene.Int()
# ============================================
# Query Resolvers
# ============================================

class Query(graphene.ObjectType):
    """Root query for AuditHawk GraphQL API"""

    hello = graphene.String(default_value="Hello AuditHawk!")

    audit_reports = graphene.List(AuditReportType)
    transactions = graphene.List(
        TransactionType,
        report_id=graphene.ID(required=True)
    )
    flagged_transactions = graphene.List(
        FlaggedTransactionType,
        report_id=graphene.ID(required=True)
    )
    dashboard_summary = graphene.Field(DashboardSummaryType)

    def resolve_audit_reports(root, info):
        return [AuditReportType(**report) for report in MOCK_AUDIT_REPORTS]

    def resolve_transactions(root, info, report_id):
        transactions = MOCK_TRANSACTIONS.get(report_id, [])
        return [TransactionType(**txn) for txn in transactions]

    def resolve_flagged_transactions(root, info, report_id):
        transactions = MOCK_FLAGGED_TRANSACTIONS.get(report_id, [])
        return [FlaggedTransactionType(**txn) for txn in transactions]

    def resolve_dashboard_summary(root, info):
        total_reports = len(MOCK_AUDIT_REPORTS)

        total_transactions = sum(
            report["total_transactions"] for report in MOCK_AUDIT_REPORTS
        )

        total_flagged = sum(
            report["flagged_count"] for report in MOCK_AUDIT_REPORTS
        )

        processing_count = sum(
            1 for report in MOCK_AUDIT_REPORTS if report["status"] == "processing"
        )

        completed_count = sum(
            1 for report in MOCK_AUDIT_REPORTS if report["status"] == "completed"
        )

        return DashboardSummaryType(
            total_reports=total_reports,
            total_transactions=total_transactions,
            total_flagged=total_flagged,
            processing_count=processing_count,
            completed_count=completed_count
        )



# ============================================
# Mutation Types
# ============================================

class UploadAuditFileResponse(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    report = graphene.Field(AuditReportType)


class UploadAuditFile(graphene.Mutation):
    """
    Upload and parse a CSV file containing financial transactions.
    This is the ONLY way to upload data - no REST endpoints are used.
    """
    class Arguments:
        file_name = graphene.String(required=True)
        csv_content = graphene.String(required=True)

    Output = UploadAuditFileResponse

    def mutate(root, info, file_name, csv_content):
        """
        Parse CSV content, validate it, and create an audit report.
        
        Args:
            file_name: Name of the CSV file (e.g., "transactions.csv")
            csv_content: Complete CSV file content as a string
            
        Returns:
            UploadAuditFileResponse with success status, message, and report
        """
        try:
            # Parse and validate CSV content using csv_parser
            transactions, summary = parse_transaction_csv(csv_content)
            
            # Create new audit report
            report_id = str(len(MOCK_AUDIT_REPORTS) + 1)
            new_report = {
                "id": report_id,
                "file_name": file_name,
                "uploaded_at": datetime.utcnow().isoformat(),
                "total_transactions": summary['total_transactions'],
                "flagged_count": 0,  # Will be updated after ML analysis
                "status": "processing"
            }
            
            # Store report and transactions in memory
            MOCK_AUDIT_REPORTS.append(new_report)
            MOCK_TRANSACTIONS[report_id] = transactions
            
            # Initialize empty flagged transactions list
            MOCK_FLAGGED_TRANSACTIONS[report_id] = []
            
            return UploadAuditFileResponse(
                success=True,
                message=f"Successfully uploaded and parsed {summary['total_transactions']} transactions",
                report=AuditReportType(**new_report)
            )
            
        except CSVParserError as e:
            # Handle CSV parsing/validation errors
            return UploadAuditFileResponse(
                success=False,
                message=f"CSV parsing error: {str(e)}",
                report=None
            )
        except Exception as e:
            # Handle unexpected errors
            return UploadAuditFileResponse(
                success=False,
                message=f"Unexpected error: {str(e)}",
                report=None
            )


class UpdateTransactionDecisionResponse(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    transaction = graphene.Field(FlaggedTransactionType)


class UpdateTransactionDecision(graphene.Mutation):
    """Update the decision on a flagged transaction (approve/reject/escalate)"""
    
    class Arguments:
        report_id = graphene.ID(required=True)
        transaction_id = graphene.String(required=True)
        decision = graphene.String(required=True)  # approved, rejected, escalate
    
    Output = UpdateTransactionDecisionResponse
    
    def mutate(root, info, report_id, transaction_id, decision):
        # Validate decision
        valid_decisions = ['approved', 'rejected', 'escalate', 'review_required', 'monitor']
        if decision not in valid_decisions:
            return UpdateTransactionDecisionResponse(
                success=False,
                message=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}",
                transaction=None
            )
        
        # Find the flagged transaction
        flagged_txns = MOCK_FLAGGED_TRANSACTIONS.get(report_id, [])
        transaction = None
        
        for txn in flagged_txns:
            if txn['transaction_id'] == transaction_id:
                txn['decision'] = decision
                transaction = txn
                break
        
        if not transaction:
            return UpdateTransactionDecisionResponse(
                success=False,
                message=f"Transaction {transaction_id} not found in report {report_id}",
                transaction=None
            )
        
        return UpdateTransactionDecisionResponse(
            success=True,
            message=f"Transaction decision updated to '{decision}'",
            transaction=FlaggedTransactionType(**transaction)
        )


class Mutation(graphene.ObjectType):
    upload_audit_file = UploadAuditFile.Field()
    update_transaction_decision = UpdateTransactionDecision.Field()


# ============================================
# Schema Export
# ============================================

schema = graphene.Schema(query=Query, mutation=Mutation)
