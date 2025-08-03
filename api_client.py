import requests
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CreditasAPIClient:
    def __init__(self, api_token: str, account_id: str, base_url: str):
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'Authorization-Bearer': api_token,
            'Content-Type': 'application/json'
        })

    def fetch_transactions(self, page_size: int = 50, page_index: int = 0) -> Optional[Dict]:
        """Fetch transactions from Creditas API"""
        try:
            url = f"{self.base_url}/account/transaction/search"
            payload = {
                "accountId": self.account_id,
                "pageItemCount": page_size,
                "pageIndex": page_index
            }
            
            logger.info(f"Fetching transactions from Creditas API (page {page_index}, size {page_size})")
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched {data.get('itemCount', 0)} transactions")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def fetch_all_transactions(self, max_pages: int = 10) -> Optional[List[Dict]]:
        """Fetch all transactions across multiple pages"""
        all_transactions = []
        page_index = 0
        
        while page_index < max_pages:
            data = self.fetch_transactions(page_index=page_index)
            if not data or not data.get('transactions'):
                break
                
            transactions = data.get('transactions', [])
            all_transactions.extend(transactions)
            
            # If we got fewer transactions than requested, we've reached the end
            if len(transactions) < 50:
                break
                
            page_index += 1
        
        logger.info(f"Fetched total of {len(all_transactions)} transactions across {page_index + 1} pages")
        return all_transactions if all_transactions else None

    def save_transactions(self, transactions: List[Dict], file_path: str) -> bool:
        """Save transactions to JSON file"""
        try:
            data = {
                "transactions": transactions,
                "itemCount": len(transactions)
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(transactions)} transactions to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save transactions: {e}")
            return False