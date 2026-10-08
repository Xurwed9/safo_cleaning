from pydantic import BaseModel


class StatisticsResponse(BaseModel):
    period: str

    leads: int
    contracts: int

    phone_clicks: int
    whatsapp_clicks: int
    telegram_clicks: int