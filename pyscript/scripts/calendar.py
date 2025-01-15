from aiofile import async_open

from uuid import uuid4
from datetime import datetime
from dateutil.relativedelta import relativedelta

from icalendar import Calendar, Event

@state_trigger("calendar.familie")
@service
@time_trigger("cron(* */2 * * *)")
async def cal_to_ical(var_name="calendar.familie", months=2):
    calendar = hass.data['calendar'].get_entity(var_name)

    if calendar:
        start_date = datetime.now()
        end_date = start_date + relativedelta(months=months)
        events = calendar.async_get_events(hass, start_date, end_date)

        c = Calendar()
        c.add('PRODID', calendar.name)
        c.add('VERSION', '2.0')
        c.add('X-WR-RELCALID', calendar.name)
        c.add('X-WR-CALNAME', calendar.name)
        c.add('X-WR-TIMEZONE', 'Europe/Oslo')
        c.add('X-AUTHOR', 'https://github.com/jkaberg')

        for event in events:
            e = Event()
            e.add('description', event.description)
            e.add('uid', str(uuid4()))
            e.add('summary', event.summary)
            e.add('location', event.location)
            e.add('dtstart', event.start)
            e.add('dtend', event.end)
            e.add('dtstamp', start_date)

            c.add_component(e)

        async with async_open(f"/config/www/{calendar.name.lower()}.ical", "w+") as f:
            f.write(c.to_ical().decode("utf-8"))