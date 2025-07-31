import os
import logging
import asyncio
from typing import List
from dotenv import load_dotenv

import gspread
from google.oauth2.service_account import Credentials
from datetime import timezone, timedelta
from database.models import Order, Platform

load_dotenv()

SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY")
ORDERS_SHEET_NAME = "Заказы"
PLATFORMS_SHEET_NAME = "Платформы"
ORDERS_HEADERS = ["ID Заказа", "Название", "Платформа", "Ссылка", "Статус оплаты", "Комментарий", "Дата создания"]
PLATFORMS_HEADERS = ["ID Платформы", "Название", "Дата создания"]

LOCAL_TIMEZONE = timezone(timedelta(hours=3))

def _get_worksheet_sync(sheet_name: str):
    try:
        creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        gc = gspread.service_account(filename=creds_path)
        spreadsheet = gc.open_by_key(SHEET_KEY)
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet
    except FileNotFoundError:
        logging.error(f"Не найден файл с ключами: {creds_path}. Убедитесь, что путь в .env указан верно.")
        raise
    except Exception as e:
        logging.error(f"Ошибка при подключении к Google API или получении листа '{sheet_name}': {e}", exc_info=True)
        raise

def _format_order(order: Order) -> list:
    utc_time = order.created.replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone(LOCAL_TIMEZONE)
    
    return [
        order.id, order.name,
        order.platform.name if order.platform else "🗑️ Удалена",
        order.link or "", order.payment_status,
        order.comment or "",
        local_time.strftime('%d.%m.%Y %H:%M:%S'),
    ]

def _format_platform(platform: Platform) -> list:
    utc_time = platform.created.replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone(LOCAL_TIMEZONE)
    
    return [platform.id, platform.name, local_time.strftime('%d.%m.%Y %H:%M:%S')]

def sync_orders_sync(orders: List[Order]):
    logging.info(f"SYNC: Starting full synchronization of {len(orders)} ORDERS...")
    worksheet = _get_worksheet_sync(ORDERS_SHEET_NAME)
    worksheet.clear()
    worksheet.append_row(ORDERS_HEADERS)
    rows_to_add = [_format_order(order) for order in orders]
    if rows_to_add:
        worksheet.append_rows(rows_to_add, value_input_option='USER_ENTERED')
    logging.info(f"SYNC: Successfully synchronized {len(orders)} orders.")

def add_order_sync(order: Order):
    logging.info(f"SYNC: Adding order #{order.id} to sheet.")
    worksheet = _get_worksheet_sync(ORDERS_SHEET_NAME)
    worksheet.append_row(_format_order(order), value_input_option='USER_ENTERED')

def update_order_sync(order: Order):
    logging.info(f"SYNC: Updating order #{order.id} in sheet.")
    worksheet = _get_worksheet_sync(ORDERS_SHEET_NAME)
    cell = worksheet.find(str(order.id), in_column=1)
    if not cell:
        logging.warning(f"SYNC: Order #{order.id} not found for update, adding instead.")
        add_order_sync(order)
        return
    row_values = _format_order(order)
    worksheet.update(f'A{cell.row}:{chr(ord("A")+len(row_values)-1)}{cell.row}', [row_values])

def delete_order_sync(order_id: int):
    logging.info(f"SYNC: Deleting order #{order_id} from sheet.")
    worksheet = _get_worksheet_sync(ORDERS_SHEET_NAME)
    cell = worksheet.find(str(order_id), in_column=1)
    if cell:
        worksheet.delete_rows(cell.row)

def sync_platforms_sync(platforms: List[Platform]):
    logging.info(f"SYNC: Starting full synchronization of {len(platforms)} PLATFORMS...")
    worksheet = _get_worksheet_sync(PLATFORMS_SHEET_NAME)
    worksheet.clear()
    worksheet.append_row(PLATFORMS_HEADERS)
    rows_to_add = [_format_platform(p) for p in platforms]
    if rows_to_add:
        worksheet.append_rows(rows_to_add, value_input_option='USER_ENTERED')
    logging.info(f"SYNC: Successfully synchronized {len(platforms)} platforms.")

def add_platform_sync(platform: Platform):
    logging.info(f"SYNC: Adding platform '{platform.name}' to sheet.")
    worksheet = _get_worksheet_sync(PLATFORMS_SHEET_NAME)
    worksheet.append_row(_format_platform(platform), value_input_option='USER_ENTERED')

def delete_platform_sync(platform_id: int):
    logging.info(f"SYNC: Deleting platform #{platform_id} from sheet.")
    worksheet = _get_worksheet_sync(PLATFORMS_SHEET_NAME)
    cell = worksheet.find(str(platform_id), in_column=1)
    if cell:
        worksheet.delete_rows(cell.row)

async def sync_orders_to_sheet(orders: List[Order]):
    await asyncio.to_thread(sync_orders_sync, orders)

async def add_order_to_sheet(order: Order):
    await asyncio.to_thread(add_order_sync, order)

async def update_order_in_sheet(order: Order):
    await asyncio.to_thread(update_order_sync, order)

async def delete_order_from_sheet(order_id: int):
    await asyncio.to_thread(delete_order_sync, order_id)

async def sync_platforms_to_sheet(platforms: List[Platform]):
    await asyncio.to_thread(sync_platforms_sync, platforms)

async def add_platform_to_sheet(platform: Platform):
    await asyncio.to_thread(add_platform_sync, platform)

async def delete_platform_from_sheet(platform_id: int):
    await asyncio.to_thread(delete_platform_sync, platform_id)