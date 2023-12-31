from flask import Blueprint, jsonify, request
import json
import datetime
from datetime import date

import os
import time
import plaid
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from plaid.model.payment_amount import PaymentAmount
from plaid.model.payment_amount_currency import PaymentAmountCurrency
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.recipient_bacs_nullable import RecipientBACSNullable
from plaid.model.payment_initiation_address import PaymentInitiationAddress
from plaid.model.payment_initiation_recipient_create_request import (
    PaymentInitiationRecipientCreateRequest,
)
from plaid.model.payment_initiation_payment_create_request import (
    PaymentInitiationPaymentCreateRequest,
)
from plaid.model.payment_initiation_payment_get_request import (
    PaymentInitiationPaymentGetRequest,
)
from plaid.model.link_token_create_request_payment_initiation import (
    LinkTokenCreateRequestPaymentInitiation,
)
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.asset_report_create_request import AssetReportCreateRequest
from plaid.model.asset_report_create_request_options import (
    AssetReportCreateRequestOptions,
)
from plaid.model.asset_report_user import AssetReportUser
from plaid.model.asset_report_get_request import AssetReportGetRequest
from plaid.model.asset_report_pdf_get_request import AssetReportPDFGetRequest
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.identity_get_request import IdentityGetRequest
from plaid.model.investments_transactions_get_request_options import (
    InvestmentsTransactionsGetRequestOptions,
)
from plaid.model.investments_transactions_get_request import (
    InvestmentsTransactionsGetRequest,
)
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.transfer_authorization_create_request import (
    TransferAuthorizationCreateRequest,
)
from plaid.model.transfer_create_request import TransferCreateRequest
from plaid.model.transfer_get_request import TransferGetRequest
from plaid.model.transfer_network import TransferNetwork
from plaid.model.transfer_type import TransferType
from plaid.model.transfer_authorization_user_in_request import (
    TransferAuthorizationUserInRequest,
)
from plaid.model.ach_class import ACHClass
from plaid.model.transfer_create_idempotency_key import TransferCreateIdempotencyKey
from plaid.model.transfer_user_address_in_request import TransferUserAddressInRequest
from plaid.model.transactions_get_request import TransactionsGetRequest

plaid_bp = Blueprint("plaid", __name__)


def empty_to_none(field):
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value


# Fill in your Plaid API keys - https://dashboard.plaid.com/account/keys
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions").split(",")
PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US").split(",")
PLAID_REDIRECT_URI = "http://localhost:3000/"


configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        "clientId": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
    },
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

products = []
for product in PLAID_PRODUCTS:
    products.append(Products(product))


# We store the access_token in memory - in production, store it in a secure
# persistent data store.
access_token = "access-sandbox-5adf8553-c2cf-4f50-8c71-64081370a218"

# The transfer_id is only relevant for Transfer ACH product.
# We store the transfer_id in memory - in production, store it in a secure
# persistent data store.
transfer_id = None
item_id = None


@plaid_bp.route("/api/plaid/create_link_token", methods=["POST"])
def create_link_token():
    plaid_request = LinkTokenCreateRequest(
        products=products,
        client_name="Lux",
        country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
        language="en",
        user=LinkTokenCreateRequestUser(client_user_id=str(time.time())),
    )

    plaid_request["redirect_uri"] = PLAID_REDIRECT_URI
    # create link token
    response = client.link_token_create(plaid_request)
    return jsonify(response.to_dict())


@plaid_bp.route("/api/plaid/exchange_public_token", methods=["POST"])
def exchange_public_token():
    global access_token
    data = request.get_json()
    public_token = data["public_token"]
    plaid_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(plaid_request)
    # These values should be saved to a persistent database and
    # associated with the currently signed-in user
    access_token = response["access_token"]
    item_id = response["item_id"]
    print(access_token)
    return jsonify({"public_token_exchange": "complete"})


@plaid_bp.route("/api/plaid/info", methods=["POST"])
def info():
    global access_token
    global item_id
    return jsonify(
        {"item_id": item_id, "access_token": access_token, "products": PLAID_PRODUCTS}
    )


@plaid_bp.route("/api/plaid/accounts", methods=["GET"])
def get_accounts():
    try:
        request = AccountsGetRequest(access_token=access_token)
        accounts_response = client.accounts_get(request)
    except plaid.ApiException as e:
        response = json.loads(e.body)
        return jsonify(
            {
                "error": {
                    "status_code": e.status,
                    "display_message": response["error_message"],
                    "error_code": response["error_code"],
                    "error_type": response["error_type"],
                }
            }
        )
    return jsonify(accounts_response.to_dict())


@plaid_bp.route("/api/plaid/transactions")
def get_transactions():
    global access_token
    try:
        start_date = date(2023, 1, 1)
        end_date = date(2023, 10, 31)

        # Define the transaction request
        transaction_request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options={
                "count": 500
            }
        )

        # Call the Plaid API to get transactions
        response = client.transactions_get(transaction_request).to_dict()

        # Extract the transactions
        transactions = response["transactions"]
        print(len(transactions))
        # print(type(transactions["data"]))
        return jsonify({"data": transactions})
    except plaid.ApiException as e:
        response = json.loads(e.body)
        return jsonify(
            {
                "error": {
                    "status_code": e.status,
                    "display_message": response["error_message"],
                    "error_code": response["error_code"],
                    "error_type": response["error_type"],
                }
            }
        )

@plaid_bp.route("/api/plaid/migrate-transaction-data")
def migrate_transaction_data():
    global access_token
    try:
        start_date = date(2023, 2, 1)
        end_date = date(2023, 10, 30)

        # Define the transaction request
        transaction_request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )

        # Call the Plaid API to get transactions
        response = client.transactions_get(transaction_request).to_dict()

        # Extract the transactions
        transactions = response["transactions"]
        dates = [data["date"] for data in transactions]
        print(len(transactions))
        # print(type(transactions["data"]))
        return jsonify({"data": transactions})
    except plaid.ApiException as e:
        response = json.loads(e.body)
        return jsonify(
            {
                "error": {
                    "status_code": e.status,
                    "display_message": response["error_message"],
                    "error_code": response["error_code"],
                    "error_type": response["error_type"],
                }
            }
        )