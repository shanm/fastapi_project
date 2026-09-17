from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_repository import AuditRepository


async def write_audit_log(
    db: AsyncSession,
    *,
    action: str,
    method: str,
    path: str,
    status_code: int,
    user_id: UUID | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    details: str | None = None,
) -> None:
    await AuditRepository(db).create(
        action=action,
        method=method,
        path=path,
        status_code=status_code,
        user_id=user_id,
        request_id=request_id,
        ip_address=ip_address,
        details=details,
    )
