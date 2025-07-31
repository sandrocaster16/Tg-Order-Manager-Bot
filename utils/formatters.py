from datetime import datetime, timezone, timedelta

# UTC+3
LOCAL_TIMEZONE = timezone(timedelta(hours=3))

def format_order_for_display(order):
    utc_time = order.created.replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone(LOCAL_TIMEZONE)
    created_date = local_time.strftime('%d.%m.%Y %H:%M')

    comment_text = f"<i>{order.comment}</i>" if order.comment else "<em>(пусто)</em>"
    link_text = f"<a href='{order.link}'>Открыть</a>" if order.link else "<em>(нет ссылки)</em>"
    platform_name = order.platform.name if order.platform else "🗑️ Удалена"
    
    return (
        f"<b>🏷️ {order.name}</b>\n"
        f"➖➖➖➖➖\n"
        f"▪️ <b>Дата:</b> {created_date}\n"
        f"▪️ <b>Платформа:</b> {platform_name}\n"
        f"▪️ <b>Ссылка:</b> {link_text}\n"
        f"▪️ <b>Статус:</b> {order.payment_status}\n"
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