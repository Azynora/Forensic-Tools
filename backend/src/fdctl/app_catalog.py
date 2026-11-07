"""Application roadmap used by GUI selection and future adapter integrations."""

from __future__ import annotations


APP_CATALOG: tuple[dict[str, str], ...] = (
    {"id": "discord", "name": "Discord", "name_vi": "Discord", "status": "available"},
    {"id": "telegram", "name": "Telegram Desktop", "name_vi": "Telegram Desktop", "status": "available"},
    {"id": "zalo", "name": "Zalo", "name_vi": "Zalo", "status": "planned"},
    {"id": "whatsapp", "name": "WhatsApp", "name_vi": "WhatsApp", "status": "planned"},
    {"id": "messenger", "name": "Facebook Messenger", "name_vi": "Facebook Messenger", "status": "planned"},
    {"id": "signal", "name": "Signal", "name_vi": "Signal", "status": "planned"},
)


def get_app(app_id: str) -> dict[str, str]:
    return next((item for item in APP_CATALOG if item["id"] == app_id), APP_CATALOG[0])


def app_label(app: dict[str, str], language: str = "en") -> str:
    name = app["name_vi"] if language == "vi" else app["name"]
    if app["status"] == "available":
        return f"{name}  ·  {'Sẵn sàng' if language == 'vi' else 'Ready'}"
    return f"{name}  ·  {'Đang phát triển' if language == 'vi' else 'In development'}"
