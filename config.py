import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class Account:
    """Represents a configured account"""

    def __init__(self, id: str, name: str, bank: str, api_token: str, account_id: str, known_accounts: list):
        self.id = id
        self.name = name
        self.bank = bank
        self.api_token = api_token
        self.account_id = account_id
        self.known_accounts = set(known_accounts) if known_accounts else set()
        self.transactions_file = f"data/{id}_transactions.json"

    def __repr__(self):
        return f"Account(id={self.id}, name={self.name}, bank={self.bank})"


def load_accounts_from_config(config_file: str = "config.json") -> list:
    """
    Load accounts from config.json

    Args:
        config_file: Path to config.json file

    Returns:
        List of Account objects
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        accounts = []
        for account_data in config_data.get('accounts', []):
            account = Account(
                id=account_data['id'],
                name=account_data.get('name', account_data['id']),
                bank=account_data['bank'],
                api_token=account_data['api_token'],
                account_id=account_data['account_id'],
                known_accounts=account_data.get('known_accounts', [])
            )
            accounts.append(account)

        logger.info(f"Loaded {len(accounts)} accounts from {config_file}")
        return accounts

    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return []
    except KeyError as e:
        logger.error(f"Missing required field in config: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return []


def load_remittance_rules(config_file: str = "config.json") -> dict:
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        remittance = config_data.get('remittance', {})
        apply_to = set(remittance.get('apply_to', []))
        regex = remittance.get('regex', [])
        if not isinstance(regex, list):
            logger.error("Remittance regex must be a list")
            regex = []

        return {"apply_to": apply_to, "regex": regex}

    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
        return {"apply_to": set(), "regex": []}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return {"apply_to": set(), "regex": []}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"apply_to": set(), "regex": []}


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    DEBUG = True


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
