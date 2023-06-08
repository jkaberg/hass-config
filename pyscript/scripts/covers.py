@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) > 15000 \
               and float(sensor.sun_solar_azimuth) > 157 \
               and float(sensor.sun_solar_azimuth) < 330 \
               and float(sensor.vaerstasjon_velocity) < 20", state_hold=30)
@state_active("cover.screen_kortvegg == 'open'")
def kortvegg_close():
    cover.close_cover(entity_id='cover.screen_kortvegg')

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