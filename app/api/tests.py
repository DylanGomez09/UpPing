import csv
import io
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.ping_test import PingTest
from app.models.user import User
from app.schemas.test import PingTestCreate, PingTestList, PingTestOut

router = APIRouter(prefix="/tests", tags=["tests"])

CSV_HEADERS = [
    "id",
    "target_ip",
    "avg_latency_ms",
    "packets_sent",
    "packets_received",
    "loss_percent",
    "ran_at",
    "created_at",
]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PingTestOut,
)
async def create_test(
    payload: PingTestCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PingTest:
    test = PingTest(
        user_id=user.id,
        target_ip=str(payload.target_ip),
        avg_latency_ms=payload.avg_latency_ms,
        packets_sent=payload.packets_sent,
        packets_received=payload.packets_received,
        loss_percent=payload.loss_percent,
        ran_at=payload.ran_at,
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)
    return test


@router.get("", response_model=PingTestList)
async def list_tests(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    target_ip: str | None = Query(default=None),
) -> PingTestList:
    stmt = select(PingTest).where(PingTest.user_id == user.id)
    if target_ip:
        stmt = stmt.where(PingTest.target_ip == target_ip)

    total = await db.scalar(
        select(func.count()).select_from(stmt.subquery())
    )
    rows = (
        await db.scalars(
            stmt.order_by(PingTest.ran_at.desc()).limit(limit).offset(offset)
        )
    ).all()
    return PingTestList(
        items=rows, total=total or 0, limit=limit, offset=offset
    )


@router.get("/export")
async def export_csv(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    rows = (
        await db.scalars(
            select(PingTest)
            .where(PingTest.user_id == user.id)
            .order_by(PingTest.ran_at)
        )
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)
    for row in rows:
        writer.writerow(
            [
                row.id,
                row.target_ip,
                row.avg_latency_ms,
                row.packets_sent,
                row.packets_received,
                row.loss_percent,
                row.ran_at.isoformat(),
                row.created_at.isoformat(),
            ]
        )
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ping_tests.csv"'},
    )


async def _get_owned_test(
    db: AsyncSession, user: User, test_id: UUID
) -> PingTest:
    test = await db.scalar(
        select(PingTest).where(
            PingTest.id == test_id, PingTest.user_id == user.id
        )
    )
    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado",
        )
    return test


@router.get("/{test_id}", response_model=PingTestOut)
async def get_test(
    test_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PingTest:
    return await _get_owned_test(db, user, test_id)


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test(
    test_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    test = await _get_owned_test(db, user, test_id)
    await db.delete(test)
    await db.commit()
