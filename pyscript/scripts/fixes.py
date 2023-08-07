@time_trigger("startup", "cron(0 * * * *)")
@time_active("range(15:00, 22:00)")
@state_active("sensor.nordpool_kwh_trheim_nok_3_00_0.tomorrow_valid == 'false'")
def fix_nordpool():
    homeassistant.reload_config_entry(entity_id='sensor.nordpool_kwh_trheim_nok_3_00_0')

@time_trigger("startup", "cron(0 * * * *)")
@time_active("range(15:00, 22:00)")
@state_active("sensor.priceanalyzer_tr_heim_2.tomorrow_valid == 'false'")
def fix_priceanalyzer():
    homeassistant.reload_config_entry(entity_id='sensor.priceanalyzer_tr_heim_2')