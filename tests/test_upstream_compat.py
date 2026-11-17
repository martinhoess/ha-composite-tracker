"""Options written by the fork must not break upstream (rollback path).

Runs against this repo and, per .claude/verify.md, against the upstream tag.
"""
from homeassistant.const import STATE_NOT_HOME
from homeassistant.core import HomeAssistant

from .conftest import CAR, FAR, PHONE, report, setup_composite, tracker


async def test_entry_with_fallback_options_loads(hass: HomeAssistant) -> None:
    """An entry carrying fallback keys sets up and tracks."""
    entry = await setup_composite(
        hass, fallback=[CAR], fallback_after={"hours": 0, "minutes": 5, "seconds": 0}
    )
    report(hass, PHONE, FAR)
    await hass.async_block_till_done()

    assert tracker(hass).state == STATE_NOT_HOME

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "options"
