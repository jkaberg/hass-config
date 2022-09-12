d = { 'BCA40C':['rf_1','ON','true'],
      'BCA404':['rf_1','OFF','true'],
      'BCA40A':['rf_2','ON','true'],
      'BCA402':['rf_2','OFF','true'],
      'BCA409':['rf_3','ON','true'],
      'BCA401':['rf_3','OFF','true']
    }

p = str(data.get('payload'))

if p is not None:
  if p in d.keys():
    service_data = {'topic':'home/{}'.format(d[p][0]), 'payload':'{}'.format(d[p][1]), 'qos':0, 'retain':'{}'.format(d[p][2])}
  else:
    service_data = {'topic':'home/unknown', 'payload':'{}'.format(p), 'qos':0, 'retain':'false'}
    logger.warning('<rfbridge_demux> Received unknown RF command: {}'.format(p))
  hass.services.call('mqtt', 'publish', service_data, False)
