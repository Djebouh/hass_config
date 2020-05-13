""""
Read data from Parrot Pot plant sensor.
"""

from datetime import datetime, timedelta
from struct import unpack
import logging
import math
from threading import Lock
from btlewrap.base import BluetoothInterface, BluetoothBackendException

HANDLES = [
    ["battery", 0x004b],
    ["name", 0x03],
    ["soil_temperature", 0x0034],
    ["air_temperature", 0x0037],
    ["air_temperature_cal", 0x0044],
    ["moisture_live", 0x003a],
    ["moisture_cal", 0x0041],
    # ["light", 0x0025],
    ["light_int", 0x0025],
    ["dli_cal", 0x0047],
    ["conductivity", 0x0031],
    ["moisture_rj", 0x0031],
    ["watertank_Level", 0x008b],
    ["watering_mode", 0x0090],
    ["watering_status", 0x009a]
]

_LOGGER = logging.getLogger(__name__)

def format_bytes(raw_data):
    """Prettyprint a byte array."""
    if raw_data is None:
        return 'None'
    return ' '.join([format(c, "02x") for c in raw_data]).upper()


class ParrotPotPoller(object):
    """"
    A class to read data from Parrot Pot plant sensors.
    """

    def __init__(self, mac, backend, cache_timeout=600, retries=3, adapter='hci0'):
        """
        Initialize a Parrot Pot Poller for the given MAC address.
        """


        _LOGGER.debug('ParrotPotPoller intialized with mac %s, backend %s and adapter %s .', mac, backend.__name__, adapter)

        self._mac = mac
        self._bt_interface = BluetoothInterface(backend, adapter=adapter)
        self._cache = None
        self._cache_timeout = timedelta(seconds=cache_timeout)
        self._last_read = None
        self._fw_last_read = None
        self.retries = retries
        self.ble_timeout = 10
        self.lock = Lock()

    
    def name(self):
        """Return the name of the sensor."""
        with self._bt_interface.connect(self._mac) as connection:
            name = connection.read_handle(_HANDLE_READ_NAME)  # pylint: disable=no-member

        if not name:
            raise BluetoothBackendException("Could not read data from Parrot Pot sensor %s" % self._mac)
        return ''.join(chr(n) for n in name)

    
    def battery_level(self):
        """Return the battery level.

        The battery level is updated when reading the firmware version. This
        is done only once every 24h
        """
        
        with self._bt_interface.connect(self._mac) as connection:
            data = connection.read_handle(_HANDLE_READ_VERSION_BATTERY)
            _LOGGER.debug('Received result for handle %s: %s',
                          _HANDLE_READ_VERSION_BATTERY, format_bytes(data))
            rawValue = int.from_bytes(data, byteorder='little')
            battery = rawValue * 1.0
        
        return battery

    
    def fill_cache(self):
        """Fill the cache with new data from the sensor."""
        self._cache = dict()
        _LOGGER.info('Filling cache with new sensor data for device %s.', self._mac)
        try:
            with self._bt_interface.connect(self._mac) as connection:

                for handle in HANDLES:
                    data2read = handle[0]
                    data = connection.read_handle(handle[1])
                    _LOGGER.debug('Received result for %s(%x): %s',
                              data2read, handle[1], format_bytes(data))
                    
                    if len(data) <= 2:
                        rawValue = int.from_bytes(data, byteorder='little')
                    elif len(data) == 4:
                        rawValue = unpack('<f',  data )[0]
                    else:
                        rawValue = data
                    _LOGGER.debug('Rawdata for %s: %s', data2read, rawValue)

                    # if data2read == "light":
                    #     if (rawValue == 0):
                    #         value2report = "Not a number"
                    #     else:
                    #         value2report = 642.2 * (0.08640000000000001 * (192773.17000000001 * math.pow(rawValue, -1.0606619)))
                    #     # value2report = (0.08640000000000001 * (192773.17000000001 * math.pow(rawValue, -1.0606619)))
                    if data2read in ["soil_temperature", "air_temperature"]:
                        value2report = 0.00000003044 * math.pow(rawValue, 3.0) - 0.00008038 * math.pow(rawValue, 2.0) + rawValue * 0.1149 - 30.449999999999999
                    elif data2read in ["moisture", "moisture_rj"]:
                        soilMoisture = 11.4293 + (0.0000000010698 * math.pow(rawValue, 4.0) - 0.00000152538 * math.pow(rawValue, 3.0) +  0.000866976 * math.pow(rawValue, 2.0) - 0.169422 * rawValue)
                        value2report = 100.0 * (0.0000045 * math.pow(soilMoisture, 3.0) - 0.00055 * math.pow(soilMoisture, 2.0) + 0.0292 * soilMoisture - 0.053);
                    else:
                        value2report = rawValue

                    if isinstance(value2report, int):
                        value2report = value2report * 1.0
                    elif isinstance(value2report, float):
                        value2report = round(value2report, 1)
                    elif isinstance(value2report, str):
                        value2report = value2report
                    else:
                        value2report = ''.join(chr(n) for n in value2report)


                    _LOGGER.info('Decoded result for %s: %s', data2read, value2report)
                    self._cache[data2read] = value2report
        except:
            self.clear_cache()
            # self._cache = None
            # self._last_read = datetime.now() - self._cache_timeout + timedelta(seconds=300)
            raise


        if self.cache_available():
            self._last_read = datetime.now()
        else:
            # If a sensor doesn't work, wait 5 minutes before retrying
            self._last_read = datetime.now() - self._cache_timeout + timedelta(seconds=300)

    def parameter_values(self, read_cached=True):
        """Return a value of one of the monitored paramaters.

        This method will try to retrieve the data from cache and only
        request it by bluetooth if no cached value is stored or the cache is
        expired.
        This behaviour can be overwritten by the "read_cached" parameter.
        """
        # Special handling for battery attribute

        # Use the lock to make sure the cache isn't updated multiple times
        with self.lock:
            if (read_cached is False) or \
                    (self._last_read is None) or \
                    (datetime.now() - self._cache_timeout > self._last_read):
                self.fill_cache()
            else:
                _LOGGER.debug("Using cache (%s < %s)",
                              datetime.now() - self._last_read,
                              self._cache_timeout)

        if self.cache_available():
            return self._cache
        else:
            raise BluetoothBackendException("Could not read data from Parrot Pot sensor %s" % self._mac)



    def parameter_value(self, parameter, read_cached=True):
        """Return a value of one of the monitored paramaters.

        This method will try to retrieve the data from cache and only
        request it by bluetooth if no cached value is stored or the cache is
        expired.
        This behaviour can be overwritten by the "read_cached" parameter.
        """
        # Special handling for battery attribute
        # if parameter == MI_BATTERY:
        #     return self.battery_level()

        return self.parameter_values(read_cached)[parameter]


    def clear_cache(self):
        """Manually force the cache to be cleared."""
        self._cache = None
        self._last_read = None

    def cache_available(self):
        """Check if there is data in the cache."""
        return ((self._cache is not None) and (self._cache))
