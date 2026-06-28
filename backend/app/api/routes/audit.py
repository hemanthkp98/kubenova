"""
Audit log API routes.

GET /api/audit           — paginated list of audit events
GET /api/audit/export    — CSV download of matching audit events
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_audit_logger, get_db
from app.config import get_settings
from app.core.audit.logger import AuditLogger
from app.core.audit.models import PaginatedAuditEvents

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=PaginatedAuditEvents)
async def list_audit_events(
    page: int = Query(default=1, ge=1, description="1-based page number."),
    page_size: int = Query(default=0, ge=1, le=500, description="Items per page. 0 = settings default."),
    cluster_context: str | None = Query(default=None, description="Filter by cluster context."),
    from_date: datetime | None = Query(default=None, description="ISO-8601 start datetime filter."),
    to_date: datetime | None = Query(default=None, description="ISO-8601 end datetime filter."),
    risk_level: str | None = Query(default=None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)."),
    db: AsyncSession = Depends(get_db),
    audit: AuditLogger = Depends(get_audit_logger),
) -> PaginatedAuditEvents:
    """
    Return a paginated list of audit events, most recent first.

    Supports filtering by cluster context, date range, and risk level.
    """
    settings = get_settings()
    effective_page_size = page_size or settings.AUDIT_PAGE_SIZE

    return await audit.query(
        session=db,
        page=page,
        page_size=effective_page_size,
        cluster_context=cluster_context,
        from_date=from_date,
        to_date=to_date,
        risk_level=risk_level,
    )


@router.get("/export")
async def export_audit_csv(
    cluster_context: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    audit: AuditLogger = Depends(get_audit_logger),
) -> Response:
    """
    Export audit events as a CSV file download.

    Returns a text/csv response with Content-Disposition: attachment so
    the browser prompts a file save. Applies the same filters as GET /audit.
    """
    csv_content = await audit.export_csv(
        session=db,
        cluster_context=cluster_context,
        from_date=from_date,
        to_date=to_date,
        risk_level=risk_level,
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="kubenova-audit.csv"'
        },
    )
