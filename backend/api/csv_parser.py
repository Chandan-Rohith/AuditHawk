"""
CSV Parser for Financial Transaction Data

Handles parsing and validation of uploaded CSV files containing
transaction records for fraud detection analysis.
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any


class CSVParserError(Exception):
    """Custom exception for CSV parsing errors"""
    pass


class TransactionCSVParser:
    """
    Parses CSV files containing financial transaction data.
    
    Expected CSV format:
    transaction_id,date,amount,merchant,category,account_id
    """
    
    REQUIRED_COLUMNS = [
        'transaction_id',
        'date',
        'amount',
        'merchant',
        'category',
        'account_id'
    ]
    
    def __init__(self, file_content: str):
        """
        Initialize parser with file content.
        
        Args:
            file_content: String content of the CSV file
        """
        self.file_content = file_content
        self.transactions = []
        
    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse the CSV file and return a list of transaction dictionaries.
        
        Returns:
            List of transaction dictionaries
            
        Raises:
            CSVParserError: If CSV format is invalid
        """
        try:
            # Use StringIO to read CSV from string
            csv_file = io.StringIO(self.file_content)
            reader = csv.DictReader(csv_file)
            
            # Validate headers
            if not reader.fieldnames:
                raise CSVParserError("CSV file is empty or has no headers")
            
            missing_columns = set(self.REQUIRED_COLUMNS) - set(reader.fieldnames)
            if missing_columns:
                raise CSVParserError(
                    f"Missing required columns: {', '.join(missing_columns)}"
                )
            
            # Parse rows
            transactions = []
            for idx, row in enumerate(reader, start=1):
                try:
                    transaction = self._parse_row(row, idx)
                    transactions.append(transaction)
                except ValueError as e:
                    raise CSVParserError(f"Error in row {idx}: {str(e)}")
            
            if not transactions:
                raise CSVParserError("CSV file contains no transaction data")
            
            self.transactions = transactions
            return transactions
            
        except csv.Error as e:
            raise CSVParserError(f"CSV format error: {str(e)}")
    
    def _parse_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """
        Parse a single CSV row into a transaction dictionary.
        
        Args:
            row: Dictionary representing one CSV row
            row_num: Row number (for error messages)
            
        Returns:
            Parsed transaction dictionary
        """
        try:
            # Parse amount as float
            amount = float(row['amount'])
            if amount < 0:
                raise ValueError("Amount cannot be negative")
            
            # Validate date format (basic validation)
            date = row['date'].strip()
            if not date:
                raise ValueError("Date cannot be empty")
            
            # Create transaction object
            transaction = {
                'id': str(row_num),  # Auto-generate ID
                'transaction_id': row['transaction_id'].strip(),
                'date': date,
                'amount': amount,
                'merchant': row['merchant'].strip(),
                'category': row['category'].strip(),
                'account_id': row['account_id'].strip()
            }
            
            # Validate required fields are not empty
            for key, value in transaction.items():
                if key != 'id' and (value == '' or value is None):
                    raise ValueError(f"Field '{key}' cannot be empty")
            
            return transaction
            
        except KeyError as e:
            raise ValueError(f"Missing field: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of parsed transactions.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.transactions:
            return {
                'total_transactions': 0,
                'total_amount': 0.0,
                'avg_amount': 0.0
            }
        
        amounts = [t['amount'] for t in self.transactions]
        
        return {
            'total_transactions': len(self.transactions),
            'total_amount': sum(amounts),
            'avg_amount': sum(amounts) / len(amounts),
            'min_amount': min(amounts),
            'max_amount': max(amounts)
        }


def parse_transaction_csv(file_content: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to parse CSV and return transactions with summary.
    
    Args:
        file_content: String content of CSV file
        
    Returns:
        Tuple of (transactions list, summary dict)
        
    Raises:
        CSVParserError: If parsing fails
    """
    parser = TransactionCSVParser(file_content)
    transactions = parser.parse()
    summary = parser.get_summary()
    return transactions, summary
