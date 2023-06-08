from datetime import datetime

@state_trigger("climate.panasonic_ac_2",
               "climate.panasonic_ac_3")
def heatpump_use_heat(var_name=None, value=None):
    if value == 'heat_cool':
        climate.set_hvac_mode(entity_id=var_name,
                              hvac_mode='heat')

#@time_trigger("once(04:30)", "once(22:30)")
#@state_active("climate.panasonic_ac_3 == 'off'")
def heatpump_power_on():
    climate.set_hvac_mode(entity_id='climate.panasonic_ac_3',
                          hvac_mode='heat')

#@time_trigger("once(06:00)")
#@state_trigger("group.someone_home == 'home'")
#@time_active("range(06:00, 22:30)")
#@state_active("group.someone_home == 'home'")
def heatpump_quiet():
    if datetime.now().month in range(4, 10):
        climate.set_preset_mode(entity_id='climate.panasonic_ac_3', preset_mode='Quiet')

#@time_trigger("once(22:30)")
#@state_trigger("group.someone_home == 'not_home'")
def heatpump_normal():
    if datetime.now().month in range(4, 10):
        climate.set_preset_mode(entity_id='climate.panasonic_ac_3', preset_mode='Normal')

@state_trigger("float(sensor.vaskerom_humidity) > 45")
@state_active("switch.vaskerom_avfukter == 'off'")
def humidifier_on():
    switch.turn_on(entity_id='switch.vaskerom_avfukter')

@state_trigger("float(sensor.vaskerom_humidity) < 35")
@state_active("switch.vaskerom_avfukter == 'on'")
def humidifier_off():
    switch.turn_off(entity_id='switch.vaskerom_avfukter')