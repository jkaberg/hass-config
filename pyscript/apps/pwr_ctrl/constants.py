PYSCRIPT_PWR_CTRL_VARNAME = "pyscript.PWR_CTRL"
#################
# Device stages #
#################

# Priority ranging 'low' to 'critical'
DEVICE_STAGES = {8.4: ['switch.varmtvannsbereder',
                       'easee.EHCQPVGQ'],
                 8.7: ['dummy.test'],
                 9.0: ['dummy.test'],
                 9.5: ['dummy.test']}

ALL_DEVICES = [y for x in DEVICE_STAGES.values() for y in x]

##############
# EV CHARGER #
##############
EV_CHARGER_CURRENT_ON=int(input_select.current_easee_charger)
EV_CHARGER_CURRENT_OFF=0

########
# MISC #
########
TEMP_ADJUSTMENT = 2