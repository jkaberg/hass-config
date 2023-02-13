from asyncio import sleep

state.persist("pyscript.VENT_GARAGE", default_value=False)

# ta ned etter 1 min
@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) > 13000 \
               and float(sensor.azimuth) > 157 \
               and float(sensor.azimuth) < 255 \
               and int(sensor.panasonic_ac_outside_temperature_3) > 2 \
               and float(sensor.vaerstasjon_velocity) < 20", state_hold=30)
@state_active("cover.screen_kortvegg == 'open'")
def kortvegg_close():
    cover.close_cover(entity_id='cover.screen_kortvegg')

# ta opp etter 15 min
@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) < 13000",
               "float(sensor.vaerstasjon_velocity) > 20",
               "int(sensor.panasonic_ac_outside_temperature_3) < 2",
               state_hold=900)
@state_active("cover.screen_kortvegg == 'closed'")
def kortvegg_open():
    cover.open_cover(entity_id='cover.screen_kortvegg')


@time_trigger("once(08:30)", "once(22:00)")
@state_trigger("group.someone_home == 'not_home'")
@state_active("cover.garage_port == 'open' and pyscript.VENT_GARAGE == 'false'")
def garage_port_close():
    cover.close_cover(entity_id='cover.garage_port')

#@time_trigger("cron(0 * * * *)")
@state_active("cover.garage_port == 'closed'")
def vent_garage():
    cover_name='cover.garage_port'
    log.debug('Checking if garage needs ventilation')

    if float(sensor.garasje_sensor_humidity) > 60.0 and pyscript.VENT_GARAGE == 'False': #and state.get(cover_name) == 'closed':
        log.debug('High humidity in the garage, opening garage door for ventilation')
        cover.open_cover(entity_id=cover_name)
        sleep(2) # let it run just enough so that the top "board" opens 30 cm
        cover.stop_cover(entity_id=cover_name)

        return state.set('pyscript.VENT_GARAGE', 'True')
    elif pyscript.VENT_GARAGE == 'True': # and state.get(cover_name) == 'open': # opened
        log.debug('Garage ventilation done, closing garage door')
        cover.close_cover(entity_id=cover_name)

        return state.set('pyscript.VENT_GARAGE', 'False')



