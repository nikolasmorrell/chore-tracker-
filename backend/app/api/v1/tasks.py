"""Internal task routes."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.db.models.task import Task
from app.schemas.common import CursorPage
from app.schemas.task import TaskCreate, TaskRead, TaskStatus, TaskUpdate
from app.services import audit

router = APIRouter()


@router.get("", response_model=CursorPage[TaskRead], summary="List tasks")
async def list_tasks(
    session: SessionDep,
    user: CurrentUser,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> CursorPage[TaskRead]:
    stmt = select(Task).order_by(Task.created_at.desc()).limit(limit)
    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)
    rows = (await session.scalars(stmt)).all()
    return CursorPage[TaskRead](items=[TaskRead.model_validate(r) for r in rows])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED, summary="Create a task")
async def create_task(
    payload: TaskCreate,
    session: SessionDep,
    user: CurrentUser,
) -> TaskRead:
    task = Task(
        tenant_id=user.tenant_id,
        title=payload.title,
        description=payload.description,
        due_at=payload.due_at,
        priority=payload.priority,
        assigned_to=payload.assigned_to,
        source="manual",
    )
    session.add(task)
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="task.created",
        entity_type="task",
        entity_id=task.id,
    )
    await session.commit()
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead, summary="Update a task")
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> TaskRead:
    task = await session.scalar(select(Task).where(Task.id == task_id))
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="task.updated",
        entity_type="task",
        entity_id=task.id,
    )
    await session.commit()
    return TaskRead.model_validate(task)


@router.post("/{task_id}/assign", response_model=TaskRead, summary="Assign a task to a teammate")
async def assign_task(
    task_id: UUID,
    assignee_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> TaskRead:
    task = await session.scalar(select(Task).where(Task.id == task_id))
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    task.assigned_to = assignee_id
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="task.assigned",
        entity_type="task",
        entity_id=task.id,
        extra={"assignee_id": str(assignee_id)},
    )
    await session.commit()
    return TaskRead.model_validate(task)
