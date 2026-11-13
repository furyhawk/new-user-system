# New User System

This project is a lightweight, file-based user management system written in Python. It stores users in a JSON file and supports creation, login, listing, deletion, and password changes.

## Features

- User registration with validation
- Password hashing using PBKDF2-HMAC-SHA256
- Login authentication
- Admin flag support
- User listing and deletion
- Password change workflow
- JSON-backed persistence

## Quick start

```bash
cd /root/new-user-system
python3 user_system.py register alice StrongPass123 --email alice@example.com
python3 user_system.py login alice StrongPass123
python3 user_system.py list-users
```

## Commands

### Register a user

```bash
python3 user_system.py register <username> <password> --email <email> --admin
```

### Log in

```bash
python3 user_system.py login <username> <password>
```

### List all users

```bash
python3 user_system.py list-users
```

### Delete a user

```bash
python3 user_system.py delete-user <username>
```

### Change a password

```bash
python3 user_system.py change-password <username> <old_password> <new_password>
```

## Data storage

Users are stored in the file:

```text
/root/new-user-system/data/users.json
```

## Notes

- Passwords are never stored in plain text.
- The default data file is created automatically when the app runs.
- You can override the storage file using the `--data-file` option.
