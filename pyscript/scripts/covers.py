OUTDOOR_LUX_LEVEL_TRIGGER = 45000
GARAGE_HUMIDTY_TRESHOLD = 65

@state_trigger("int(sensor.weatherflow_brightness) > OUTDOOR_LUX_LEVEL_TRIGGER", state_hold=300)
@state_active("cover.screen_kortvegg == 'open' \
               and float(sensor.sun_solar_azimuth) in range(157, 330) \
               and float(sensor.weatherflow_wind_speed) < 20")
def kortvegg_close():
    cover.close_cover(entity_id='cover.screen_kortvegg')

@state_trigger("int(sensor.weatherflow_brightness) < (OUTDOOR_LUX_LEVEL_TRIGGER * 0.9)",
               "float(sensor.weatherflow_wind_speed) > 20",
               state_hold=900)
@state_active("cover.screen_kortvegg == 'closed'")
def kortvegg_open():
    cover.open_cover(entity_id='cover.screen_kortvegg')

@state_trigger("float(sensor.garasje_sensor_humidity) > GARAGE_HUMIDTY_TRESHOLD")
@time_active("range(06:00, 22:30)")
@state_active("sensor.garage_door_detailed_status != 'venting'")
def vent_garage_open():
    switch.turn_on(entity_id='switch.garage_door_vent')

@time_trigger("once(22:30)")
@state_trigger("group.someone_home == 'not_home'",
               "float(sensor.garasje_sensor_humidity) < (GARAGE_HUMIDTY_TRESHOLD - 5)")
@state_active("sensor.garage_door_detailed_status != 'closed'")
def vent_garage_close():
    cover.close_cover(entity_id='cover.garage_door')