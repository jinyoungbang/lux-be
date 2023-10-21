from flask import Blueprint, request, jsonify
from datetime import datetime
import json
from datetime import timedelta

insights_bp = Blueprint("insights", __name__)

with open("data.json", "r") as file:
    data = json.load(file)

transaction_data = data["data"]

for transaction in transaction_data:
    transaction['date'] = datetime.strptime(transaction['date'], '%a, %d %b %Y %H:%M:%S %Z')


# Helper function to filter transactions within a date range
def filter_transactions(transactions, start_date, end_date):
    return [
        transaction
        for transaction in transactions
        if start_date <= transaction["date"] <= end_date
    ]

@insights_bp.route("/api/insights/spending/monthly", methods=["GET"])
def get_daily_spending():
    date_str = request.args.get("date")
    date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")

    start_date = date
    end_date = date + timedelta(days=1)

    daily_transactions = filter_transactions(transaction_data, start_date, end_date)

    total_spending = sum(transaction["amount"] for transaction in daily_transactions)

    return jsonify({"date": date_str, "total_spending": total_spending})


@insights_bp.route("/api/insights/spending/weekly", methods=["GET"])
def get_weekly_spending():
    date_str = request.args.get("date")
    date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")

    start_date = date - timedelta(days=date.weekday())  # Start of the week (Monday)
    end_date = start_date + timedelta(days=7)

    weekly_transactions = filter_transactions(transaction_data, start_date, end_date)

    total_spending = sum(transaction["amount"] for transaction in weekly_transactions)

    return jsonify(
        {
            "start_date": start_date.strftime("%a, %d %b %Y"),
            "end_date": end_date.strftime("%a, %d %b %Y"),
            "total_spending": total_spending,
        }
    )


# Endpoint to get monthly spending
@insights_bp.route("/api/insights/spending/monthly", methods=["GET"])
def get_monthly_spending():
    date_str = request.args.get("date")
    date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")

    start_date = date.replace(day=1)
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)

    monthly_transactions = filter_transactions(transaction_data, start_date, end_date)

    total_spending = sum(transaction["amount"] for transaction in monthly_transactions)

    return jsonify(
        {
            "start_date": start_date.strftime("%a, %d %b %Y"),
            "end_date": end_date.strftime("%a, %d %b %Y"),
            "total_spending": total_spending,
        }
    )


@insights_bp.route("/api/insights/transactions/monthly", methods=["GET"])
def get_all_monthly_transactions():
    date_str = request.args.get("date")
    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format (YYYY-MM-DD)"}, 400)

    start_date = date.replace(day=1)
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)

    monthly_transactions = filter_transactions(transaction_data, start_date, end_date)

    return jsonify(monthly_transactions)

@insights_bp.route("/api/insights/transactions/last-6-months", methods=["GET"])
def get_last_6_monthly_spending():
    date_str = request.args.get("date")
    
    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format (YYYY-MM-DD)"}, 400)

    # Initialize a list to store the aggregated spending for the last 6 months
    aggregated_data = []

    date = date.replace(month=date.month+1)

    for _ in range(6):
        end_date = date.replace(day=1)
        
        if end_date.month == 1:
            start_date = end_date.replace(year=end_date.year - 1, month=12)
        else:
            start_date = end_date.replace(month=end_date.month - 1)

        monthly_transactions = filter_transactions(transaction_data, start_date, end_date)

        total_spending = sum(transaction["amount"] for transaction in monthly_transactions)

        aggregated_data.append({
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_spending": total_spending,
        })

        # Update the date to the previous month
        date = start_date

    # Reverse the list to have the data in chronological order
    aggregated_data.reverse()

    return jsonify(aggregated_data)