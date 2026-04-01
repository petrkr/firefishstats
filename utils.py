import json
import logging
import re
from collections import defaultdict
from decimal import Decimal

logger = logging.getLogger(__name__)

def load_transactions(file_path):
    """Načte transakce z JSON souboru se strukturou { transactions: [...], itemCount: n }"""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            transactions = data.get("transactions", [])
            logger.info(f"Loaded {len(transactions)} transactions from {file_path}")
            return transactions
    except FileNotFoundError:
        logger.error(f"Transaction file not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading transactions from {file_path}: {e}")
        return []


def _normalize_remittance(remittance, typ, rules):
    if not remittance:
        return remittance
    if typ not in rules["apply_to"]:
        return remittance
    for pattern in rules["regex"]:
        try:
            match = re.match(pattern, remittance)
        except re.error:
            logger.warning(f"Invalid remittance regex: {pattern}")
            continue
        if match:
            if match.lastindex:
                return match.group(1).strip()
            if "core" in match.groupdict():
                return match.group("core").strip()
            return match.group(0).strip()
    return remittance


def _is_known_account_transaction(tx, known_accounts):
    acc = tx.get("partnerAccount", {})
    number = acc.get("number")
    bank_code = acc.get("bankCode")
    partner_name = (acc.get("partnerName") or "").strip()

    if number and bank_code and f"{number}/{bank_code}" in known_accounts:
        return True

    if partner_name and partner_name in known_accounts:
        return True

    return False


def classify_transactions(transactions, known_accounts, remittance_rules=None):
    deposits = []
    withdrawals = []
    investments = defaultdict(list)
    returns = defaultdict(list)
    overpayments = defaultdict(list)
    remittance_rules = remittance_rules or {"apply_to": set(), "regex": []}

    for tx in transactions:
        typ = tx.get("type")
        remittance = tx.get("remittanceInfo", "").strip()
        remittance = _normalize_remittance(remittance, typ, remittance_rules)
        is_known = _is_known_account_transaction(tx, known_accounts)

        if typ == "CREDIT" and is_known:
            deposits.append(tx)
        elif typ == "DEBIT" and is_known:
            withdrawals.append(tx)
        elif remittance:
            if typ == "DEBIT":
                if remittance.endswith(" ret"):
                    base = remittance.removesuffix(" ret").strip()
                    overpayments[base].append(tx)
                else:
                    investments[remittance].append(tx)
            elif typ == "CREDIT":
                returns[remittance].append(tx)

    return deposits, withdrawals, investments, returns, overpayments


def compute_stats(deposits, withdrawals, investment_rows):
    return {
        "num_deposits": len(deposits),
        "deposited_total": sum(Decimal(tx["amount"]["value"]) for tx in deposits),
        "num_withdrawals": len(withdrawals),
        "withdrawn_total": sum(Decimal(tx["amount"]["value"]) for tx in withdrawals),
        "num_investments": len(investment_rows),
        "matched_investments": sum(1 for row in investment_rows if row["profit"] is not None),
        "total_invested": sum(row["invested_total"] for row in investment_rows),
        "total_returned": sum(row["returned_total"] for row in investment_rows),
        "total_overpaid": sum(row["overpaid_total"] for row in investment_rows),
        "total_profit": sum(row["profit"] for row in investment_rows if row["profit"] is not None)
    }


def compute_account_balance(transactions):
    balance = Decimal("0")
    for tx in transactions:
        amount = Decimal(tx["amount"]["value"])
        if tx["type"] == "CREDIT":
            balance += amount
        elif tx["type"] == "DEBIT":
            balance -= amount
    return balance
