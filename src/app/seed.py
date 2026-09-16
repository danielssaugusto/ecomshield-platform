"""Seed the database with the default admin user."""

from sqlmodel import Session, select

from src.app.auth import get_password_hash
from src.app.database import engine
from src.app.models import User, UserRole


def seed_admin() -> None:
    """Create the admin user if it does not exist yet."""
    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.username == "admin")
        ).first()

        if existing is not None:
            return

        admin = User(
            username="admin",
            email="admin@ecomshield.dev",
            hashed_password=get_password_hash("senha123"),
            role=UserRole.admin,
            disabled=False,
        )
        session.add(admin)
        session.commit()


if __name__ == "__main__":
    from src.app.database import create_db_and_tables

    create_db_and_tables()
    seed_admin()
    print("✓ Admin user seeded successfully.")
