from pwr_ctrl.constants import *

def is_between(a, x, b):
    return min(a, b) < float(x) < max(a, b)


def find_stage(value):
    # an stage represents devices to handle at that stage until the next stage
    counter = 0
    #last_stage = False

    stages = sorted(DEVICE_STAGES.keys())

    for stage in stages:
        try:
            next_stage = list(stages)[counter+1]
        except IndexError:
            pass # we're on last stage
            #last_stage = True
            #next_stage = round(stage) if isinstance(stage, float) else stage + 1

        if is_between(stage, value, next_stage):
            return stage, list(DEVICE_STAGES.values())[counter]

        counter += 1

        return False, False


# TODO: functions turn_on() and turn_off() blindly assumes that 
# pwr_ctrl is in full controll. However at a later stage we should
# save state (when 'off') of the device and return it to previous state
# when we 'on' an device

def restore(devices):
    if not isinstance(devices, list):
        devices = [devices]

    for device in devices:
        if device.startswith('switch'):
            switch.turn_on(entity_id=device)
        elif device.startswith('light'):
            light.turn_on(entity_id=device)
        elif device.startswith('climate'):
            # this should really restore the orginal value,
            # and not assume that its always the same static value
            curr_temp = float(state.getattr(device).get('temperature'))
            if curr_temp:
                new_temp = curr_temp + TEMP_ADJUSTMENT
                climate.set_temperature(entity_id=device,
                                        temperature=new_temp)
        elif device.startswith('easee'):
            if switch.garasje_is_enabled == 'off':
                switch.turn_on(entity_id='switch.garasje_is_enabled')

            easee.set_charger_max_limit(charger_id=device.replace('easee.', ''),
                                        current=EV_CHARGER_CURRENT_ON)


def idle(devices):
    if not isinstance(devices, list):
        devices = [devices]

    for device in devices:
        if device.startswith('switch'):
            switch.turn_off(entity_id=device)
        elif device.startswith('light'):
            light.turn_off(entity_id=device)
        elif device.startswith('climate'):
            curr_temp = float(state.getattr(device).get('temperature'))
            if curr_temp:
                new_temp = curr_temp - TEMP_ADJUSTMENT

                climate.set_temperature(entity_id=device,
                                        temperature=new_temp)
        elif device.startswith('easee'):
            easee.set_charger_max_limit(charger_id=device.replace('easee.', ''),
                                        current=EV_CHARGER_CURRENT_OFF)