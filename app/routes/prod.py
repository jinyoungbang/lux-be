from flask import Blueprint, request, jsonify
from datetime import datetime
import json
from datetime import timedelta
from dateutil.relativedelta import relativedelta  # Use dateutil for date operations
import os
import openai


from services.mongo import MongoService

prod_bp = Blueprint("prod", __name__)
mongo = MongoService()
mongo.connect()

with open("output.json", "r") as file:
    data = json.load(file)

transaction_data = data["data"]

for transaction in transaction_data:
    transaction["date"] = datetime.strptime(
        transaction["date"], "%a, %d %b %Y %H:%M:%S %Z"
    )


# Helper function to filter transactions within a date range
def filter_transactions(transactions, start_date, end_date):
    return [
        transaction
        for transaction in transactions
        if start_date <= transaction["date"] <= end_date
    ]


# Edits transaction amount
@prod_bp.route("/api/prod/transaction/<transaction_id>", methods=["PUT"])
def update_transaction_amount(transaction_id):
    new_amount = request.json.get("modifiedAmount")

    if new_amount is None:
        return (
            jsonify(
                {"error": "The 'modifiedAmount' field is missing from the request."}
            ),
            400,
        )

    # Use the transaction_id to find the transaction in the database
    transaction = mongo.find_transaction_by_id(transaction_id)

    if transaction is None:
        return jsonify({"error": "Transaction not found."}), 404

    # Update the 'modifiedAmount' field in the transaction document
    transaction["modified_amount"] = new_amount

    # Save the updated document back to the database
    success = mongo.update_transaction(transaction_id, transaction)

    if success:
        return jsonify({"message": "Transaction amount updated successfully."})
    else:
        return jsonify({"error": "Failed to update transaction amount."}), 500


@prod_bp.route("/api/prod/toggle-transaction/<transaction_id>", methods=["PUT"])
def toggle_transaction(transaction_id):
    # Use the transaction_id to find the transaction in the database
    transaction = mongo.find_transaction_by_id(transaction_id)

    if transaction is None:
        return jsonify({"error": "Transaction not found."}), 404

    # Check if 'is_hidden' field exists in the transaction document
    if "is_hidden" in transaction:
        # If it exists, toggle its value (from True to False or vice versa)
        transaction["is_hidden"] = not transaction["is_hidden"]
    else:
        # If it doesn't exist, set it to True
        transaction["is_hidden"] = True

    # Save the updated document back to the database
    success = mongo.update_transaction(transaction_id, transaction)

    if success:
        return jsonify(
            {"message": "Transaction 'is_hidden' field toggled successfully."}
        )
    else:
        return jsonify({"error": "Failed to toggle 'is_hidden' field."}), 500


# @insights_bp.route("/api/insights/spending/monthly", methods=["GET"])
# def get_daily_spending():
#     date_str = request.args.get("date")
#     date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")

#     start_date = date
#     end_date = date + timedelta(days=1)

#     daily_transactions = filter_transactions(transaction_data, start_date, end_date)

#     total_spending = sum(transaction["amount"] for transaction in daily_transactions)

#     return jsonify({"date": date_str, "total_spending": total_spending})


# @insights_bp.route("/api/insights/spending/weekly", methods=["GET"])
# def get_weekly_spending():
#     date_str = request.args.get("date")
#     date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")

#     start_date = date - timedelta(days=date.weekday())  # Start of the week (Monday)
#     end_date = start_date + timedelta(days=7)

#     weekly_transactions = filter_transactions(transaction_data, start_date, end_date)

#     total_spending = sum(transaction["amount"] for transaction in weekly_transactions)

#     return jsonify(
#         {
#             "start_date": start_date.strftime("%a, %d %b %Y"),
#             "end_date": end_date.strftime("%a, %d %b %Y"),
#             "total_spending": total_spending,
#         }
#     )


# # Endpoint to get monthly spending
# @insights_bp.route("/api/insights/spending/monthly", methods=["GET"])
# def get_monthly_spending():
#     date_str = request.args.get("date")
#     date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")

#     start_date = date.replace(day=1)
#     if start_date.month == 12:
#         end_date = start_date.replace(year=start_date.year + 1, month=1)
#     else:
#         end_date = start_date.replace(month=start_date.month + 1)

#     monthly_transactions = filter_transactions(transaction_data, start_date, end_date)

#     total_spending = sum(transaction["amount"] for transaction in monthly_transactions)

#     return jsonify(
#         {
#             "start_date": start_date.strftime("%a, %d %b %Y"),
#             "end_date": end_date.strftime("%a, %d %b %Y"),
#             "total_spending": total_spending,
#         }
#     )


@prod_bp.route("/api/prod/insights/transactions/monthly", methods=["GET"])
def get_all_monthly_transactions():
    date_str = request.args.get("date")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify(
            {"error": "Invalid date format. Use the format: 'YYYY-MM-DD'"}, 400
        )

    # Fetch all transactions from MongoDB and convert date strings to datetime objects
    all_transactions = mongo.get_all_transactions()

    for transaction in all_transactions:
        transaction["date"] = datetime.strptime(
            transaction["date"], "%a, %d %b %Y %H:%M:%S %Z"
        )

    # Calculate the start and end dates for the given month
    start_date = date.replace(day=1)
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)

    monthly_transactions = filter_transactions(all_transactions, start_date, end_date)

    return jsonify(monthly_transactions)


@prod_bp.route("/api/prod/insights/transactions/last-6-months", methods=["GET"])
def get_last_6_monthly_spending():
    date_str = request.args.get("date")

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify(
            {"error": "Invalid date format. Use the format: 'YYYY-MM-DD'"}, 400
        )

    # Fetch all transactions from MongoDB
    all_transactions = mongo.get_all_transactions()
    for transaction in all_transactions:
        transaction["date"] = datetime.strptime(
            transaction["date"], "%a, %d %b %Y %H:%M:%S %Z"
        )

    # Initialize a list to store the aggregated spending for the last 6 months
    aggregated_data = []

    # Calculate the start and end dates for the last 6 months
    for i in range(6):
        end_date = date
        start_date = date - relativedelta(months=1)
        date = start_date

        # Convert the dates to datetime objects
        start_date = datetime(start_date.year, start_date.month + 1, start_date.day)
        end_date = datetime(end_date.year, end_date.month + 1, end_date.day)

        # Filter transactions that fall within the date range
        monthly_transactions = [
            transaction
            for transaction in all_transactions
            if (
                start_date <= transaction["date"] <= end_date
                and transaction["amount"] > 0
                and (
                    "is_hidden" not in transaction
                    or ("is_hidden" in transaction and not transaction["is_hidden"])
                )
            )
        ]
        
        total_spending = 0

        for transaction in monthly_transactions:
            if "modified_amount" in transaction and transaction["amount"] != transaction["modified_amount"]:
                total_spending += transaction["modified_amount"]
            else:
                total_spending += transaction["amount"]
                
        aggregated_data.append(
            {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_spending": round(total_spending, 2),
            }
        )

    # Reverse the list to have the data in chronological order
    aggregated_data.reverse()

    return jsonify(aggregated_data)


@prod_bp.route("/api/prod/insights/report", methods=["GET"])
def get_monthly_insight_report():
    date_str = request.args.get("date")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify(
            {"error": "Invalid date format. Use the format: 'YYYY-MM-DD'"}, 400
        )

    # Fetch all transactions from MongoDB and convert date strings to datetime objects
    all_transactions = mongo.get_all_transactions()

    for transaction in all_transactions:
        transaction["date"] = datetime.strptime(
            transaction["date"], "%a, %d %b %Y %H:%M:%S %Z"
        )

    # Calculate the start and end dates for the given month
    start_date = date.replace(day=1)
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)

    monthly_transactions = filter_transactions(all_transactions, start_date, end_date)

    monthly_transactions_to_analyze = []

    for transaction in monthly_transactions:
        data_to_append = {}
        data_to_append["amount"] = transaction["amount"]
        data_to_append["category"] = transaction["personal_finance_category"]["primary"]
        data_to_append["name"] = transaction["name"]
        monthly_transactions_to_analyze.append(data_to_append)

    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant providing personal financial advice. You want to give the best tips for a person to help improve their money management and build their net worth over time. I want it to be brief and give the user good financial advice as well. Try keep it concise. Ideally, bullet point styles, to the point but informative.",
            },
            {
                "role": "user",
                "content": "Give me things I'm doing well and three things im not in terms of financial advice: "
                + str(monthly_transactions_to_analyze),
            },
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0.05,
        presence_penalty=0,
    )

    return jsonify(response)

@prod_bp.route("/api/prod/insights/card", methods=["GET"])
def get_card_recommendations():
    date_str = request.args.get("date")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify(
            {"error": "Invalid date format. Use the format: 'YYYY-MM-DD'"}, 400
        )

    # Fetch all transactions from MongoDB and convert date strings to datetime objects
    all_transactions = mongo.get_all_transactions()

    for transaction in all_transactions:
        transaction["date"] = datetime.strptime(
            transaction["date"], "%a, %d %b %Y %H:%M:%S %Z"
        )

    # Calculate the start and end dates for the given month
    start_date = date.replace(day=1)
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)

    monthly_transactions = filter_transactions(all_transactions, start_date, end_date)

    monthly_transactions_to_analyze = []

    for transaction in monthly_transactions:
        data_to_append = {}
        data_to_append["amount"] = transaction["amount"]
        data_to_append["category"] = transaction["personal_finance_category"]["primary"]
        data_to_append["name"] = transaction["name"]
        monthly_transactions_to_analyze.append(data_to_append)

    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant providing personal financial advice. You want to give the best tips for a person to help improve their money management and build their net worth over time. I want it to be brief and give the user good financial advice as well. Try keep it concise. Ideally, bullet point styles, to the point but informative.",
            },
            {
                "role": "user",
                "content": "Give me things I'm doing well and three things im not in terms of financial advice: "
                + str(monthly_transactions_to_analyze),
            },
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0.05,
        presence_penalty=0,
    )

    return jsonify(response)
