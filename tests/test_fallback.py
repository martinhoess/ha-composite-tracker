"""Fallback inputs: a fallback only fills in while every primary is silent."""
from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant.const import STATE_HOME, STATE_NOT_HOME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import (
    CAR,
    DOMAIN,
    FAR,
    FAR2,
    HOME,
    NEAR,
    PHONE,
    report,
    setup_composite,
    tracker,
)

# Each step: (seconds after the previous step, input, position).
Step = tuple[int, str, tuple[float, float]]


def phone_still_at_home(minutes: int) -> list[Step]:
    """Return a phone lying at home and reporting every 30 s."""
    return [(30, PHONE, HOME) for _ in range(minutes * 2)]


SCENARIOS: dict[str, tuple[list[Step], str, str]] = {
    # name: (steps, expected state, expected last input)
    "A_all_home": (
        [(0, PHONE, HOME), (1, CAR, HOME), *phone_still_at_home(10)],
        STATE_HOME,
        PHONE,
    ),
    "B_leave_on_foot": (
        [(0, PHONE, HOME), (1, CAR, HOME), (60, PHONE, FAR), (600, CAR, HOME)],
        STATE_NOT_HOME,
        PHONE,
    ),
    "B_return_on_foot": (
        [(0, PHONE, FAR), (1, CAR, HOME), (600, PHONE, HOME)],
        STATE_HOME,
        PHONE,
    ),
    "C_arrive_by_vehicle_phone_silent": (
        [(0, PHONE, FAR), (1, CAR, FAR), (400, CAR, FAR2), (60, CAR, HOME)],
        STATE_HOME,
        CAR,
    ),
    "C_leave_by_vehicle_phone_silent": (
        [(0, PHONE, HOME), (1, CAR, HOME), (400, CAR, FAR)],
        STATE_NOT_HOME,
        CAR,
    ),
    "D_vehicle_parked_elsewhere": (
        # The last car report moves, so only the period can stop it.
        [(0, PHONE, HOME), (15, CAR, NEAR), *phone_still_at_home(10), (5, CAR, FAR)],
        STATE_HOME,
        PHONE,
    ),
    "F_other_driver": (
        [
            (0, PHONE, HOME),
            (1, CAR, HOME),
            (20, PHONE, HOME),
            (10, CAR, FAR),
            (20, PHONE, HOME),
            (10, CAR, FAR2),
        ],
        STATE_HOME,
        PHONE,
    ),
    "G_phone_returns": (
        [(0, PHONE, HOME), (1, CAR, HOME), (600, CAR, FAR), (60, PHONE, FAR2)],
        STATE_NOT_HOME,
        PHONE,
    ),
    "G_phone_returns_unmoved": (
        # Car took over while the phone was silent; the phone reports again from
        # the same spot: it wins, and the car is blocked again afterwards.
        [
            (0, PHONE, HOME),
            (1, CAR, HOME),
            (600, CAR, FAR),
            (60, PHONE, HOME),
            (30, CAR, FAR2),
        ],
        STATE_HOME,
        PHONE,
    ),
    "H_taxi_or_train": (
        [(0, PHONE, HOME), (1, CAR, HOME), (60, PHONE, FAR), (300, PHONE, FAR2)],
        STATE_NOT_HOME,
        PHONE,
    ),
    "I_phone_forgotten": (
        [(0, PHONE, HOME), (1, CAR, HOME), (20, PHONE, HOME), (10, CAR, FAR)],
        STATE_HOME,
        PHONE,
    ),
}


async def run_steps(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, steps: list[Step]
) -> None:
    """Play the steps with frozen time."""
    for seconds, entity_id, pos in steps:
        freezer.tick(timedelta(seconds=seconds))
        report(hass, entity_id, pos)
        await hass.async_block_till_done()


@pytest.mark.parametrize("name", SCENARIOS)
async def test_scenarios(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, name: str
) -> None:
    """Car is a fallback input, phone is the primary."""
    steps, expected_state, expected_input = SCENARIOS[name]
    await setup_composite(hass, fallback=[CAR])

    await run_steps(hass, freezer, steps)

    state = tracker(hass)
    assert state.state == expected_state
    assert state.attributes["last_entity_id"] == expected_input


async def test_no_fallback_is_upstream_behaviour(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Without a fallback flag a parked car beats a phone lying still."""
    await setup_composite(hass)

    await run_steps(hass, freezer, SCENARIOS["D_vehicle_parked_elsewhere"][0])

    state = tracker(hass)
    assert state.state == STATE_NOT_HOME
    assert state.attributes["last_entity_id"] == CAR


async def test_fallback_without_primary_counts(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """With no primary report at all, a fallback counts like any input."""
    await setup_composite(hass, fallback=[CAR])

    await run_steps(hass, freezer, [(0, CAR, HOME), (60, CAR, FAR)])

    state = tracker(hass)
    assert state.state == STATE_NOT_HOME
    assert state.attributes["last_entity_id"] == CAR


@pytest.mark.parametrize(
    ("silent_seconds", "car_counts"), [(119, False), (120, True), (121, True)]
)
async def test_fallback_after_boundary(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    silent_seconds: int,
    car_counts: bool,
) -> None:
    """The period is configurable; at exactly the period the fallback counts."""
    await setup_composite(hass, fallback=[CAR], fallback_after={"minutes": 2})

    await run_steps(hass, freezer, [(0, PHONE, HOME), (silent_seconds, CAR, FAR)])

    assert tracker(hass).attributes["last_entity_id"] == (CAR if car_counts else PHONE)


async def test_fallback_after_default_is_five_minutes(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Entries without fallback_after use 5 minutes."""
    await setup_composite(hass, fallback=[CAR])

    await run_steps(hass, freezer, [(0, PHONE, HOME), (299, CAR, FAR)])
    assert tracker(hass).attributes["last_entity_id"] == PHONE

    await run_steps(hass, freezer, [(2, CAR, FAR2)])
    assert tracker(hass).attributes["last_entity_id"] == CAR


async def test_non_gps_primary_ignored_report_does_not_block(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A router reporting not_home (ignored by the composite) does not block."""
    router = "binary_sensor.router"
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test",
        data={},
        options={
            "entity_id": [
                {"entity": e, "all_states": False, "use_picture": False, "fallback": f}
                for e, f in ((PHONE, False), (router, False), (CAR, True))
            ],
            "require_movement": True,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await run_steps(hass, freezer, [(0, PHONE, HOME), (1, CAR, HOME)])

    freezer.tick(timedelta(seconds=400))
    hass.states.async_set(router, "off")
    await hass.async_block_till_done()
    await run_steps(hass, freezer, [(10, CAR, FAR)])

    assert tracker(hass).attributes["last_entity_id"] == CAR


async def test_no_speed_across_fallback_switch(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Handing over between car and phone yields no speed (and no driving)."""
    entry = await setup_composite(hass, fallback=[CAR])
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "driving_speed": 10}
    )
    await hass.async_block_till_done()

    await run_steps(
        hass,
        freezer,
        [(0, PHONE, FAR), (1, CAR, FAR), (600, CAR, FAR2), (60, PHONE, FAR)],
    )

    state = tracker(hass)
    assert state.attributes["last_entity_id"] == PHONE
    assert state.state == STATE_NOT_HOME
    assert hass.states.get("sensor.test_speed").state in ("unknown", "0.0")
