import logging
from typing import Optional
from core.settings.general import GeneralSettings
from core.settings.analytics import AnalyticsSettings
from core.settings.stage_model import StageModelSettings
from core.settings.live2d import Live2dSettings
from core.settings.theme import ThemeSettings
from core.settings.controls_island import ControlsIslandSettings
from core.settings.discord import DiscordSettings
from core.settings.twitter import TwitterSettings
from core.display_models import DisplayModelsStore
from core.configurator import Configurator

logger = logging.getLogger("airi_settings_index")

class UnifiedSettings:
    def __init__(self, display_models_store: DisplayModelsStore, configurator: Configurator):
        self.general = GeneralSettings()
        self.analytics = AnalyticsSettings()
        self.stage_model = StageModelSettings(display_models_store)
        self.live2d = Live2dSettings()
        self.theme = ThemeSettings()
        self.controls_island = ControlsIslandSettings()
        self.discord = DiscordSettings(configurator)
        self.twitter = TwitterSettings(configurator)

    async def reset_state(self):
        await self.stage_model.reset_state()
        self.analytics.reset_state()
        self.general.reset_state()
        self.live2d.reset_state()
        self.theme.reset_state()
        self.controls_island.reset_state()
        self.discord.reset_state()
        self.twitter.reset_state()
        logger.info("Unified settings reset")

    # Accessors for direct use (as Pinia stores do)
    @property
    def disable_transitions(self) -> bool:
        return self.general.disable_transitions

    @property
    def language(self) -> str:
        return self.general.language

    @property
    def analytics_enabled(self) -> bool:
        return self.analytics.analytics_enabled

    @property
    def stage_model_renderer(self) -> Optional[str]:
        return self.stage_model.stage_model_renderer
