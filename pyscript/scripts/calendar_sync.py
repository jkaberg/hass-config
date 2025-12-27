# File: pyscript/sync_calendars_ms365.py
from datetime import datetime, timedelta, timezone, date
import asyncio
import re
from typing import Any, Tuple, Optional
from homeassistant.util import dt as hadt  # HA timezone utilities

# JOB MAPPINGS: add as many as you need
JOBS = [
    {
        "name": "private_to_ms365",
        "source_entity": "calendar.private_joel",
        "target_entity": "calendar.ms365_calendar",
        "window_days": 60,
    },
    # {
    #     "name": "source2_to_target2",
    #     "source_entity": "calendar.source2",
    #     "target_entity": "calendar.ms365_calendar_2",
    #     "window_days": 60,
    # },
]

# Helpers

def _now_local() -> datetime:
    return hadt.now()

async def _get_events(entity_id: str, start_dt: datetime, end_dt: datetime) -> list[dict]:
    data = {
        "entity_id": entity_id,
        "start_date_time": start_dt,
        "end_date_time": end_dt,
    }
    result = await hass.services.async_call(
        "calendar",
        "get_events",
        data,
        blocking=True,
        return_response=True,
    )
    if isinstance(result, dict) and "events" in result:
        return result["events"] or []
    return result or []

def _source_key(ev: dict[str, Any]) -> Tuple[str, str]:
    return (str(ev.get("uid") or ""), str(ev.get("recurrence_id") or ""))

def _is_iso_date_string(v: Any) -> bool:
    return isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-"

def _parse_event_times(ev: dict[str, Any]) -> Tuple[bool, Any, Any]:
    # Returns (is_all_day, start_value, end_value)
    start_v = ev.get("start")
    end_v   = ev.get("end")

    if _is_iso_date_string(start_v) and _is_iso_date_string(end_v):
        return (True, date.fromisoformat(start_v), date.fromisoformat(end_v))

    def to_dt(val: Any) -> Any:
        if isinstance(val, datetime):
            return val if val.tzinfo else hadt.as_local(val.replace(tzinfo=timezone.utc))
        if isinstance(val, str):
            try:
                dtp = datetime.fromisoformat(val)
                if dtp.tzinfo:
                    return hadt.as_local(dtp)
                return hadt.as_local(dtp.replace(tzinfo=timezone.utc))
            except Exception:
                return val
        return val

    return (False, to_dt(start_v), to_dt(end_v))

def _to_service_value(v: Any) -> Any:
    # Convert date/datetime to ISO strings for service payloads
    if isinstance(v, date) and not isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, datetime):
        return v.isoformat()
    return v

def _marker_prefix_for(source_entity: str) -> str:
    return f"SYNC:{source_entity}:"

def _build_marker_for_source(source_entity: str, ev: dict[str, Any]) -> str:
    uid, rid = _source_key(ev)
    return f"{_marker_prefix_for(source_entity)}uid={uid}" + (f";rid={rid}" if rid else "")

def _parse_marker(source_entity: str, desc: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not desc:
        return (None, None)
    prefix = _marker_prefix_for(source_entity)
    if not desc.startswith(prefix):
        return (None, None)
    # Expect "SYNC:<source>:uid=<UID>[;rid=<RID>]" on first line
    first = desc.splitlines()[0]
    m = re.search(r"uid=([^\s;]+)", first, re.IGNORECASE)
    if not m:
        return (None, None)
    uid = m.group(1)
    m2 = re.search(r"rid=([^\s;]+)", first, re.IGNORECASE)
    rid = m2.group(1) if m2 else ""
    return (uid, rid)

def _strip_marker_from_description(source_entity: str, desc: str) -> str:
    if not desc:
        return ""
    lines = desc.splitlines()
    if lines and lines[0].startswith(_marker_prefix_for(source_entity)):
        return "\n".join(lines[1:]).strip()
    return desc.strip()

def _events_equivalent(source_entity: str, source_ev: dict[str, Any], target_ev: dict[str, Any]) -> bool:
    src_title = source_ev.get("summary") or ""
    tgt_title = target_ev.get("summary") or ""

    src_is_all_day, src_start, src_end = _parse_event_times(source_ev)
    tgt_is_all_day, tgt_start, tgt_end = _parse_event_times(target_ev)

    src_desc = (source_ev.get("description") or "").strip()
    tgt_desc = _strip_marker_from_description(source_entity, target_ev.get("description") or "")

    if src_title != tgt_title:
        return False
    if src_is_all_day != tgt_is_all_day:
        return False

    if isinstance(src_start, (datetime, date)) and isinstance(tgt_start, (datetime, date)):
        if src_start != tgt_start:
            return False
    else:
        if str(src_start) != str(tgt_start):
            return False

    if isinstance(src_end, (datetime, date)) and isinstance(tgt_end, (datetime, date)):
        if src_end != tgt_end:
            return False
    else:
        if str(src_end) != str(tgt_end):
            return False

    if src_desc != tgt_desc:
        return False

    return True

def _build_target_description(source_entity: str, source_ev: dict[str, Any]) -> str:
    meta = _build_marker_for_source(source_entity, source_ev)
    body = source_ev.get("description") or ""
    return f"{meta}\n{body}".strip()

async def _create_target_event(source_entity: str, target_entity: str, source_ev: dict[str, Any]):
    title = source_ev.get("summary") or "Busy"
    is_all_day, start_v, end_v = _parse_event_times(source_ev)
    description = _build_target_description(source_entity, source_ev)

    payload = {
        "entity_id": target_entity,
        "subject": title,
        "description": description,
        "sensitivity": "private",
        "show_as": "oof",
        "start": _to_service_value(start_v),
        "end": _to_service_value(end_v),
    }
    if is_all_day:
        payload["all_day"] = True

    await hass.services.async_call("ms365_calendar", "create_event", payload, blocking=True)

async def _update_target_event_ms365(target_entity: str, target_uid: str, target_rid: Optional[str], source_entity: str, source_ev: dict[str, Any]):
    title = source_ev.get("summary") or "Busy"
    is_all_day, start_v, end_v = _parse_event_times(source_ev)
    description = _build_target_description(source_entity, source_ev)

    payload: dict[str, Any] = {
        "entity_id": target_entity,
        "uid": target_uid,
        "subject": title,
        "description": description,
        "sensitivity": "private",
        "show_as": "oof",
        "start": _to_service_value(start_v),
        "end": _to_service_value(end_v),
    }
    if target_rid:
        payload["recurrence_id"] = target_rid
    if is_all_day:
        payload["all_day"] = True

    await hass.services.async_call("ms365_calendar", "update_event", payload, blocking=True)

async def _delete_target_event(target_entity: str, target_uid: str, target_rid: Optional[str]):
    data: dict[str, Any] = {"entity_id": target_entity, "uid": target_uid}
    if target_rid:
        data["recurrence_id"] = target_rid
    await hass.services.async_call("calendar", "delete_event", data, blocking=True)

async def _run_sync_job(job: dict):
    source_entity = job["source_entity"]
    target_entity = job["target_entity"]
    window_days   = int(job.get("window_days", 60))

    start_dt = _now_local()
    end_dt   = start_dt + timedelta(days=window_days)

    source_events = await _get_events(source_entity, start_dt, end_dt)
    target_events = await _get_events(target_entity, start_dt, end_dt)

    # Index source by (uid, rid)
    source_by_key: dict[Tuple[str, str], dict] = {}
    for ev in source_events:
        uid, rid = _source_key(ev)
        if uid:
            source_by_key[(uid, rid)] = ev

    # Index target by our marker (source uid,rid)
    target_by_source_key: dict[Tuple[str, str], dict] = {}
    for tev in target_events:
        src_uid, src_rid = _parse_marker(source_entity, tev.get("description"))
        if not src_uid:
            continue
        target_by_source_key[(src_uid, src_rid or "")] = {
            "target": tev,
            "t_uid": tev.get("uid"),
            "t_rid": tev.get("recurrence_id"),
        }

    # Create or Update
    for key, sev in source_by_key.items():
        tgt_entry = target_by_source_key.get(key)
        if not tgt_entry:
            await _create_target_event(source_entity, target_entity, sev)
            await asyncio.sleep(0)
            continue

        tev = tgt_entry["target"]
        if not _events_equivalent(source_entity, sev, tev):
            await _update_target_event_ms365(target_entity, tgt_entry["t_uid"], tgt_entry["t_rid"], source_entity, sev)
            await asyncio.sleep(0)

    # Delete stale (only events we created, identified by marker)
    for key, info in target_by_source_key.items():
        if key in source_by_key:
            continue
        t_uid, t_rid = info["t_uid"], info["t_rid"]
        if t_uid:
            await _delete_target_event(target_entity, t_uid, t_rid)
            await asyncio.sleep(0)

# Schedules

#@time_trigger("cron(0 0 * * *)")
async def sync_all_jobs_scheduled():
    for job in JOBS:
        await _run_sync_job(job)

@service
async def sync_calendars_ms365_run_now(job_name: Optional[str] = None):
    if job_name:
        for job in JOBS:
            if job["name"] == job_name:
                await _run_sync_job(job)
                return
        log.error(f"Job '{job_name}' not found.")
        return
    # Run all
    for job in JOBS:
        await _run_sync_job(job)