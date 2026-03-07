"""
CSV Parser for Financial Transaction Data

Handles parsing and validation of uploaded CSV files containing
transaction records for fraud detection analysis.
"""

import csv
import io
import re
from difflib import SequenceMatcher
from typing import List, Dict, Any

try:
    from thefuzz import process as fuzz_process
except Exception:
    fuzz_process = None


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
        'amount',
    ]

    COLUMN_ALIASES = {
        'transaction_id': [
            'transaction_id', 'transactionid', 'txn_id', 'tx_id', 'txid',
            'reference_id', 'reference', 'trans_id', 'id', 'payment_id'
        ],
        'date': [
            'date', 'transaction_date', 'txn_date', 'posted_date',
            'booking_date', 'timestamp', 'created_at', 'event_date'
        ],
        'amount': [
            'amount', 'transaction_amount', 'txn_amount', 'value',
            'debit_amount', 'credit_amount', 'total_amount', 'amt'
        ],
        'merchant': [
            'merchant', 'vendor', 'payee', 'merchant_name', 'vendor_name',
            'counterparty', 'beneficiary', 'description'
        ],
        'category': [
            'category', 'transaction_category', 'txn_category', 'type',
            'transaction_type', 'txn_type', 'spend_category',
            'expense_category', 'class'
        ],
        'account_id': [
            'account_id', 'accountid', 'acct_id', 'acct', 'account',
            'account_number', 'acc_no', 'wallet_id', 'customer_account'
        ],
    }

    KEYWORD_TARGETS = {
        'amount': ['amount', 'amt', 'value', 'withdrawal', 'debit', 'cost'],
        'date': ['date', 'txn_date', 'timestamp', 'dt', 'day', 'time'],
        'merchant': ['desc', 'description', 'narrative', 'details', 'particulars', 'vendor', 'memo', 'merchant', 'payee'],
        'account_id': ['account', 'acct', 'iban', 'acc_no', 'beneficiary', 'account_number'],
        'category': ['category', 'transaction_type', 'txn_type', 'type', 'class'],
        'transaction_id': ['transaction_id', 'txn_id', 'tx_id', 'reference', 'id'],
    }

    FUZZY_MATCH_THRESHOLD = 0.72
    
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

            header_map = self._build_header_map(reader.fieldnames)

            missing_columns = set(self.REQUIRED_COLUMNS) - set(header_map.keys())
            if missing_columns:
                raise CSVParserError(
                    f"Missing required columns: {', '.join(missing_columns)}"
                )
            
            # Parse rows
            transactions = []
            for idx, row in enumerate(reader, start=1):
                try:
                    transaction = self._parse_row(row, idx, header_map)
                    transactions.append(transaction)
                except ValueError as e:
                    raise CSVParserError(f"Error in row {idx}: {str(e)}")
            
            if not transactions:
                raise CSVParserError("CSV file contains no transaction data")
            
            self.transactions = transactions
            return transactions
            
        except csv.Error as e:
            raise CSVParserError(f"CSV format error: {str(e)}")

    @staticmethod
    def _normalize_header(header: str) -> str:
        if header is None:
            return ''
        normalized = header.strip().lower()
        normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
        normalized = re.sub(r'_+', '_', normalized).strip('_')
        return normalized

    @classmethod
    def _keyword_match_score(cls, header: str, keywords: List[str]) -> float:
        if fuzz_process is not None:
            try:
                result = fuzz_process.extractOne(header.lower(), keywords)
                if not result:
                    return 0.0
                _matched_keyword, score = result
                normalized_score = float(score) / 100.0
                if any(keyword in header.lower() for keyword in keywords):
                    normalized_score += 0.10
                return min(normalized_score, 1.0)
            except Exception:
                pass

        normalized_header = cls._normalize_header(header)
        if not normalized_header:
            return 0.0

        best_score = 0.0
        for keyword in keywords:
            normalized_keyword = cls._normalize_header(keyword)
            if not normalized_keyword:
                continue

            score = SequenceMatcher(None, normalized_header, normalized_keyword).ratio()
            if normalized_keyword in normalized_header:
                score += 0.10
            best_score = max(best_score, score)

        return min(best_score, 1.0)

    @staticmethod
    def _parse_amount(raw_value: str) -> float:
        cleaned = re.sub(r'[$,\s]', '', str(raw_value or ''))
        if cleaned == '':
            return 0.0
        amount = float(cleaned)
        return amount

    @classmethod
    def _map_by_targets(cls, headers: List[str]) -> Dict[str, str]:
        mapped: Dict[str, tuple[str, float]] = {}
        used_headers: set[str] = set()

        for target_field, keywords in cls.KEYWORD_TARGETS.items():
            best_header = None
            best_score = 0.0

            for header in headers:
                if header in used_headers:
                    continue
                score = cls._keyword_match_score(header, keywords)
                if score > 0.60 and score > best_score:
                    best_score = score
                    best_header = header

            if best_header:
                mapped[target_field] = (best_header, best_score)
                used_headers.add(best_header)

        return {required: source for required, (source, _score) in mapped.items()}

    @classmethod
    def _get_candidate_aliases(cls, required_field: str) -> List[str]:
        aliases = cls.COLUMN_ALIASES.get(required_field, [])
        normalized = [cls._normalize_header(alias) for alias in aliases]
        if required_field not in normalized:
            normalized.append(required_field)
        return list(dict.fromkeys(normalized))

    @classmethod
    def _best_required_match(cls, original_header: str) -> tuple[str | None, float]:
        normalized_header = cls._normalize_header(original_header)
        if not normalized_header:
            return None, 0.0

        best_field = None
        best_score = 0.0

        for required_field in cls.COLUMN_ALIASES.keys():
            aliases = cls._get_candidate_aliases(required_field)
            for alias in aliases:
                score = SequenceMatcher(None, normalized_header, alias).ratio()
                if score > best_score:
                    best_score = score
                    best_field = required_field

        if best_score < cls.FUZZY_MATCH_THRESHOLD:
            return None, best_score
        return best_field, best_score

    @classmethod
    def _build_header_map(cls, headers: List[str]) -> Dict[str, str]:
        """
        Map canonical required fields to source CSV headers using aliases + fuzzy matching.

        Returns:
            Dict like {"transaction_id": "Txn ID", "amount": "Amount($)", ...}
        """
        mapped: Dict[str, tuple[str, float]] = {}

        # Pass 1: direct keyword-target mapping (matches user's ingestor behavior)
        target_map = cls._map_by_targets(headers)
        for required, source in target_map.items():
            # Seed with threshold confidence so stronger alias/fuzzy matches can still replace it.
            mapped[required] = (source, cls.FUZZY_MATCH_THRESHOLD)

        for header in headers:
            required_field, score = cls._best_required_match(header)
            if not required_field:
                continue

            current = mapped.get(required_field)
            if current is None or score > current[1]:
                mapped[required_field] = (header, score)

        return {required: source for required, (source, _score) in mapped.items()}
    
    def _parse_row(self, row: Dict[str, str], row_num: int, header_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse a single CSV row into a transaction dictionary.
        
        Args:
            row: Dictionary representing one CSV row
            row_num: Row number (for error messages)
            
        Returns:
            Parsed transaction dictionary
        """
        try:
            mapped_row = {
                required_field: (row.get(source_header, '') or '').strip()
                for required_field, source_header in header_map.items()
            }

            # Parse amount as float
            amount = self._parse_amount(mapped_row.get('amount', ''))
            
            # Validate date format (basic validation)
            date = mapped_row.get('date', '').strip() or "N/A"

            transaction_id = mapped_row.get('transaction_id', '').strip() or f"TXN-{row_num}"
            merchant = mapped_row.get('merchant', '').strip() or "Unknown Vendor"
            category = mapped_row.get('category', '').strip() or "Unknown"
            account_id = mapped_row.get('account_id', '').strip() or "N/A"
            
            # Create transaction object
            transaction = {
                'id': str(row_num),  # Auto-generate ID
                'transaction_id': transaction_id,
                'date': date,
                'amount': amount,
                'merchant': merchant,
                'category': category,
                'account_id': account_id
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
