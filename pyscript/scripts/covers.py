from asyncio import sleep

state.persist("pyscript.VENT_GARAGE", default_value=False)
state.persist("pyscript.GARAGE_DIRECTION", default_value='closing')


# ta ned etter 1 min
@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) > 15000 \
               and float(sensor.azimuth) > 157 \
               and float(sensor.azimuth) < 310 \
               and float(sensor.vaerstasjon_velocity) < 20", state_hold=30)
@state_active("cover.screen_kortvegg == 'open'")
def kortvegg_close():
    cover.close_cover(entity_id='cover.screen_kortvegg')

# ta opp etter 15 min
@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) < 15000",
               "float(sensor.vaerstasjon_velocity) > 20",
               state_hold=900)
@state_active("cover.screen_kortvegg == 'closed'")
def kortvegg_open():
    cover.open_cover(entity_id='cover.screen_kortvegg')


@time_trigger("once(08:30)", "once(22:00)")
@state_trigger("group.someone_home == 'not_home'")
@state_active("cover.garage_port == 'open'")
def garage_port_close():
    cover.close_cover(entity_id='cover.garage_port')
    pyscript.VENT_GARAGE = 'false'


#@time_trigger("cron(*/1 * * * *)")
#@state_active("cover.garage_port == 'closed'")
#@time_active("range(07:00, 21:30)")
#@state_active("group.someone_home == 'home'")
def vent_garage():
    cover_name='cover.garage_port'
    humidity = float(sensor.garasje_sensor_humidity)
    cut_off = 60.0
    log.debug(f"Garage: Checking if humidity is above {cut_off}")

    if humidity > cut_off \
        and pyscript.VENT_GARAGE == 'false' \
        and cover.garage_port == 'closed': # door is closed
        log.debug(f"Garage: High humidity, opening garage door")
        cover.open_cover(entity_id=cover_name)
        sleep(2) # let it run just enough so that the top "board" opens 30 cm
        cover.stop_cover(entity_id=cover_name)

        pyscript.VENT_GARAGE = 'true'
    elif humidity < cut_off \
         and pyscript.VENT_GARAGE == 'true' \
         and state.get(cover_name) == 'open': # opened
        log.debug(f"Garage: Low humidity, closing garage door")
        cover.close_cover(entity_id=cover_name)

        pyscript.VENT_GARAGE = 'false'