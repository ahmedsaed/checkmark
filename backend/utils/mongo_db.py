"""
MongoDB connection utilities for Checkmark Platform
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os


class MongoDBConfig:
    """MongoDB connection configuration"""

    def __init__(self):
        self.connection_string = os.getenv(
            "MONGODB_URI",
            "mongodb://localhost:27017"
        )
        self.database_name = os.getenv("MONGODB_DATABASE", "checkmark")
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[Any] = None

    async def connect(self) -> AsyncIOMotorClient:
        """Establish connection to MongoDB"""
        if self.client is None:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Set connection timeout
            self.client.server_info_timeout = 5
            
            # Handle connection events
            self.client.start_session()
            
        return self.client

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    @property
    def database(self):
        """Get database reference"""
        if self.db is None:
            raise ConnectionError("Not connected to MongoDB")
        return self.db

    @property
    def collection(self, name: str):
        """Get collection reference"""
        if self.db is None:
            raise ConnectionError("Not connected to MongoDB")
        return self.db[name]


# Singleton instance
_mongo_config = None


def get_mongo_config() -> MongoDBConfig:
    """Get the singleton MongoDBConfig instance"""
    global _mongo_config
    if _mongo_config is None:
        _mongo_config = MongoDBConfig()
    return _mongo_config


async def get_database() -> Any:
    """Get MongoDB database instance"""
    config = get_mongo_config()
    await config.connect()
    return config.database


async def close_database() -> None:
    """Close MongoDB database connection"""
    config = get_mongo_config()
    if config.client:
        config.disconnect()
