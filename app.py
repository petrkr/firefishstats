import os
import logging
from flask import Flask, render_template, jsonify, flash, redirect, url_for
from utils import load_transactions, classify_transactions, compute_stats, compute_account_balance
from api_client import CreditasAPIClient
from config import config
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

@app.route("/")
def index():
    known_accounts = app.config['KNOWN_ACCOUNTS']
    transactions = load_transactions(app.config['TRANSACTIONS_FILE'])
    deposits, withdrawals, investments, returns, overpayments = classify_transactions(transactions, known_accounts)

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

        investment_rows.append({
            "remittance": remit,
            "investments": inv_list,
            "returns": ret_list,
            "overpayments": overpay_list,
            "invested_total": invested_total,
            "returned_total": returned_total,
            "overpaid_total": overpaid_total,
            "profit": net_profit
        })

    stats = compute_stats(deposits, withdrawals, investment_rows)
    current_balance = compute_account_balance(transactions)
    stats["current_balance"] = current_balance
    stats["total_profit"] = sum(row["profit"] for row in investment_rows if row["profit"] is not None)

    investment_rows.sort(key=get_sort_date, reverse=True)

    return render_template("index.html", stats=stats, investment_rows=investment_rows,
                       deposits=deposits, withdrawals=withdrawals)


@app.route("/api/refresh")
def refresh_data():
    """Fetch fresh transaction data from Creditas API"""
    try:
        # Check if API credentials are configured
        if not app.config['CREDITAS_API_TOKEN'] or not app.config['CREDITAS_ACCOUNT_ID']:
            return jsonify({"error": "API credentials not configured"}), 500
        
        # Initialize API client
        client = CreditasAPIClient(
            app.config['CREDITAS_API_TOKEN'],
            app.config['CREDITAS_ACCOUNT_ID'],
            app.config['CREDITAS_API_BASE_URL']
        )
        
        # Fetch all transactions
        transactions = client.fetch_all_transactions()
        if transactions is None:
            return jsonify({"error": "Failed to fetch transactions from API"}), 500
        
        # Save to file
        success = client.save_transactions(transactions, app.config['TRANSACTIONS_FILE'])
        if not success:
            return jsonify({"error": "Failed to save transactions"}), 500
        
        return jsonify({
            "success": True,
            "message": f"Successfully updated {len(transactions)} transactions",
            "count": len(transactions)
        })
        
    except Exception as e:
        app.logger.error(f"Error refreshing data: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/status")
def api_status():
    """Check API configuration status"""
    has_token = bool(app.config.get('CREDITAS_API_TOKEN'))
    has_account_id = bool(app.config.get('CREDITAS_ACCOUNT_ID'))
    
    return jsonify({
        "api_configured": has_token and has_account_id,
        "has_token": has_token,
        "has_account_id": has_account_id
    })


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
