import httpx
from decimal import Decimal


from app.core.config import settings



TELEGRAM_API_URL = (
    "https://api.telegram.org/"
    f"bot{settings.telegram_bot_token}"
)


async def send_telegram_message(
    text: str,
    reply_markup: dict | None = None,
) -> None:

    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json=payload,
        )

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {data}"
        )





def build_lead_message(
    *,
    object_type: str,
    area: Decimal,
    cleaning_frequency: str,
    name: str,
    phone: str,
    language: str,
    calculated_price: Decimal,
    comment: str | None,
    extra_services: list[str],
) -> str:

    services_text = (
        ", ".join(extra_services)
        if extra_services
        else "Нет"
    )

    comment_text = comment or "Нет"

    return (
        "🆕 <b>Новый лид</b>\n\n"
        f"🏢 Тип объекта: <b>{object_type}</b>\n"
        f"📐 Площадь: <b>{area} м²</b>\n"
        f"🧹 Частота: <b>{cleaning_frequency}</b>\n"
        f"➕ Доп. услуги: <b>{services_text}</b>\n\n"
        f"👤 Имя: <b>{name}</b>\n"
        f"📞 Телефон: <b>{phone}</b>\n"
        f"🌐 Язык: <b>{language}</b>\n"
        f"💰 Расчётная цена: <b>{calculated_price}</b>\n\n"
        f"💬 Комментарий: <b>{comment_text}</b>"
    )



def build_whatsapp_button(phone: str) -> dict:
    clean_phone = (
        phone
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    return {
        "inline_keyboard": [
            [
                {
                    "text": "💬 Написать клиенту в WhatsApp",
                    "url": f"https://wa.me/{clean_phone}",
                }
            ]
        ]
    }