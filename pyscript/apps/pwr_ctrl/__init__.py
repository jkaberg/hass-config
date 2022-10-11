from pwr_ctrl.helpers import *
from pwr_ctrl.constants import *

state.persist(PYSCRIPT_PWR_CTRL_VARNAME, default_value={})

#@state_trigger("input_boolean.powersaver_active")
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

#@state_trigger("input_boolean.force_evcharge")
def force_evcharge(value=None, **kwargs):
    """
    Force EV charging even tho energy price is high
    """
    if value == 'on':
        restore('easee.EHCQPVGQ')
    else:
        idle('easee.EHCQPVGQ')

#@state_trigger("sensor.accumulated_energy_hourly2")
def power_handler(value=None, **kwargs):
    """
    Handle tariff effect and shut down devices as we pass stages,
    and then turn back on at next full hour
    """
    value = float(value)
    stage, devices = find_stage(value)
    stage_name = str(stage).replace(".", "_")

    if devices and not state.getattr(PYSCRIPT_PWR_CTRL_VARNAME).get(stage_name):
        idle(devices)
        state.setattr(f"{PYSCRIPT_PWR_CTRL_VARNAME}.{stage_name}", True)

    # so this is quite dumb. we should have logic here to handle devices that is normaly on and resume them as we go
    elif value == 0 and input_boolean.powersaver_active == 'on':
        restore(ALL_DEVICES)

        for stage, value in state.getattr(PYSCRIPT_PWR_CTRL_VARNAME):
            state.setattr(f"{PYSCRIPT_PWR_CTRL_VARNAME}.{stage_name}", False)


# vi trenger en funksjon som analyserer prisen til nordpool, og utefra den setter en variable med type nivåene "billig, mellom, dyrt, veldig dyrt" for inneværende time
