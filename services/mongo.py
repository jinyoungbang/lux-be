from pymongo.mongo_client import MongoClient
import os
from dotenv import load_dotenv
from bson import ObjectId  # Import ObjectId from the bson module
from dateutil.parser import parse  # Import the date parser


load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")


class MongoService:
    """Manages connections to MongoDB."""

    def __init__(self):
        """Establishes connection to MongoDB server"""
        self.user = MONGO_USER
        self.password = MONGO_PASS
        self.uri = f"mongodb+srv://{self.user}:{self.password}@cluster0.hdrfc1v.mongodb.net/?retryWrites=true&w=majority"
        self.client = MongoClient(self.uri)
        self.db = None

    def connect(self):
        # Send a ping to confirm a successful connection
        try:
            self.client.admin.command("ping")
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

        self.db = self.client.db

    def insert_transaction(self, transaction):
        try:
            # Replace 'your_collection' with the actual name of your MongoDB collection
            collection = self.db.transactions
            result = collection.insert_one(transaction)
            return result
        except Exception as e:
            print(f"Error inserting transaction: {e}")
            return None

    def find_transaction_by_id(self, transaction_id):
        try:
            # Replace 'your_collection' with the actual name of your MongoDB collection
            collection = self.db.transactions
            return collection.find_one({"transaction_id": transaction_id})
        except Exception as e:
            print(f"Error finding transaction: {e}")
            return None

    def update_transaction(self, transaction_id, updated_transaction):
        try:
            # Replace 'your_collection' with the actual name of your MongoDB collection
            collection = self.db.transactions
            result = collection.update_one(
                {"transaction_id": transaction_id}, {"$set": updated_transaction}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating transaction: {e}")
            return False
        
    def find_transactions_in_date_range(self, start_date, end_date):
        try:
            # Replace 'your_collection' with the actual name of your MongoDB collection
            collection = self.db.transactions
            start_date = parse(start_date)
            end_date = parse(end_date)

            # Create a query to find transactions within the specified date range
            query = {
                "date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            # Use the find method to retrieve transactions that match the query
            transactions = collection.find(query)

            # Convert the result to a list of dictionaries
            return list(transactions)
        except Exception as e:
            print(f"Error finding transactions in date range: {e}")
            return []
        
    def get_all_transactions(self):
        try:
            # Replace 'your_collection' with the actual name of your MongoDB collection
            collection = self.db.transactions

            # Use the find method to retrieve all transactions from the collection
            transactions = collection.find({}, {'_id': False})

            # Convert the result to a list of dictionaries
            return list(transactions)
        except Exception as e:
            print(f"Error fetching all transactions: {e}")
            return []