# ta ned etter 1 min
#@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) >= 13000 \
#                and float(sensor.azimuth) >= 157 \
#                and float(sensor.azimuth) <= 255 \
#                and int(sensor.panasonic_ac_outside_temperature) >= 2 \
#                and float(sensor.vaerstasjon_velocity) <= 25", 
#                state_hold=60)
#@state_active("cover.screens_kortvegg == 'open'")
def kortvegg_ned(**kwargs):
    cover.close_cover(entity_id='cover.screens_kortvegg')

# ta opp etter 15 min
#@state_trigger("int(sensor.utendor_bevegelse_sensor_illuminance_lux) <= 13000", state_hold=900)
#@state_trigger("float(sensor.vaerstasjon_velocity) >= 25")
#@state_active("cover.screens_kortvegg == 'closed'")
def kortvegg_opp(**kwargs):
    cover.open_cover(entity_id='cover.screens_kortvegg')