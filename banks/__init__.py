"""
Bank plugin loader
"""
from .base import GenericBankAPI
from .creditas import CreditasClient


BANK_CLIENTS = {
    'creditas': CreditasClient,
}


def get_bank_client(bank_name: str, api_token: str, account_id: str, **kwargs) -> GenericBankAPI:
    """
    Get bank API client instance

    Args:
        bank_name: Name of the bank (e.g., 'creditas', 'fio')
        api_token: API authentication token
        account_id: Account identifier
        **kwargs: Additional bank-specific configuration

    Returns:
        Instance of bank API client

    Raises:
        ValueError: If bank_name is not supported
    """
    bank_name = bank_name.lower()

    if bank_name not in BANK_CLIENTS:
        supported = ', '.join(BANK_CLIENTS.keys())
        raise ValueError(f"Unsupported bank: '{bank_name}'. Supported banks: {supported}")

    client_class = BANK_CLIENTS[bank_name]
    return client_class(api_token, account_id, **kwargs)


__all__ = ['GenericBankAPI', 'CreditasClient', 'get_bank_client']
