from datetime import datetime, time

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

@time_trigger("once(04:00:00)")
@state_active("climate.panasonic_ac == 'off' \
               and float(sensor.kjokken_sensor_temperature) < 21")
def morning_heat_on():
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')

@state_trigger("climate.panasonic_ac == 'heat_cool'")
def heatpump_use_heat():
    """
    We never want to use heat_cool since it both heat and
    cool the air, thus using a lot of energy for nothing.

    Normally this only happends when the heatpump is activated
    via Google Assistant/Home.
    """
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')

@time_trigger("once(05:30)", "once(22:30)")
@state_trigger("group.someone_home", "climate.panasonic_ac == 'heat'")
def heatpump_silent_mode():
    mode = 'medium'

    if group.someone_home == 'home' and is_time_between(time(5,30), time(22,29)):
        mode = 'low'

    climate.set_fan_mode(entity_id='climate.panasonic_ac',
                         fan_mode=mode)

@state_trigger("sensor.vaskerom_humidity")
def handle_humidifier(value=None):
    value = float(value)

    if value > 40 and switch.vaskerom_avfukter == 'off':
        switch.turn_on(entity_id='switch.vaskerom_avfukter')
    elif value < 40 and switch.vaskerom_avfukter == 'on':
        switch.turn_off(entity_id='switch.vaskerom_avfukter')
