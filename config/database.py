from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

load_dotenv()

class DatabaseManager:
    _instance = None
    _client = None
    _db = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.connect()
    
    def connect(self, max_retries=3, retry_delay=5):
        """Connect to MongoDB with retry mechanism"""
        MONGO_URI = "mongodb+srv://toolminesai:tY9uqb1WnxVf7A6L@mycluster0.u8ntx.mongodb.net/?retryWrites=true&w=majority&appName=Mycluster0"
        
        for attempt in range(max_retries):
            try:
                if self._client is not None:
                    self._client.close()
                
                self._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                # Test the connection
                self._client.admin.command('ping')
                self._db = self._client['jarvis_db']
                print("Successfully connected to MongoDB!")
                return self._db
            
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                if attempt < max_retries - 1:
                    print(f"Connection attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to connect to MongoDB after {max_retries} attempts: {str(e)}")
                    raise
    
    def get_database(self):
        """Get database connection, reconnecting if necessary"""
        try:
            # Test if connection is still alive
            self._client.admin.command('ping')
            return self._db
        except Exception:
            # Connection lost, try to reconnect
            return self.connect()
    
    def close(self):
        """Close the database connection"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None

# Initialize database manager
db_manager = DatabaseManager.get_instance()

# Get database connection
def get_database():
    return db_manager.get_database()

# Initialize database connection
db = get_database()