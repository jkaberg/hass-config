from pwr_ctrl.helpers import *
from pwr_ctrl.constants import *

state.persist("pyscript.PWR_CTRL", default_value={})

@state_trigger("input_boolean.powersaver_active")
def powersaver_active(value=None, **kwargs):
    """
    Regulate devices according to energy prices


    We need better logic here =]
    """

    devices = ALL_DEVICES

    # we can use electric, its cheap!
    if value == 'on':
        restore(devices)
    else:
        if input_boolean.force_evcharge == 'on':
            devices.remove('easee.EHCQPVGQ')
        
        idle(devices)

@state_trigger("input_boolean.force_evcharge")
def force_evcharge(value=None, **kwargs):
    """
    Force EV charging even tho energy price is high
    """
    if value == 'on':
        restore('easee.EHCQPVGQ')
    else:
        idle('easee.EHCQPVGQ')

@state_trigger("sensor.accumulated_energy_hourly2")
def power_handler(value=None, **kwargs):
    """
    Handle tariff effect and shut down devices as we pass stages,
    and then turn back on at next full hour
    """
    value = float(value)
    stage, devices = find_stage(value) # find our stage as in does current consumption match any stage?
    stage_name = str(stage).replace(".", "_")
    temp = {} if not pyscript.PWR_CTRL else pyscript.PWR_CTRL

    if devices and not pyscript.PWR_CTRL.get(stage_name):
        # since we didnt find any stage already set
        # lets turn these devices off
        # storing the stage state in temp
        idle(devices)
        temp[stage_name] = True

    # so this is quite dumb. we should have logic here to handle devices that is normaly on and resume them as we go
    elif value == 0 and input_boolean.powersaver_active == 'on':
        # past full hour
        # restore all devices to previous state
        # and set all stages to False indicating they are not active yet
        restore(ALL_DEVICES)

        if pyscript.PWR_CTRL:
            for stage, value in pyscript.PWR_CTRL.items():
                temp[stage] = False

    #log.error(temp)
    #log.error(pyscript.PWR_CTRL)

    pyscript.PWR_CTRL = temp

# vi trenger en funksjon som analyserer prisen til nordpool, og utefra den setter en variable med type nivåene "billig, mellom, dyrt, veldig dyrt" for inneværende time
