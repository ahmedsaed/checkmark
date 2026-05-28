#!/usr/bin/env python3
"""
CLI script for managing admin accounts in the Checkmark backend.

Usage:
    python scripts/manage_admins.py add    <username> <password>
    python scripts/manage_admins.py list
    python scripts/manage_admins.py update <username> <new_password>
    python scripts/manage_admins.py delete <username>
"""

import asyncio
import os
import sys

# Ensure backend package imports resolve when running the script directly.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.mongo_db import get_database
from auth import hash_password


async def add_admin(username: str, password: str) -> None:
    from datetime import datetime

    db = await get_database()
    admins_col = db["admins"]

    existing = await admins_col.find_one({"username": username})
    if existing:
        print(f"ERROR: Admin '{username}' already exists (id: {existing['_id']})")
        sys.exit(1)

    try:
        hashed = hash_password(password)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    result = await admins_col.insert_one({
        "username": username,
        "password_hash": hashed,
        "created_at": datetime.utcnow(),
    })
    print(f"OK: Admin '{username}' created (id: {result.inserted_id})")


async def list_admins() -> None:
    db = await get_database()
    admins_col = db["admins"]

    admins = []
    async for doc in admins_col.find():
        admins.append({
            "id": str(doc["_id"]),
            "username": doc["username"],
            "created_at": doc.get("created_at"),
        })

    if not admins:
        print("No admins found.")
        return

    print(f"{'ID':<40} {'Username':<20} {'Created At'}")
    print("-" * 70)
    for a in admins:
        created = a["created_at"].strftime("%Y-%m-%d %H:%M:%S") if a["created_at"] else "N/A"
        print(f"{a['id']:<40} {a['username']:<20} {created}")


async def update_admin(username: str, new_password: str) -> None:
    db = await get_database()
    admins_col = db["admins"]

    try:
        hashed = hash_password(new_password)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    result = await admins_col.update_one(
        {"username": username},
        {"$set": {"password_hash": hashed}},
    )
    if result.matched_count == 0:
        print(f"ERROR: Admin '{username}' not found")
        sys.exit(1)
    print(f"OK: Password updated for '{username}'")


async def delete_admin(username: str) -> None:
    db = await get_database()
    admins_col = db["admins"]

    result = await admins_col.delete_one({"username": username})
    if result.deleted_count == 0:
        print(f"ERROR: Admin '{username}' not found")
        sys.exit(1)
    print(f"OK: Admin '{username}' deleted")


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "add":
        if len(sys.argv) != 4:
            print("Usage: manage_admins.py add <username> <password>")
            sys.exit(1)
        await add_admin(sys.argv[2], sys.argv[3])
    elif command == "list":
        await list_admins()
    elif command == "update":
        if len(sys.argv) != 4:
            print("Usage: manage_admins.py update <username> <new_password>")
            sys.exit(1)
        await update_admin(sys.argv[2], sys.argv[3])
    elif command == "delete":
        if len(sys.argv) != 3:
            print("Usage: manage_admins.py delete <username>")
            sys.exit(1)
        await delete_admin(sys.argv[2])
    else:
        print(f"ERROR: Unknown command '{command}'")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
