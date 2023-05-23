@time_trigger("once(06:00)", "once(22:00)")
def change_peak(trigger_time=None):
    select.accumulated_energy_hourly2 = 'offpeak' if trigger_time.now().hour == 22 else 'peak'