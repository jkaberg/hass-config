@state_trigger("climate.panasonic_ac == 'heat_cool'")
def heatpump_use_heat():
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')

@time_trigger("once(06:00)", "once(09:00)", "once(15:00)", "once(22:30)")
def heatpump_handle_noise(trigger_time=None, var_name='climate.panasonic_ac', preset_mode='Quiet'):
    hour = trigger_time.now().hour

    if hour == 9 and not group.someone_home == 'home' or hour == 22:
        preset_mode='Normal'

    climate.set_preset_mode(entity_id=var_name, preset_mode=preset_mode)

@state_trigger("sensor.vaskerom_humidity")
def handle_humidifier(value=None):
    value = float(value)

    if value > 40 and switch.vaskerom_avfukter == 'off':
        switch.turn_on(entity_id='switch.vaskerom_avfukter')
    elif value < 40 and switch.vaskerom_avfukter == 'on':
        switch.turn_off(entity_id='switch.vaskerom_avfukter')