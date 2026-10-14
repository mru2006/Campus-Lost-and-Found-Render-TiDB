"""Create an administrator using DB_* environment variables.
Run: python create_admin.py
The script prompts for credentials; the password is not echoed.
"""
import getpass
import os
import mysql.connector
from werkzeug.security import generate_password_hash
from db import get_db_connection


def main():
    name = input("Admin display name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password (min 12 characters recommended): ")
    if not name or not email or len(password) < 8:
        raise SystemExit("Name/email are required; password must be at least 8 characters.")

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT user_id FROM `USER` WHERE email = %s", (email,))
        existing = cursor.fetchone()
        if existing:
            user_id = existing[0]
            cursor.execute("UPDATE `USER` SET name=%s, password=%s WHERE user_id=%s",
                           (name, generate_password_hash(password), user_id))
        else:
            cursor.execute("INSERT INTO `USER` (name, email, password) VALUES (%s, %s, %s)",
                           (name, email, generate_password_hash(password)))
            user_id = cursor.lastrowid
        cursor.execute("SELECT admin_id FROM ADMIN WHERE user_id=%s", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO ADMIN (user_id) VALUES (%s)", (user_id,))
        connection.commit()
        print(f"Admin account is ready for {email}. Keep the password private.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
