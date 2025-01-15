import time
import math

def solar_elevation(latitude, longitude):
    """ Return Sun Elevation in Degrees with respect to the Horizon.
    Input:
        Latitude in Degrees and fractional degrees
        Longitude in Degrees and fractional degrees
        Local Time
        UTC Time
    Where:
        jd is Julian Date (Day of Year only), then Julian Date + Fractional True
        lt is Local Time (####) 24 hour time, no colon
        tz is Time Zone Offset (ie -7 from UTC)
        beta is Beta for EOT
        lstm is Local Standard Time Meridian
        eot is Equation of Time
        tc is Time Correction Factor
        lst is Local Solar Time
        h is Hour Angle
        dec is Declination
        se is Solar Elevation
        ** All Trigonometry Fuctions need Degrees converted to Radians **
        ** The assumption is made that correct local time is established **
    """
    if latitude is None or longitude is None:
        return None

    cos = math.cos
    sin = math.sin
    asin = math.asin
    radians = math.radians
    degrees = math.degrees
    jd = time.localtime(time.time()).tm_yday
    hr = time.localtime(time.time()).tm_hour
    min = time.localtime(time.time()).tm_min
    lt = hr + min/60
    tz = time.localtime(time.time()).tm_gmtoff/3600
    jd = jd + lt/24
    beta = (360/365) * (jd - 81)
    lstm = 15 * tz
    eot = (9.87*(sin(radians(beta*2)))) - (7.53*(cos(radians(beta)))) - (1.5*(sin(radians(beta))))
    tc = (4 * (longitude - lstm)) + eot
    lst = lt + tc/60
    h = 15 * (lst - 12)
    dec = cos(radians(((jd) + 10) * (360/365))) * (-23.44)
    se = degrees(asin(sin(radians(latitude)) * sin(radians(dec)) + cos(radians(latitude)) * cos(radians(dec)) * cos(radians(h))))
    se = round(se)

    return se

def solar_insolation(elevation, latitude, longitude):
    """ Return Estimation of Solar Radiation at current sun elevation angle.
    Input:
        Elevation in Meters
        Latitude
        Longitude
    Where:
        solar_elevation is the Sun Elevation in Degrees with respect to the Horizon
        sz is Solar Zenith in Degrees
        ah is (Station Elevation Compensation) Constant ah_a = 0.14, ah_h = Station elevation in km
        am is Air Mass of atmoshere between Station and Sun
        1353 W/M^2 is considered Solar Radiation at edge of atmoshere
        ** All Trigonometry Fuctions need Degrees converted to Radians **
    """
    if elevation is None or latitude is None or longitude is None:
        return None

    # Calculate Solar Elevation
    #solar_ele = solar_elevation(latitude, longitude)

    cos = math.cos
    sin = math.sin
    asin = math.asin
    radians = math.radians
    degrees = math.degrees
    se = solar_elevation(latitude, longitude)
    sz = 90 - se
    ah_a = 0.14
    ah_h = elevation / 1000
    ah = ah_a * ah_h
    if se >= 0:
        am = 1/(cos(radians(sz)) + 0.50572*pow((96.07995 - sz),(-1.6364)))
        si = (1353 * ((1-ah)*pow(.7, pow(am, 0.678))+ah))*(sin(radians(se)))
    else:
        am = 1
        si = 0
    si = round(si)

    return si

#@time_trigger("cron(*/1 * * * *)")
def test():
    lat = 63.397846403694764
    long = 10.410087316242366
    elev = 52

    log.debug(f"solar insolation is {solar_insolation(elev, lat, long)}")

def snow_probability(temperature, humidity):
    temperature = float(temperature)
    humidity = float(humidity)

    if temperature > 0:
        return 0.0
    
    temp_factor = max(0, min(1, (0 - temperature) / 30))
    humidity_factor = max(0, min(1, humidity / 100))
    
    return temp_factor * humidity_factor

def fog_probability(temperature, humidity):
    temperature = float(temperature)
    humidity = float(humidity)

    if temperature > 0:
        return 0.0
    
    temp_factor = max(0, min(1, (10 - temperature) / 20))
    humidity_factor = max(0, min(1, humidity / 100))
    
    return temp_factor * humidity_factor

def current_conditions(lightning_1h, precip_type, rain_rate, wind_speed, solar_el, solar_rad, solar_ins, snow_prob, fog_prob):
    """ Return local current conditions based on only weather station sesnors.
    Input:
        lightning_1h (#)
        **** Need to use the precip type number from Tempest so to get it before translations ****
        precip_type (#)
        rain_rate (imperial or metric)
        wind_speed (metric)
        solar_el (degrees)
        solar_rad (metric)
        snow_prob (%)
        fog_prob (%)
    Where:
        lightning_1h is lightning strike count within last hour
        precip_type is the type of precipitation: rain / hail
        rain_rate is the rain fall rate
        wind_speed is the speed of wind
        solar_el is the elevation of the sun with respect to horizon
        solar_rad is the measured solar radiation
        solar_ins is the calculated solar radiation
        snow_prob is the probability of snow
        fog_prob is the probability of fog
        si_p is the percentage difference in Solar Radiation and Solar Insolation
        si_d is the numeral difference in Solar Radiation and Solar Insolation
        cloudy is Boolan for cloud state
        part_cloud is Boolan for partly cloud state
        current is the Local Current Weather Condition
    """
    if (
        lightning_1h is None
        or precip_type is None
        or rain_rate is None
        or wind_speed is None
        or solar_el is None
        or solar_rad is None
        or solar_ins is None
        or snow_prob is None
        or fog_prob is None
    ):
        log.info("Something is missing to calculate current conditions %s - %s - %s - %s - %s - %s - %s - %s - %s", lightning_1h, precip_type, rain_rate, wind_speed,solar_el, solar_rad, solar_ins, snow_prob, fog_prob)
        return "clear-night"

    # Home Assistant weather conditions: clear-night, cloudy, fog, hail, lightning, lightning-rainy, partlycloudy, pouring, rainy, snowy, snowy-rainy, sunny, windy, windy-variant, exceptional
    # Exceptional not used here
    
    if solar_el <= 0: # Can not determine clouds at night
        cloudy = False
        part_cloud = False
    else:
        si_p = round(((solar_rad) / (solar_ins))) * 100
        si_d = round((solar_ins) - (solar_rad))
        if ((si_p <= 50) and (si_d >= 50)):
            cloudy = True
            part_cloud = False
        elif ((si_p <= 75) and (abs(si_d) >= 15)):
            part_cloud = True
            cloudy = False
        elif ((si_p >= 115) and (abs(si_d) >= 15)):
            part_cloud = True
            cloudy = False
        else:
            part_cloud = False
            cloudy = False

    if ((lightning_1h >= 1) and (rain_rate >= 0.01)): # any rain at all
        current = "lightning-rainy"
    elif (lightning_1h >= 1):
        current = "lightning"
    elif (precip_type == 2):
        current = "hail"
    elif (rain_rate >= 7.8): # pouring => Imperial >= 0.31 in/hr, Metric >= 7.8 mm/hr
        current = "pouring"
    elif ((snow_prob >= 50) and (rain_rate >= 0.01)): # any rain at all
        current = "snowy-rainy"
    elif (rain_rate >= 0.01): # any rain at all
        current = "rainy"
    elif ((wind_speed >= 11.17) and (cloudy)): # windy => Imperial >= 25 mph, Metric >= 11.17 m/s
        current = "windy-variant"
    elif (wind_speed >= 11.17): # windy => Imperial >= 25 mph, Metric >= 11.17 m/s
        current = "windy"
    elif (fog_prob >= 50):
        current = "fog"
    elif ((snow_prob >= 50) and (cloudy)):
        current = "snowy"
    elif (cloudy == 'true'):
        current = "cloudy"
    elif (part_cloud):
        current = "partlycloudy"
    elif (solar_el >= 0 ): # if daytime
        current = "sunny"
    else:
        current = "clear-night"

    # return the standard weather conditions as used by Home Assistant
    return current

#@time_trigger("cron(*/1 * * * *)")
def test():
    lat = 63.397846403694764
    long = 10.410087316242366
    elev = 52

    res = current_conditions(sensor.st_00117532_lightning_count,
                             sensor.st_00117532_precipitation_type,
                             sensor.st_00117532_nedborsintensitet,
                             sensor.st_00117532_vindstyrke,
                             sun.sun.elevation,
                             sensor.st_00117532_innstraling,
                             sensor.st_00117532_innstraling,
                             snow_probability(sensor.st_00117532_temperatur, sensor.st_00117532_luftfuktighet),
                             fog_probability(sensor.st_00117532_temperatur, sensor.st_00117532_luftfuktighet),)

    log.debug(f"current weather is {res}")