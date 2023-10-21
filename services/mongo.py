from pymongo.mongo_client import MongoClient
import os
from dotenv import load_dotenv

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

    # def get_all_data(self):
    #     """fetches all data in specified collection"""
    #     try:
    #         self.users = self.vault.users.find()  # parameterize this
    #         # assert(self.users.count() != 0)   # this doesn't work, fix silent failure!!
    #     except Exception as e:
    #         print(e)

    #     # for u in self.users:
    #     #    print(u)
    #     return self.users

    #     # insert more CRUD methods here
