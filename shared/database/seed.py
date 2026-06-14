"""
F:\3ml project\backend\app\core\seed.py

Database seeder – creates the initial admin account if it does not
already exist.  Call once at application startup after init_db().
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default admin credentials
# (Override via environment variables in production – never commit secrets)
# ---------------------------------------------------------------------------

_ADMIN_USERNAME = "admin"
_ADMIN_EMAIL = "admin@codealpha.ai"
_ADMIN_PASSWORD = "admin123"  # noqa: S105


async def seed_admin(db: AsyncSession) -> None:
    """Ensure an admin user exists in the database.

    If a user with ``username == 'admin'`` already exists the function
    returns without making any changes, making it safe to call on every
    application startup.

    Parameters
    ----------
    db:
        An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """
    result = await db.execute(
        select(User).where(User.username == _ADMIN_USERNAME)
    )
    existing_admin: User | None = result.scalar_one_or_none()

    if existing_admin is not None:
        logger.info("Admin user already exists – skipping seed.")
        return

    admin_user = User(
        username=_ADMIN_USERNAME,
        email=_ADMIN_EMAIL,
        hashed_password=get_password_hash(_ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    logger.info(
        "Seeded admin user: id=%d username=%r email=%r",
        admin_user.id,
        admin_user.username,
        admin_user.email,
    )
