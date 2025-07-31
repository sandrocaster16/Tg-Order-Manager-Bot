# formatters.py

# ИМПОРТИРУЕМ НУЖНЫЕ МОДУЛИ
from datetime import datetime, timezone, timedelta

# НОВЫЙ КОД: Задаем нашу часовую зону (UTC+3)
LOCAL_TIMEZONE = timezone(timedelta(hours=3))

def format_order_for_display(order):
    # ИЗМЕНЕНО: Конвертируем время перед отображением
    # 1. Говорим Python, что время в БД - это UTC
    utc_time = order.created.replace(tzinfo=timezone.utc)
    # 2. Конвертируем в нашу локальную зону
    local_time = utc_time.astimezone(LOCAL_TIMEZONE)
    # 3. Форматируем уже локальное время
    created_date = local_time.strftime('%d.%m.%Y %H:%M')

    comment_text = f"<i>{order.comment}</i>" if order.comment else "<em>(пусто)</em>"
    link_text = f"<a href='{order.link}'>🔗 Открыть</a>" if order.link else "<em>(нет ссылки)</em>"
    platform_name = order.platform.name if order.platform else "🗑️ Удалена"
    
    return (
        f"<b>🏷️ {order.name}</b>\n"
        f"➖➖➖➖➖\n"
        f"▪️ <b>Дата:</b> {created_date}\n"
        f"▪️ <b>Платформа:</b> {platform_name}\n"
        f"▪️ <b>Ссылка:</b> {link_text}\n"
        f"▪️ <b>Статус:</b> 💳 {order.payment_status}\n"
        f"▪️ <b>Комментарий:</b> {comment_text}"
    )

def format_order_data_for_review(data: dict):
    comment_text = data.get('comment') if data.get('comment') else "<em>(пусто)</em>"
    link_text = data.get('link') if data.get('link') else "<em>(нет ссылки)</em>"
    
    return (
        "<b>👀 Пожалуйста, проверьте данные перед сохранением:</b>\n"
        "➖➖➖➖➖\n"
        f"▪️ <b>Название:</b> {data['name']}\n"
        f"▪️ <b>Платформа:</b> {data['platform_name']}\n"
        f"▪️ <b>Ссылка:</b> {link_text}\n"
        f"▪️ <b>Статус:</b> {data['payment_status']}\n"
        f"▪️ <b>Комментарий:</b> {comment_text}"
    )