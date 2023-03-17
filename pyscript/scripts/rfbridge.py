from homeassistant.const import EVENT_CALL_SERVICE

# https://github.com/Portisch/RF-Bridge-EFM8BB1/blob/master/BitBucketConverter.py
def bb_conv(szInpStr, repVal):
    #log.debug("Repeat: %d" % repVal)

    szInpStr = szInpStr.replace(' ', '')

    iNbrOfBuckets = int(szInpStr[4:6], 16)
    arrBuckets = []
    szOutAux = " %0.2X " % iNbrOfBuckets
    szOutAux += "%0.2X " % int(repVal)

    for i in range(0, iNbrOfBuckets):
        szOutAux += szInpStr[6+i*4:10+i*4] + " "
        arrBuckets.append(int(szInpStr[6+i*4:10+i*4], 16))    

    #syncData = findSyncPattern(szInpStr[10+i*4:-2])
    syncData = None

    if (syncData != None):
        szOutAux += syncData
        szBits = decodeBuckets(arrBuckets, syncData[2:])
        log.debug("Decoded value: " + szBits)
    else:
        szOutAux += szInpStr[10+i*4:-2]

    szDataStr = szOutAux.replace(' ', '')
    szOutAux += " 55"
    iLength = int(len(szDataStr) / 2)
    szOutAux = "AA B0 " + "%0.2X" % iLength + szOutAux

    return szOutAux


#@time_trigger("startup")
def send_adv_code():
    raw_code = "AA B1 05 12D4 05BE 02D0 0172 1FAE 481A3A3B2B2A3A3A3B2A3A3A3A3A3B2A3A3B2B2A3A3A3A3A3A3B2B2B2B2B2A3B2A3B2B2A3A3A3A3B2B 55"

    yeh = bb_conv(raw_code, 4)
    log.debug(yeh)

    #esphome.rf_bridge_send_rf_raw(raw=yeh)
    esphome.rf_bridge_send_rf_raw(raw=yeh)
    
# brannvarslene er Flamingo FA21RF

#@event_trigger(EVENT_CALL_SERVICE) #, "domain == 'esphome'") # and service in ['rf_bridge_send_rf_raw']")
def test1(**kwargs): #domain=None, service=None, service_data=None):
    log.debug(f"{kwargs}") # "{service} - {service_data}")

#UT
#[10:53:12][I][rf_bridge:077]: Received RFBridge Advanced Code: length=0x06 protocol=0x01 code=0xCEFB3F0533
#[10:53:12][I][rf_bridge:077]: Received RFBridge Advanced Code: length=0x06 protocol=0x01 code=0xCEFB3F053C
#Received RFBridge Bucket: AA B1 05 12CA 05BE 02D0 0154 1E3C 481A3A3B2B2A3A3A3B2A3A3A3A3A3B2A3A3B2B2A3A3A3A3A3A3B2B2B2B2B2A3B2A3B2B2A3A3A3A3B2B 55

#STOP
#[10:53:18][I][rf_bridge:077]: Received RFBridge Advanced Code: length=0x06 protocol=0x01 code=0xCEFB3F0555
# Received RFBridge Bucket: AA B1 05 12CA 05C8 02D0 0168 1E6E 481A3A3B2B2A3A3A3B2A3A3A3A3A3B2A3A3B2B2A3A3A3A3A3A3B2B2B2B2B2A3B2A3B2A3B2A3B2A3B2A 55


#INN
#[10:53:47][I][rf_bridge:077]: Received RFBridge Advanced Code: length=0x06 protocol=0x01 code=0xCEFB3F0511
#[10:53:47][I][rf_bridge:077]: Received RFBridge Advanced Code: length=0x06 protocol=0x01 code=0xCEFB3F051E
#Received RFBridge Bucket: AA B1 05 12C0 05D2 02BC 0172 1EBE 481A3A3B2B2A3A3A3B2A3A3A3A3A3B2A3A3B2B2A3A3A3A3A3A3B2B2B2B2B2A3B2A3B2B2B2A3B2B2B2A 55