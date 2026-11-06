from fdctl.adapters.discord import DiscordAdapter
from fdctl.adapters.zalo import ZaloAdapter

def get_adapters() -> dict[str, object]:
    adapters = [DiscordAdapter(), ZaloAdapter()]
    return {adapter.app_id: adapter for adapter in adapters}

