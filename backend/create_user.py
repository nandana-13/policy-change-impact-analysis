from getpass import getpass

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def create_user():
    username = input("Enter username: ").strip()
    password = getpass("Enter password: ")
    role = input("Enter role (analyst/admin): ").strip().lower()

    if role not in ["analyst", "admin"]:
        print("Invalid role. Use 'analyst' or 'admin'.")
        return

    db: Session = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existing_user:
            print(f"User '{username}' already exists.")
            return

        hashed_password = password_hash.hash(password)

        user = User(
            username=username,
            password_hash=hashed_password,
            role=role,
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print()
        print("User created successfully.")
        print(f"Username : {user.username}")
        print(f"Role     : {user.role}")
        print(f"Active   : {user.is_active}")

    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_user()