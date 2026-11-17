"""Per-input state survives a restart."""
from datetime import datetime, timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory

from homeassistant.const import STATE_HOME, STATE_NOT_HOME
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.restore_state import async_get as async_get_restore_state
import homeassistant.util.dt as dt_util
from pytest_homeassistant_custom_component.common import (
    mock_restore_cache,
    mock_restore_cache_with_extra_data,
)

from .conftest import (
    CAR,
    FAR,
    FAR2,
    HOME,
    NEAR,
    PHONE,
    TRACKER,
    report,
    setup_composite,
    tracker,
)


def composite_state(
    state: str, pos: tuple[float, float], last_entity_id: str, last_seen: datetime
) -> State:
    """Return the composite's state as saved before the restart."""
    return State(
        TRACKER,
        state,
        {
            "source_type": "gps",
            "latitude": pos[0],
            "longitude": pos[1],
            "gps_accuracy": 10,
            "entities": [PHONE, CAR],
            "last_entity_id": last_entity_id,
            "last_seen": dt_util.as_local(last_seen).isoformat(),
        },
    )


def saved_input(pos: tuple[float, float], seen: datetime) -> dict[str, Any]:
    """Return one input as saved in the restore data."""
    return {"seen": seen.isoformat(), "lat": pos[0], "lon": pos[1], "acc": 10}


async def restart(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    before: State,
    inputs: dict[str, dict[str, Any]],
    after: list[tuple[str, tuple[float, float]]],
    **options: Any,
) -> None:
    """Restore the composite, then let inputs report in the given order."""
    mock_restore_cache_with_extra_data(hass, [(before, {"inputs": inputs})])
    for entity_id, pos in after:
        freezer.tick(timedelta(seconds=1))
        report(hass, entity_id, pos)
    await setup_composite(hass, **options)
    # Inputs that report again right after the start, in the same order.
    for entity_id, pos in after:
        freezer.tick(timedelta(seconds=1))
        report(hass, entity_id, pos)
        await hass.async_block_till_done()


async def test_restart_vehicle_elsewhere_stays_home(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario E: a car parked outside the home zone must not win the restart."""
    now = dt_util.utcnow()
    await restart(
        hass,
        freezer,
        composite_state(STATE_HOME, HOME, PHONE, now - timedelta(seconds=30)),
        {
            PHONE: saved_input(HOME, now - timedelta(seconds=30)),
            CAR: saved_input(NEAR, now - timedelta(hours=15)),
        },
        [(PHONE, HOME), (CAR, NEAR)],
    )

    state = tracker(hass)
    assert state.state == STATE_HOME
    assert state.attributes["last_entity_id"] == PHONE


async def test_restart_on_foot_vehicle_home_stays_away(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario B: a car parked at home must not pull an absent person home."""
    now = dt_util.utcnow()
    await restart(
        hass,
        freezer,
        composite_state(STATE_NOT_HOME, FAR, PHONE, now - timedelta(seconds=30)),
        {
            PHONE: saved_input(FAR, now - timedelta(seconds=30)),
            CAR: saved_input(HOME, now - timedelta(hours=3)),
        },
        [(PHONE, FAR), (CAR, HOME)],
    )

    state = tracker(hass)
    assert state.state == STATE_NOT_HOME
    assert state.attributes["last_entity_id"] == PHONE


async def test_restart_real_movement_counts(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """An input that moved during the restart counts with its first report."""
    now = dt_util.utcnow()
    await restart(
        hass,
        freezer,
        composite_state(STATE_HOME, HOME, PHONE, now - timedelta(seconds=30)),
        {
            PHONE: saved_input(HOME, now - timedelta(seconds=30)),
            CAR: saved_input(NEAR, now - timedelta(hours=1)),
        },
        [(PHONE, HOME), (CAR, FAR)],
    )

    state = tracker(hass)
    assert state.state == STATE_NOT_HOME
    assert state.attributes["last_entity_id"] == CAR


async def test_restart_fallback_blocked_by_restored_primary(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A phone that reported just before the restart counts as fresh."""
    now = dt_util.utcnow()
    await restart(
        hass,
        freezer,
        composite_state(STATE_HOME, HOME, PHONE, now - timedelta(seconds=60)),
        {
            PHONE: saved_input(HOME, now - timedelta(seconds=60)),
            CAR: saved_input(NEAR, now - timedelta(hours=1)),
        },
        [(CAR, FAR)],
        fallback=[CAR],
    )

    state = tracker(hass)
    assert state.state == STATE_HOME
    assert state.attributes["last_entity_id"] == PHONE


async def test_restore_without_extra_data(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """State saved by a version without input data: start like upstream."""
    now = dt_util.utcnow()
    mock_restore_cache(
        hass, [composite_state(STATE_HOME, HOME, PHONE, now - timedelta(seconds=30))]
    )
    await setup_composite(hass)
    for entity_id, pos in ((PHONE, HOME), (CAR, NEAR)):
        freezer.tick(timedelta(seconds=1))
        report(hass, entity_id, pos)
        await hass.async_block_till_done()

    # Upstream behaviour: with no known position the car's report counts.
    assert tracker(hass).attributes["last_entity_id"] == CAR


async def test_restore_ignores_broken_input_data(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Broken entries are skipped, valid ones still apply."""
    now = dt_util.utcnow()
    await restart(
        hass,
        freezer,
        composite_state(STATE_HOME, HOME, PHONE, now - timedelta(seconds=30)),
        {
            PHONE: {"seen": "not a date", "lat": "x"},
            CAR: saved_input(NEAR, now - timedelta(hours=1)),
        },
        [(PHONE, HOME), (CAR, NEAR)],
    )

    assert tracker(hass).attributes["last_entity_id"] == PHONE


async def test_restore_data_is_saved(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any]
) -> None:
    """The saved data has the shape the restore reads."""
    await setup_composite(hass)
    report(hass, PHONE, HOME)
    freezer.tick(timedelta(seconds=5))
    report(hass, CAR, FAR2)
    await hass.async_block_till_done()

    await async_get_restore_state(hass).async_dump_states()

    saved = {
        item["state"]["entity_id"]: item
        for item in hass_storage["core.restore_state"]["data"]
    }
    inputs = saved[TRACKER]["extra_data"]["inputs"]
    assert set(inputs) == {PHONE, CAR}
    assert inputs[CAR]["lat"] == FAR2[0]
    assert inputs[CAR]["lon"] == FAR2[1]
    assert inputs[CAR]["acc"] == 10
    assert dt_util.parse_datetime(inputs[CAR]["seen"]) is not None
