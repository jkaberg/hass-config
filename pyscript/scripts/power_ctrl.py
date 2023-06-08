from datetime import datetime

from history import _get_statistic, _get_history

state.persist("pyscript.PWR_CTRL", default_value=0)


def season_heating(heater_type=None):
    estimated_outside_temp = float(sensor.estimated_outside_temp)

    season = 'winter'

    # season and temperature, the temperature when to consider with in range of the season.
    seasons = {'midseason': 8, # spring, autumn
               'summer': 16}

    for s, temp in seasons.items():
        if estimated_outside_temp > temp:
            season = s

    heaters = {
               'bathroom': {'summer': 22, 'midseason': 23, 'winter': 24},
               'bedroom': {'summer': 'off', 'midseason': 20, 'winter': 20},
               'main_bedroom': {'summer': 'off', 'midseason': 'off', 'winter': 18},
               'floorheating': {'summer': 21, 'midseason': 23, 'winter': 23},
               'livingroom': {'summer': 'off', 'midseason': 21, 'winter': 21}
              }

    log.debug(f"season: {season} | outside estimated temp: {estimated_outside_temp} | temp: {temp} | heater type: {heater_type}")
        
    return heaters.get(heater_type).get(season)

#@time_trigger("cron(0 0 1 * *)")
def energy_tarif():
    """ Set our target energy tarif for current month """
    summer_time = range(4,9) # april til september
    tarif = 5 if datetime.now().month in range(4, 9) else 10

    state.set('input_select.energy_tariff', value=tarif)

@state_trigger("input_boolean.away_mode")
def away_mode(value=None):
    away = True if value == 'on' else False

    # TODO: Consider re-enable this? Does it make sense? 
    #boiler(inactive=away)
    heating(inactive=away)

@state_trigger("sensor.nygardsvegen_6_forbruk")
@state_active("input_boolean.away_mode == 'off'")
def power_tarif(value=None):
    """ Adjust boiler and heating if we go above tresholds
        The check() function == a very simple state machine
        to keep track of what has been done.
    """
    value = float(value)
    energy_tarif = float(input_select.energy_tariff)

    def check(n, v=value):
        if v > n and v > float(pyscript.PWR_CTRL):
            pyscript.PWR_CTRL = n
            return True
        return False

    if check(energy_tarif - 0.2): # 4.8 / 9.8
        heating(inactive=True)
    elif check(energy_tarif - 0.4): # 4.5 / 9.5
        boiler(inactive=True)
    elif value == 0:
        pyscript.PWR_CTRL = 0

#@state_trigger("binary_sensor.priceanalyzer_is_ten_cheapest")
#@time_trigger("cron(0 * * * *)")
#@state_active("input_boolean.away_mode == 'off'")
#def boiler(inactive=False):
#    """ Handle boiler with regard to five cheapest hours """
#    if binary_sensor.priceanalyzer_is_ten_cheapest == 'on' and not inactive:
#      switch.turn_on(entity_id='switch.vaskerom_vvb')
#    else:
#      switch.turn_off(entity_id='switch.vaskerom_vvb')


@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def boiler(inactive=False):
    """ Handle boiler with regard to cheapest hours """
    value = float(sensor.vvbsensor_tr_heim)

    if inactive:
        value = 40

    climate.set_temperature(entity_id='climate.varmtvannsbereder', temperature=value)

@state_trigger("sensor.priceanalyzer_tr_heim_2")
@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def heating(inactive=False, away_temp_adjust=4):
    """ Handle heating using the heat capicator apphroach """
    value = -abs(away_temp_adjust) if inactive else float(sensor.priceanalyzer_tr_heim_2)

    # climate entity: setpoint
    heaters = {'climate.inngang': season_heating('livingroom'),
               'climate.hovedsoverom': season_heating('main_bedroom'),
               'climate.stort_soverom': season_heating('bedroom'),
               'climate.mellom_soverom': season_heating('bedroom'),
               'climate.litet_soverom': season_heating('bedroom'),
               'climate.gulvvarme_bad_1_etg': season_heating('bathroom'),
               'climate.gulvvarme_bad_2_etg': season_heating('bathroom'),
               'climate.panasonic_ac': season_heating('livingroom'),
               'climate.panasonic_ac_3': season_heating('livingroom'),
               'climate.gulvvarme_inngang': season_heating('floorheating'),
               'climate.gulvvarme_stue': season_heating('floorheating'),
               'climate.gulvvarme_kjokken': season_heating('floorheating'),
               'climate.gulvvarme_tv_stue': season_heating('floorheating'),
               'climate.panelovn_kontor': season_heating('livingroom')}

    for heater, temp in heaters.items():
        log.debug(f"processing heater {heater} and temp/value {temp}")

        if temp == 'off' and state.get(heater) != 'off':
            log.debug(f"turning off {heater}")
            climate.set_hvac_mode(entity_id=heater,
                                  hvac_mode='off')
        else:
            temp += value

            try:
                if state.get(heater) == 'off':
                    log.debug(f"turning on {heater}")
                    climate.set_hvac_mode(entity_id=heater,
                                          hvac_mode='heat')

                if float(state.getattr(heater).get('temperature')) != temp:
                    log.debug(f"setting temp {temp} on {heater}")
                    climate.set_temperature(entity_id=heater,
                                            temperature=temp)
            except TypeError:
                # device unavilable or similar.
                pass