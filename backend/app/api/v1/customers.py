"""Customer CRUD routes."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.db.models.customer import Customer
from app.schemas.common import CursorPage, Message
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services import audit

router = APIRouter()


@router.get("", response_model=CursorPage[CustomerRead], summary="List customers")
async def list_customers(
    session: SessionDep,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
) -> CursorPage[CustomerRead]:
    rows = (
        await session.scalars(select(Customer).order_by(Customer.created_at.desc()).limit(limit))
    ).all()
    return CursorPage[CustomerRead](items=[CustomerRead.model_validate(r) for r in rows])


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a customer",
)
async def create_customer(
    payload: CustomerCreate,
    session: SessionDep,
    user: CurrentUser,
) -> CustomerRead:
    customer = Customer(
        tenant_id=user.tenant_id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        notes=payload.notes,
    )
    session.add(customer)
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="customer.created",
        entity_type="customer",
        entity_id=customer.id,
    )
    await session.commit()
    return CustomerRead.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerRead, summary="Fetch a single customer")
async def get_customer(
    customer_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> CustomerRead:
    customer = await session.scalar(select(Customer).where(Customer.id == customer_id))
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "customer not found")
    return CustomerRead.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerRead, summary="Update a customer")
async def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> CustomerRead:
    customer = await session.scalar(select(Customer).where(Customer.id == customer_id))
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "customer not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="customer.updated",
        entity_type="customer",
        entity_id=customer.id,
    )
    await session.commit()
    return CustomerRead.model_validate(customer)


@router.delete("/{customer_id}", response_model=Message, summary="Delete a customer")
async def delete_customer(
    customer_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> Message:
    customer = await session.scalar(select(Customer).where(Customer.id == customer_id))
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "customer not found")
    await session.delete(customer)
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="customer.deleted",
        entity_type="customer",
        entity_id=customer_id,
    )
    await session.commit()
    return Message(detail="deleted")
