import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

import asyncio

from app.services.telegram import send_telegram_message


async def main():
    await send_telegram_message(
        "🧪 Safo Cleaning Telegram test"
    )

    print("Telegram message sent successfully")


if __name__ == "__main__":
    asyncio.run(main())




# import sys
# from pathlib import Path

# sys.path.append(
#     str(Path(__file__).resolve().parents[1])
# )

# import asyncio
# import httpx

# from app.core.config import settings


# async def main():
#     url = (
#         f"https://api.telegram.org/"
#         f"bot{settings.telegram_bot_token}/getUpdates"
#     )

#     async with httpx.AsyncClient(timeout=10) as client:
#         response = await client.get(url)
#         response.raise_for_status()

#         data = response.json()

#     if not data.get("ok"):
#         print(data)
#         return

#     updates = data.get("result", [])

#     if not updates:
#         print("No updates found.")
#         return

#     for update in updates:
#         message = update.get("message")

#         if not message:
#             continue

#         chat = message.get("chat", {})

#         print(f"Chat ID: {chat.get('id')}")
#         print(f"Chat title: {chat.get('title')}")
#         print(f"Chat type: {chat.get('type')}")
#         print("-" * 30)


# if __name__ == "__main__":
#     asyncio.run(main())