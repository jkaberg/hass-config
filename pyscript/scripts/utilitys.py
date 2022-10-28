@time_trigger("once(06:00)", "once(22:00)")
def change_peak(trigger_time=None):
    peak = 'peak' 
    
    if trigger_time.weekday() in [5, 6] or trigger_time.now().hour > 21 or trigger_time.now().hour < 6:
        peak = 'offpeak'
    
    select.accumulated_energy_hourly2 = peak