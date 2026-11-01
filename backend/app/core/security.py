from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import Depends, Header, HTTPException, status


class Role(str, Enum):
    public = "public"
    reporter = "reporter"
    reviewer = "reviewer"
    authority_admin = "authority_admin"
    platform_admin = "platform_admin"


# Role hierarchy — higher roles inherit lower role permissions
ROLE_HIERARCHY: dict[Role, set[Role]] = {
    Role.public: {Role.public},
    Role.reporter: {Role.public, Role.reporter},
    Role.reviewer: {Role.public, Role.reporter, Role.reviewer},
    Role.authority_admin: {Role.public, Role.reporter, Role.reviewer, Role.authority_admin},
    Role.platform_admin: {
        Role.public,
        Role.reporter,
        Role.reviewer,
        Role.authority_admin,
        Role.platform_admin,
    },
}


class CurrentUser:
    """Simple mock-auth user context for MVP."""

    def __init__(
        self,
        user_id: str | None = None,
        role: Role = Role.public,
        email: str | None = None,
        organisation_id: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.role = role
        self.email = email
        self.organisation_id = organisation_id

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    @property
    def is_staff(self) -> bool:
        return self.role in (Role.reviewer, Role.authority_admin, Role.platform_admin)

    @property
    def is_admin(self) -> bool:
        return self.role in (Role.authority_admin, Role.platform_admin)

    @property
    def is_platform_admin(self) -> bool:
        return self.role == Role.platform_admin

    def has_role(self, required_role: Role) -> bool:
        return required_role in ROLE_HIERARCHY.get(self.role, set())


def _parse_role_from_header(
    x_user_role: str | None,
    x_user_id: str | None,
    x_user_email: str | None,
    x_user_org: str | None,
) -> CurrentUser:
    """Parse mock auth from headers. In production this would validate Cognito tokens."""
    role = Role.public
    if x_user_role:
        try:
            role = Role(x_user_role.lower())
        except ValueError:
            role = Role.public

    return CurrentUser(
        user_id=x_user_id,
        role=role,
        email=x_user_email,
        organisation_id=x_user_org,
    )


async def get_current_user(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    x_user_org: str | None = Header(default=None, alias="X-User-Organisation"),
) -> CurrentUser:
    """Dependency that returns the current user from mock header-based auth."""
    return _parse_role_from_header(x_user_role, x_user_id, x_user_email, x_user_org)


def require_role(*allowed_roles: Role):
    """Dependency factory that enforces the user has one of the allowed roles (or higher)."""

    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        for required in allowed_roles:
            if user.has_role(required):
                return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "message": f"Requires one of: {', '.join(r.value for r in allowed_roles)}",
            },
        )

    return _check


# Convenience dependencies
require_reporter = require_role(Role.reporter)
require_reviewer = require_role(Role.reviewer)
require_admin = require_role(Role.authority_admin)
require_platform_admin = require_role(Role.platform_admin)
