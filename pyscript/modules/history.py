from typing import Literal
from datetime import datetime, timezone, timedelta

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.recorder.statistics import statistics_during_period

async def _get_history(
    start_time: datetime,
    end_time: datetime | None,
    entity_ids: list[str] | None):

    start_time = start_time.astimezone(timezone.utc)
    end_time = end_time.astimezone(timezone.utc)

    return(await get_instance(hass).async_add_executor_job(get_significant_states, hass, start_time, end_time, entity_ids))


async def _get_statistic(
    start_time: datetime,
    end_time: datetime | None,
    statistic_ids: list[str] | None,
    period: Literal["5minute", "day", "hour", "week", "month"],
    types: set[Literal["last_reset", "max", "mean", "min", "state", "sum"]]):

    start_time = start_time.astimezone(timezone.utc)
    end_time = end_time.astimezone(timezone.utc)

    return(await get_instance(hass).async_add_executor_job(statistics_during_period, hass, start_time, end_time, statistic_ids, period, None, types))