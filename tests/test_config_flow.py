"""Fallback options in the options flow and in YAML."""
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from .conftest import CAR, DOMAIN, FAR, HOME, PHONE, report, setup_composite


async def test_options_flow_fallback_step(hass: HomeAssistant) -> None:
    """The last options step selects fallback inputs and the period."""
    report(hass, PHONE, HOME)
    report(hass, CAR, HOME)
    entry = await setup_composite(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "options"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "entity_id": [PHONE, CAR],
            "require_movement": True,
            "show_unknown_as_0": False,
        },
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "all_states"}
    )
    assert result["step_id"] == "all_states"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["step_id"] == "fallback"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"entity": [CAR], "fallback_after": {"hours": 0, "minutes": 3, "seconds": 0}},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    fallback = {cfg["entity"]: cfg["fallback"] for cfg in entry.options["entity_id"]}
    assert fallback == {PHONE: False, CAR: True}
    assert entry.options["fallback_after"] == {"hours": 0, "minutes": 3, "seconds": 0}

    # The running entity uses the new setting right away.
    await hass.async_block_till_done()
    report(hass, PHONE, HOME)
    await hass.async_block_till_done()
    report(hass, CAR, FAR)
    await hass.async_block_till_done()
    assert hass.states.get("device_tracker.test").attributes["last_entity_id"] == PHONE


async def test_options_flow_fallback_step_suggests_current(
    hass: HomeAssistant,
) -> None:
    """Reopening the options shows the current fallback inputs and period."""
    entry = await setup_composite(
        hass, fallback=[CAR], fallback_after={"hours": 0, "minutes": 7, "seconds": 0}
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "entity_id": [PHONE, CAR],
            "require_movement": True,
            "show_unknown_as_0": False,
        },
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "all_states"}
    )
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})

    suggested = {
        str(key): key.description["suggested_value"]
        for key in result["data_schema"].schema
        if key.description
    }
    assert suggested == {
        "entity": [CAR],
        "fallback_after": {"hours": 0, "minutes": 7, "seconds": 0},
    }


async def test_yaml_import_fallback(hass: HomeAssistant) -> None:
    """YAML takes fallback per input and fallback_after per tracker."""
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "trackers": [
                    {
                        "name": "Test",
                        "entity_id": [PHONE, {"entity": CAR, "fallback": True}],
                        "fallback_after": {"minutes": 2},
                    }
                ]
            }
        },
    )
    await hass.async_block_till_done()

    (entry,) = hass.config_entries.async_entries(DOMAIN)
    fallback = {cfg["entity"]: cfg["fallback"] for cfg in entry.options["entity_id"]}
    assert fallback == {PHONE: False, CAR: True}
    assert entry.options["fallback_after"] == {"hours": 0, "minutes": 2, "seconds": 0}


async def test_yaml_import_fallback_after_default_options(hass: HomeAssistant) -> None:
    """fallback_after in default_options applies to every tracker."""
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "default_options": {"fallback_after": {"minutes": 4}},
                "trackers": [{"name": "Test", "entity_id": [PHONE, CAR]}],
            }
        },
    )
    await hass.async_block_till_done()

    (entry,) = hass.config_entries.async_entries(DOMAIN)
    assert entry.options["fallback_after"] == {"hours": 0, "minutes": 4, "seconds": 0}
