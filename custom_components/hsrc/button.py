from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HsrcConfigEntry, HsrcCoordinator
from .entity import HsrcEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: HsrcConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([AddUnbookedToBasketButton(entry.runtime_data)])


class AddUnbookedToBasketButton(HsrcEntity, ButtonEntity):
    _attr_icon = "mdi:cart-plus"

    def __init__(self, coordinator: HsrcCoordinator) -> None:
        super().__init__(coordinator, "add_unbooked_to_basket")

    async def async_press(self) -> None:
        await self.coordinator.async_add_unbooked_to_basket()
