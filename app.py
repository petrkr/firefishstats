import os
import logging
from flask import Flask, render_template, jsonify, abort
from utils import load_transactions, classify_transactions, compute_stats, compute_account_balance
from banks import get_bank_client
from config import config, load_accounts_from_config
from decimal import Decimal
from datetime import datetime


def parse_date(tx):
    return datetime.strptime(tx["effectiveDate"], "%Y-%m-%d")


def get_sort_date(row):
    dates = []

    for tx in row["returns"] + row["investments"] + row["overpayments"]:
        if "effectiveDate" in tx:
            dates.append(parse_date(tx))

    return max(dates) if dates else datetime.min


def create_app(config_name=None):
    app = Flask(__name__)

    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    # Setup logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    return app


app = create_app()


def process_account_data(account):
    """Process transaction data for a single account"""
    transactions = load_transactions(account.transactions_file)
    deposits, withdrawals, investments, returns, overpayments = classify_transactions(
        transactions, account.known_accounts
    )

    investment_rows = []
    all_remittances = set(investments) | set(returns) | set(overpayments)

    for remit in sorted(all_remittances):
        inv_list = investments.get(remit, [])
        ret_list = returns.get(remit, [])
        overpay_list = overpayments.get(remit, [])

        invested_total = sum(Decimal(tx["amount"]["value"]) for tx in inv_list)
        returned_total = sum(Decimal(tx["amount"]["value"]) for tx in ret_list)
        overpaid_total = sum(Decimal(tx["amount"]["value"]) for tx in overpay_list)

        net_profit = returned_total - invested_total - overpaid_total if returned_total else None

        # Get currency from first available transaction
        currency = None
        for tx in inv_list + ret_list + overpay_list:
            if "amount" in tx and "currency" in tx["amount"]:
                currency = tx["amount"]["currency"]
                break

        investment_rows.append({
            "remittance": remit,
            "investments": inv_list,
            "returns": ret_list,
            "overpayments": overpay_list,
            "invested_total": invested_total,
            "returned_total": returned_total,
            "overpaid_total": overpaid_total,
            "profit": net_profit,
            "currency": currency
        })

    stats = compute_stats(deposits, withdrawals, investment_rows)
    current_balance = compute_account_balance(transactions)
    stats["current_balance"] = current_balance
    stats["total_profit"] = sum(row["profit"] for row in investment_rows if row["profit"] is not None)

    # Get currency from first available transaction
    currency = None
    if transactions:
        for tx in transactions:
            if "amount" in tx and "currency" in tx["amount"]:
                currency = tx["amount"]["currency"]
                break

    investment_rows.sort(key=get_sort_date, reverse=True)

    return {
        "stats": stats,
        "investment_rows": investment_rows,
        "deposits": deposits,
        "withdrawals": withdrawals,
        "currency": currency
    }


@app.route("/")
def dashboard():
    """Dashboard showing all accounts"""
    accounts = load_accounts_from_config()

    if not accounts:
        return render_template("error.html",
                             error="No accounts configured. Please create config.json from config.json.example")

    account_summaries = []
    for account in accounts:
        try:
            data = process_account_data(account)
            account_summaries.append({
                "id": account.id,
                "name": account.name,
                "currency": data["currency"],
                "total_profit": data["stats"]["total_profit"],
                "current_balance": data["stats"]["current_balance"],
                "num_investments": data["stats"]["num_investments"]
            })
        except Exception as e:
            app.logger.error(f"Error processing account {account.id}: {e}")
            account_summaries.append({
                "id": account.id,
                "name": account.name,
                "error": str(e)
            })

    return render_template("dashboard.html", accounts=account_summaries)


@app.route("/detail/<account_id>")
def account_detail(account_id):
    """Detail view for a specific account"""
    accounts = load_accounts_from_config()
    account = next((acc for acc in accounts if acc.id == account_id), None)

    if not account:
        abort(404, description=f"Account '{account_id}' not found")

    try:
        data = process_account_data(account)
        return render_template("detail.html",
                             account=account,
                             stats=data["stats"],
                             investment_rows=data["investment_rows"],
                             deposits=data["deposits"],
                             withdrawals=data["withdrawals"],
                             currency=data["currency"])
    except Exception as e:
        app.logger.error(f"Error loading account {account_id}: {e}")
        abort(500, description=f"Error loading account data: {e}")


@app.route("/api/refresh/<account_id>")
def refresh_account(account_id):
    """Fetch fresh transaction data for a specific account"""
    try:
        accounts = load_accounts_from_config()
        account = next((acc for acc in accounts if acc.id == account_id), None)

        if not account:
            return jsonify({"error": f"Account '{account_id}' not found"}), 404

        # Initialize bank API client
        client = get_bank_client(
            account.bank,
            account.api_token,
            account.account_id
        )

        # Fetch all transactions
        transactions = client.fetch_all_transactions()
        if transactions is None:
            return jsonify({"error": "Failed to fetch transactions from API"}), 500

        # Save to file
        success = client.save_transactions(transactions, account.transactions_file)
        if not success:
            return jsonify({"error": "Failed to save transactions"}), 500

        return jsonify({
            "success": True,
            "message": f"Successfully updated {len(transactions)} transactions for {account.name}",
            "count": len(transactions)
        })

    except Exception as e:
        app.logger.error(f"Error refreshing account {account_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
