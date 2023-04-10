from datetime import datetime

@state_trigger("climate.panasonic_ac_2",
               "climate.panasonic_ac_3")
def heatpump_use_heat(var_name=None, value=None):
    if value == 'heat_cool':
        climate.set_hvac_mode(entity_id=var_name,
                              hvac_mode='heat')

@time_trigger("once(04:30)", "once(22:30)")
@state_active("climate.panasonic_ac_3 == 'off'")
def heatpump_power_on():
    climate.set_hvac_mode(entity_id='climate.panasonic_ac_3',
                          hvac_mode='heat')

@time_trigger("once(06:00)", "once(22:30)")
@state_trigger("group.someone_home")
@time_active("range(06:00, 22:30)")
def heatpump_handle_noise():
    preset_mode = 'Quiet'

    if datetime.now().hour == 22 or group.someone_home == 'not_home':
        preset_mode = 'Normal'

    climate.set_preset_mode(entity_id='climate.panasonic_ac_3', preset_mode=preset_mode)

@state_trigger("sensor.vaskerom_humidity")
def handle_humidifier(value=None):
    value = float(value)

    if value > 40 and switch.vaskerom_avfukter == 'off':
        switch.turn_on(entity_id='switch.vaskerom_avfukter')
    elif value < 40 and switch.vaskerom_avfukter == 'on':
        switch.turn_off(entity_id='switch.vaskerom_avfukter')