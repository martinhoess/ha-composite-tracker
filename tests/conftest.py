"""Fixtures and helpers for Composite tests."""
from collections.abc import Iterable
from typing import Any

import pytest

from homeassistant.core import HomeAssistant, State
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Import early so this repo's custom_components wins over the test plugin's copy.
import custom_components.composite  # noqa: F401

DOMAIN = "composite"
TRACKER = "device_tracker.test"
PHONE = "device_tracker.phone"
CAR = "device_tracker.car"

# Test home is hass.config (32.87336, -117.22743), zone radius 100 m.
HOME = (32.87336, -117.22743)
NEAR = (32.87670, -117.22743)  # about 370 m north, outside the home zone
FAR = (32.92336, -117.22743)  # about 5.5 km north
FAR2 = (32.97336, -117.22743)  # about 11 km north


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom_components/composite in every test."""


@pytest.fixture(autouse=True)
async def setup_zone(
    hass: HomeAssistant, auto_enable_custom_integrations: None
) -> None:
    """Create zone.home, which decides home/not_home.

    Depends on the custom integration fixture: loading any integration first
    would cache the integration list without custom_components.
    """
    assert await async_setup_component(hass, "zone", {})


def gps_attrs(pos: tuple[float, float], acc: float = 10) -> dict[str, Any]:
    """Return attributes of a GPS tracker without last_seen (like Traccar)."""
    return {
        "latitude": pos[0],
        "longitude": pos[1],
        "gps_accuracy": acc,
        "source_type": "gps",
    }


def report(hass: HomeAssistant, entity_id: str, pos: tuple[float, float]) -> None:
    """Let a GPS input report a position; a repeat still fires an event."""
    hass.states.async_set(entity_id, "not_home", gps_attrs(pos), force_update=True)


def entry_options(
    *,
    fallback: Iterable[str] = (),
    require_movement: bool = True,
    fallback_after: dict[str, int] | None = None,
    inputs: Iterable[str] = (PHONE, CAR),
) -> dict[str, Any]:
    """Return options of a composite with phone and car as inputs."""
    options: dict[str, Any] = {
        "entity_id": [
            {
                "entity": entity_id,
                "all_states": False,
                "use_picture": False,
                "fallback": entity_id in fallback,
            }
            for entity_id in inputs
        ],
        "require_movement": require_movement,
    }
    if fallback_after is not None:
        options["fallback_after"] = fallback_after
    return options


async def setup_composite(hass: HomeAssistant, **kwargs: Any) -> MockConfigEntry:
    """Set up a composite named "test" and return its config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, title="test", data={}, options=entry_options(**kwargs)
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def tracker(hass: HomeAssistant) -> State:
    """Return the composite's state."""
    state = hass.states.get(TRACKER)
    assert state is not None
    return state
