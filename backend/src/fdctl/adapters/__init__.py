from fdctl.adapters.discord import DiscordAdapter
from fdctl.adapters.telegram import TelegramAdapter
from fdctl.adapters.zalo import ZaloAdapter

def get_adapters() -> dict[str, object]:
    adapters = [DiscordAdapter(), TelegramAdapter(), ZaloAdapter()]
    return {adapter.app_id: adapter for adapter in adapters}

