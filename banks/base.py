"""
Base class for bank API implementations
"""
from typing import List, Dict, Optional


class GenericBankAPI:
    """Abstract base class for bank API clients"""

    def __init__(self, api_token: str, account_id: str, **kwargs):
        """
        Initialize bank API client

        Args:
            api_token: Authentication token for the bank API
            account_id: Account identifier
            **kwargs: Additional bank-specific configuration
        """
        self.api_token = api_token
        self.account_id = account_id

    def fetch_transactions(self, page_size: int = 50, page_index: int = 0) -> Optional[Dict]:
        """
        Fetch transactions from bank API

        Args:
            page_size: Number of transactions per page
            page_index: Page index (0-based)

        Returns:
            Dictionary with transaction data or None on error
        """
        raise NotImplementedError("Subclasses must implement fetch_transactions()")

    def fetch_all_transactions(self, max_pages: int = 10) -> Optional[List[Dict]]:
        """
        Fetch all transactions across multiple pages

        Args:
            max_pages: Maximum number of pages to fetch

        Returns:
            List of all transactions or None on error
        """
        raise NotImplementedError("Subclasses must implement fetch_all_transactions()")

    def save_transactions(self, transactions: List[Dict], file_path: str) -> bool:
        """
        Save transactions to JSON file

        Args:
            transactions: List of transaction dictionaries
            file_path: Path to save the JSON file

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement save_transactions()")
