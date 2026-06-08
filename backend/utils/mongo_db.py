"""
MongoDB connection utilities for Checkmark Platform.

Provides a singleton MongoDBConfig that manages the async Motor client
lifecycle (connect on first use, close on shutdown).
"""

from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings


class MongoDBConfig:
    """Singleton MongoDB connection manager."""

    def __init__(self):
        self.connection_string = settings.mongodb_uri
        self.database_name = settings.mongodb_database
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> AsyncIOMotorClient:
        """Establish connection to MongoDB (idempotent)."""
        if self._client is None:
            self._client = AsyncIOMotorClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
            )
            self._db = self._client[self.database_name]
            # Verify connectivity
            await self._client.admin.command("ping")
        return self._client

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get database reference."""
        if self._db is None:
            raise ConnectionError("Not connected to MongoDB — call connect() first")
        return self._db

    def get_collection(self, name: str) -> Any:
        """Get a collection reference by name."""
        return self.database[name]


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_mongo_config: Optional[MongoDBConfig] = None


def get_mongo_config() -> MongoDBConfig:
    """Return the singleton MongoDBConfig instance."""
    global _mongo_config
    if _mongo_config is None:
        _mongo_config = MongoDBConfig()
    return _mongo_config


async def get_database() -> AsyncIOMotorDatabase:
    """Convenience: connect and return the database."""
    config = get_mongo_config()
    await config.connect()
    return config.database


async def close_database() -> None:
    """Convenience: close the database connection."""
    config = get_mongo_config()
    if config._client:
        await config.disconnect()
