from datetime import datetime

from history import _get_statistic, _get_history

state.persist("pyscript.PWR_CTRL", default_value=0)


def season_heating(heater_type=None):
    estimated_outside_temp = float(sensor.estimated_outside_temp)

    season = 'winter'

    # season and temperature, the temperature when to consider with in range of the season.
    seasons = {'midseason': 8, # spring, autumn
               'summer': 12}

    # check if estimated outside temp above treshold for season
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

#    log.debug(f"season: {season} | outside estimated temp: {estimated_outside_temp} | temp: {temp} | heater type: {heater_type}")
    
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

    heating(inactive=away)

@state_trigger("sensor.nygardsvegen_6_forbruk")
@state_active("input_boolean.away_mode == 'off'")
def power_tarif(value=None):
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

@time_trigger("cron(0 * * * *)")
def boiler(inactive=False):
    """ Handle boiler with regard to cheapest hours """
    value = float(sensor.vvbsensor_tr_heim)

    if inactive or input_boolean.away_mode == 'on':
        value = 40

    climate.set_temperature(entity_id='climate.varmtvannsbereder', temperature=value)

@state_trigger("sensor.priceanalyzer_tr_heim_2")
@time_trigger("cron(0 * * * *)")
def heating(inactive=False):
    value = float(sensor.priceanalyzer_tr_heim_2)

    if inactive or input_boolean.away_mode == 'on':
        value = -abs(4)

    # climate entity: setpoint
    heaters = {'climate.hovedsoverom': season_heating('main_bedroom'),
               'climate.stort_soverom': season_heating('bedroom'),
               'climate.mellom_soverom': season_heating('bedroom'),
               'climate.litet_soverom': season_heating('bedroom'),
               'climate.gulvvarme_bad_1_etg': season_heating('bathroom'),
               'climate.gulvvarme_bad_2_etg': season_heating('bathroom'),
               'climate.panasonic_ac': season_heating('livingroom'), #gangen
               'climate.panasonic_ac_3': season_heating('livingroom'), #2etasje
               'climate.gulvvarme_inngang': season_heating('floorheating'),
               'climate.gulvvarme_stue': season_heating('floorheating'),
               'climate.gulvvarme_kjokken': season_heating('floorheating'),
               'climate.gulvvarme_tv_stue': season_heating('floorheating'),
               'climate.panelovn_kontor': season_heating('livingroom')}

    for heater, temp in heaters.items():
        #log.debug(f"processing heater {heater} and temp/value {temp}")

        if temp == 'disabled':
            continue
        elif temp == 'off':
            if state.get(heater) != 'off':
                #log.debug(f"turning off {heater}")
                climate.set_hvac_mode(entity_id=heater,
                                      hvac_mode='off')
        else:
            temp += value

            try:
                if state.get(heater) == 'off':
                    #log.debug(f"turning on {heater}")
                    climate.set_hvac_mode(entity_id=heater,
                                          hvac_mode='heat')

                if float(state.getattr(heater).get('temperature')) != temp:
                    #log.debug(f"setting temp {temp} on {heater}")
                    climate.set_temperature(entity_id=heater,
                                            temperature=temp)
            except TypeError:
                # device unavilable or similar.
                pass