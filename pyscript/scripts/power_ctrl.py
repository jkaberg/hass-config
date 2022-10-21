def climate_device(device, state):
    # {device, setpoint}
    climate_devices = {'varmtvannsbereder': 75}
    temp_adjust = 2
    new_temp = 0
    
    if device.endswith('varmtvannsbereder'):
        temp_adjust = 20

    if state == 'on':
        new_temp = climate_devices[device.replace('climate.', '')] + temp_adjust
    else:
        new_temp = climate_devices[device.replace('climate.', '')] - temp_adjust

    if new_temp:
        climate.set_temperature(entity_id=device,
                                temperature=new_temp)

def _device_ctrl(devices, state):
    if not isinstance(devices, list):
        devices = [devices]

    if not devices:
        return

    for device in devices:
        if device.startswith('climate'):
            climate_device(device, state)
        elif device.startswith('easee'):
            current = 0

            if state == 'on':
                current = int(input_select.current_easee_charger)

            easee.set_charger_max_limit(charger_id=device.replace('easee.', ''),
                                        current=current)

@state_trigger("sensor.accumulated_energy_hourly2")
def power_tariff_handler(value=None):
    value = float(value)

    devices = ['climate.varmtvannsbereder',
               'easee.EHCQPVGQ']

    if value == 0 and 'on' in (binary_sensor.priceanalyzer_is_five_cheapest, binary_sensor.priceanalyzer_is_ten_cheapest): # resume      
        _device_ctrl(devices, 'on')
    elif value >= 8.5:
        _device_ctrl(devices, 'off')


@state_trigger("binary_sensor.priceanalyzer_is_five_cheapest")
def power_is_five_cheapest(value=None): # on / off
    _device_ctrl('climate.varmtvannsbereder', value)

@state_trigger("binary_sensor.priceanalyzer_is_ten_cheapest")
def power_is_ten_cheapest(value=None): # on / off
    if not input_boolean.force_evcharge == 'on':
        _device_ctrl('easee.EHCQPVGQ', value)

@state_trigger("input_boolean.force_evcharge")
def force_evcharge(value=None): # on / off
    _device_ctrl('easee.EHCQPVGQ', value)