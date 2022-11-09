import aiohttp
import asyncio
from aiofile import async_open

import uuid
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from icalendar import Calendar, Event

def parse_dtf(text):
    for fmt in ['%Y-%m-%dT00:00:00Z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d']:
        try:
            return datetime.strptime(text, fmt)
        except (ValueError, TypeError):
            pass
    return None

@time_trigger("cron(0 * * * *)")
async def cal_to_ical(calendar="calendar.familie", months=2):
    base_url = "http://localhost:8123/api/calendars"
    access_token = pyscript.config.get('global').get('longlived_access_token')
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {access_token}"
        }

    str_format = '%Y-%m-%dT00:00:00Z'
    now = date.today()
    end = now + relativedelta(months=months)
    cal_name = 'Calendar'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, headers=headers) as resp:
            for cal in resp.json():
                if calendar == cal.get('entity_id'):
                    cal_name = cal.get('name')

        url = f"{base_url}/{calendar}?start={now.strftime(str_format)}&end={end.strftime(str_format)}"

        async with session.get(url, headers=headers) as resp:
            calendar = resp.json()

            c = Calendar()
            c.add('PRODID', cal_name)
            c.add('VERSION', '2.0')
            c.add('X-WR-RELCALID', cal_name)
            c.add('X-WR-CALNAME', cal_name)
            c.add('X-WR-TIMEZONE', 'Europe/Oslo')
            c.add('X-AUTHOR', 'https://github.com/jkaberg')

            for event in calendar:
                estart = event.get('start').get('dateTime')
                eend = event.get('end').get('dateTime')

                if None in [estart, eend]: # entire day event
                    estart = event.get('start').get('date')
                    eend = event.get('end').get('date')

                e = Event()
                e.add('description', event.get('description'))
                e.add('uid', str(uuid.uuid4()))
                e.add('summary', event.get('summary'))
                e.add('location', event.get('location'))
                e.add('dtstart', parse_dtf(estart))
                e.add('dtend', parse_dtf(eend))
                e.add('dtstamp', datetime.now())

                c.add_component(e)

            async with async_open(f"/config/www/{cal_name.lower()}.ical", "w+") as f:
                f.write(c.to_ical().decode("utf-8"))