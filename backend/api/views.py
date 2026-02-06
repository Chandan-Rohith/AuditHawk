"""
API Views for AuditHawk

Handles file uploads and other REST endpoints.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime

from .csv_parser import parse_transaction_csv, CSVParserError
from .schema import MOCK_AUDIT_REPORTS, MOCK_TRANSACTIONS, MOCK_FLAGGED_TRANSACTIONS


@csrf_exempt
@require_http_methods(["POST"])
def upload_csv(request):
    """
    Handle CSV file upload for transaction analysis.
    
    Expects:
        - POST request with file in 'file' field
        
    Returns:
        JSON response with report details
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded. Please provide a CSV file.'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Validate file extension
        if not uploaded_file.name.endswith('.csv'):
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type. Please upload a CSV file.'
            }, status=400)
        
        # Read file content
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Unable to decode file. Please ensure it is a valid CSV file.'
            }, status=400)
        
        # Parse CSV
        try:
            transactions, summary = parse_transaction_csv(file_content)
        except CSVParserError as e:
            return JsonResponse({
                'success': False,
                'error': f'CSV parsing error: {str(e)}'
            }, status=400)
        
        # Create new audit report
        report_id = str(len(MOCK_AUDIT_REPORTS) + 1)
        new_report = {
            "id": report_id,
            "file_name": uploaded_file.name,
            "uploaded_at": datetime.utcnow().isoformat(),
            "total_transactions": summary['total_transactions'],
            "flagged_count": 0,  # Will be updated after ML analysis
            "status": "processing"
        }
        
        # Store report and transactions
        MOCK_AUDIT_REPORTS.append(new_report)
        MOCK_TRANSACTIONS[report_id] = transactions
        
        # Initialize empty flagged transactions for this report
        MOCK_FLAGGED_TRANSACTIONS[report_id] = []
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully uploaded {summary["total_transactions"]} transactions',
            'report': new_report,
            'summary': summary
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'AuditHawk API',
        'timestamp': datetime.utcnow().isoformat()
    })

