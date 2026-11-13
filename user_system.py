#!/usr/bin/env python3
"""A lightweight user management system built with Python."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DEFAULT_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "users.json")


class UserSystem:
    def __init__(self, data_file: str = DEFAULT_DATA_FILE) -> None:
        self.data_file = data_file
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        if not os.path.exists(data_file):
            self._write_users([])

    def _read_users(self) -> List[Dict[str, Any]]:
        try:
            with open(self.data_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    return data
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        self._write_users([])
        return []

    def _write_users(self, users: List[Dict[str, Any]]) -> None:
        with open(self.data_file, "w", encoding="utf-8") as fh:
            json.dump(users, fh, indent=2)
            fh.write("\n")

    @staticmethod
    def _hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
        if salt is None:
            salt = os.urandom(16).hex()
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            200_000,
        )
        return {"salt": salt, "hash": derived_key.hex()}

    def register(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        is_admin: bool = False,
    ) -> Dict[str, Any]:
        username = username.strip()
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        users = self._read_users()
        if any(user["username"].lower() == username.lower() for user in users):
            raise ValueError(f"The username '{username}' already exists.")

        user = {
            "username": username,
            "email": email.strip() if email else "",
            "is_admin": bool(is_admin),
            "password": self._hash_password(password),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        users.append(user)
        self._write_users(users)
        return {
            "username": user["username"],
            "email": user["email"],
            "is_admin": user["is_admin"],
            "created_at": user["created_at"],
        }

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        username = username.strip()
        users = self._read_users()
        for user in users:
            if user["username"].lower() != username.lower():
                continue
            stored_hash = user["password"]["hash"]
            stored_salt = user["password"]["salt"]
            derived_key = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(stored_salt),
                200_000,
            )
            if derived_key.hex() == stored_hash:
                return {
                    "username": user["username"],
                    "email": user.get("email", ""),
                    "is_admin": user.get("is_admin", False),
                    "created_at": user.get("created_at"),
                }
        return None

    def list_users(self) -> List[Dict[str, Any]]:
        users = self._read_users()
        return [
            {
                "username": user["username"],
                "email": user.get("email", ""),
                "is_admin": user.get("is_admin", False),
                "created_at": user.get("created_at"),
            }
            for user in users
        ]

    def delete_user(self, username: str) -> bool:
        username = username.strip()
        users = self._read_users()
        original_length = len(users)
        users = [user for user in users if user["username"].lower() != username.lower()]
        if len(users) == original_length:
            return False
        self._write_users(users)
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> Dict[str, Any]:
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters long.")

        user = self.authenticate(username, old_password)
        if user is None:
            raise ValueError("Old password is invalid.")

        users = self._read_users()
        for item in users:
            if item["username"].lower() == username.lower():
                item["password"] = self._hash_password(new_password)
                self._write_users(users)
                return {"username": item["username"], "updated": True}

        raise ValueError(f"User '{username}' not found.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A lightweight user management system.")
    parser.add_argument(
        "--data-file",
        default=DEFAULT_DATA_FILE,
        help="Path to the JSON file that stores users.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    register_parser = subparsers.add_parser("register", help="Create a new user account.")
    register_parser.add_argument("username")
    register_parser.add_argument("password")
    register_parser.add_argument("--email", default="")
    register_parser.add_argument("--admin", action="store_true", help="Grant administrator privileges.")

    login_parser = subparsers.add_parser("login", help="Authenticate a user.")
    login_parser.add_argument("username")
    login_parser.add_argument("password")

    list_parser = subparsers.add_parser("list-users", help="List all users in the system.")
    delete_parser = subparsers.add_parser("delete-user", help="Delete a user account.")
    delete_parser.add_argument("username")

    change_parser = subparsers.add_parser("change-password", help="Change a user's password.")
    change_parser.add_argument("username")
    change_parser.add_argument("old_password")
    change_parser.add_argument("new_password")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    system = UserSystem(data_file=args.data_file)

    try:
        if args.command == "register":
            user = system.register(args.username, args.password, args.email, args.admin)
            print(f"User '{user['username']}' registered successfully.")
            print(json.dumps(user, indent=2))
            return 0

        if args.command == "login":
            user = system.authenticate(args.username, args.password)
            if user is None:
                print("Login failed: invalid username or password.")
                return 1
            print(f"Login successful for '{user['username']}'.")
            print(json.dumps(user, indent=2))
            return 0

        if args.command == "list-users":
            users = system.list_users()
            if not users:
                print("No users found.")
                return 0
            print(json.dumps(users, indent=2))
            return 0

        if args.command == "delete-user":
            if system.delete_user(args.username):
                print(f"User '{args.username}' deleted successfully.")
                return 0
            print(f"User '{args.username}' was not found.")
            return 1

        if args.command == "change-password":
            result = system.change_password(args.username, args.old_password, args.new_password)
            print(f"Password changed successfully for '{result['username']}'.")
            return 0

        parser.print_help()
        return 1

    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
