# orm_query.py

import asyncio
from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Platform, Order
from google_sheets.sheets_api import (
    add_order_to_sheet, update_order_in_sheet, delete_order_from_sheet,
    add_platform_to_sheet, delete_platform_from_sheet
)

# --- Функции для работы с Платформами ---
async def orm_add_platform(session: AsyncSession, name: str):
    obj = Platform(name=name)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    asyncio.create_task(add_platform_to_sheet(obj))

async def orm_get_platforms(session: AsyncSession):
    query = select(Platform)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_delete_platform(session: AsyncSession, platform_id: int):
    query = delete(Platform).where(Platform.id == platform_id)
    await session.execute(query)
    await session.commit()
    asyncio.create_task(delete_platform_from_sheet(platform_id))

# --- Функции для работы с Заказами ---
async def orm_add_order(session: AsyncSession, data: dict):
    obj = Order(name=data['name'], platform_id=data['platform_id'], link=data.get('link'), payment_status=data['payment_status'], comment=data.get('comment'))
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    asyncio.create_task(add_order_to_sheet(obj))

async def orm_get_order(session: AsyncSession, order_id: int):
    query = select(Order).where(Order.id == order_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()

async def orm_get_orders(session: AsyncSession, limit: int = None, offset: int = None):
    query = select(Order).order_by(Order.id.desc())
    if offset: query = query.offset(offset)
    if limit: query = query.limit(limit)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_count_orders(session: AsyncSession) -> int:
    query = select(func.count(Order.id))
    result = await session.execute(query)
    return result.scalar_one()

async def orm_update_order(session: AsyncSession, order_id: int, data: dict):
    query = update(Order).where(Order.id == order_id).values(**data)
    await session.execute(query)
    await session.commit()
    updated_order = await orm_get_order(session, order_id)
    if updated_order:
        asyncio.create_task(update_order_in_sheet(updated_order))

async def orm_delete_order(session: AsyncSession, order_id: int):
    query = delete(Order).where(Order.id == order_id)
    await session.execute(query)
    await session.commit()
    asyncio.create_task(delete_order_from_sheet(order_id))