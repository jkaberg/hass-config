from asyncio import sleep

@state_trigger("sensor.ble_opening_percentage_ble_garage_port")
def garage_direction(value=None, old_value=None):
    value = float(value)
    old_value = float(old_value)

    if value == 100:
        pyscript.GARAGE_DIRECTION = "open"
    elif value == 0:
        pyscript.GARAGE_DIRECTION = "closed"
    elif value > old_value:
        pyscript.GARAGE_DIRECTION = "opening"
    elif value < old_value:
        pyscript.GARAGE_DIRECTION = "closing"

@service
def garage_cover_position(value=None):
    eid = "switch.garasje_port_5"

    def change_direction():
        # double tap to change direction
        switch.turn_on(entity_id=eid)
        sleep(1)
        switch.turn_on(entity_id=eid)

    if value == 'open':
        if pyscript.GARAGE_DIRECTION in ["closing", "opening"]:
            change_direction()
        elif pyscript.GARAGE_DIRECTION == "closed":
            switch.turn_on(entity_id=eid)
    elif value == 'close':
        if pyscript.GARAGE_DIRECTION in ["closing", "opening"]:
            change_direction()
        elif pyscript.GARAGE_DIRECTION == "open":
            switch.turn_on(entity_id=eid)

@service
def garget_set_position(new_pct=None):
    tick = 0
    travel_time = 0
    eid = "switch.garasje_port_5"
    timers = {"open": 13.0, "close": 23.2}
    current_pct = float(sensor.ble_opening_percentage_ble_garage_port)
    new_direction = "open" if new_pct > current_pct else "close"
    current_direction = pyscript.GARAGE_DIRECTION

    def tap(taps=2, sleept=0.5):
        # double tap to change direction
        for i in range(taps):
            switch.turn_on(entity_id=eid)
            sleep(sleept)
            log.debug("hlelooooo")

        #travel_time += (taps * sleept)

    diff = abs(new_pct - current_pct)
    travel_time = (timers.get(new_direction) / 100) * diff

    log.debug(f"Current pct: {current_pct} | Direction: {new_direction} | Current direction: {current_direction} | Diff: {diff} | Travel time: {travel_time}")

    if not new_pct == current_pct:
        if new_direction == "open" and current_direction == "opening":
            if new_pct > current_pct:
                tap(4)
            else:
                tap(2)
        elif new_direction == "close" and current_direction == "closing":
            if new_pct > current_pct:
                tap(4)
            else:
                tap(2)
        else:
            tap(1)

        if not new_pct in [0, 100]:
            sleep(travel_time)
            log.debug('sleeping done')
            switch.turn_on(entity_id=eid)