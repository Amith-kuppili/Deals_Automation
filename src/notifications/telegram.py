import httpx

from src.config.settings import settings


class TelegramNotifier:
    """Small async Telegram Bot API client used by the worker."""

    def __init__(self) -> None:
        self.token = settings.TELEGRAM_BOT_TOKEN.strip()
        self.chat_id = settings.TELEGRAM_CHAT_ID.strip()

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    async def send_message(self, text: str) -> str | None:
        if not self.enabled:
            return None

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json={"chat_id": self.chat_id, "text": text})
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                raise RuntimeError(payload.get("description", "Telegram rejected the message"))
            return str(payload.get("result", {}).get("message_id"))
