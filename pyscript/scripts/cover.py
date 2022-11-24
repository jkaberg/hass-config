# ta ned etter 1 min
@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) > 13000 \
               and float(sensor.azimuth) > 157 \
               and float(sensor.azimuth) < 255 \
               and int(sensor.panasonic_ac_outside_temperature) > 2 \
               and float(sensor.vaerstasjon_velocity) < 20", state_hold=30)
@state_active("cover.screen_kortvegg == 'open'")
def kortvegg_close():
    cover.close_cover(entity_id='cover.screen_kortvegg')

# ta opp etter 15 min
@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) < 13000",
               "float(sensor.vaerstasjon_velocity) > 20",
               "int(sensor.panasonic_ac_outside_temperature) < 2",
               state_hold=900)
@state_active("cover.screen_kortvegg == 'closed'")
def kortvegg_open():
    cover.open_cover(entity_id='cover.screen_kortvegg')


@time_trigger("once(08:30)", "once(22:00)")
@state_trigger("group.someone_home == 'not_home'")
@state_active("cover.garage_port == 'open'")
def garage_port_close():
    cover.close_cover(entity_id='cover.garage_port')
