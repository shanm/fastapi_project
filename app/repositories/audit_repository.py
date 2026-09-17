from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        action: str,
        method: str,
        path: str,
        status_code: int,
        user_id: UUID | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        details: str | None = None,
    ) -> AuditLog:
        audit = AuditLog(
            action=action,
            method=method,
            path=path,
            status_code=status_code,
            user_id=user_id,
            request_id=request_id,
            ip_address=ip_address,
            details=details,
        )
        self.db.add(audit)
        await self.db.commit()
        return audit
