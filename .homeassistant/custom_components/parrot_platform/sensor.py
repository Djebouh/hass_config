"""Support for Xiaomi Parrot Pot BLE plant sensor."""
from datetime import timedelta
import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_FORCE_UPDATE,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_START)
from homeassistant.core import callback

from . import parrotpot_poller

_LOGGER = logging.getLogger(__name__)

CONF_ADAPTER = 'adapter'
CONF_MEDIAN = 'median'

DEFAULT_ADAPTER = 'hci0'
DEFAULT_FORCE_UPDATE = False
DEFAULT_MEDIAN = 3
DEFAULT_NAME = 'Parrot Pot'

SCAN_INTERVAL = timedelta(seconds=1800)

# Sensor types are defined like: Name, units, icon
SENSOR_TYPES = {
    'soil_temperature': ['Temperature', '°C', 'mdi:thermometer'],
    'dli_cal': ['Brightness', 'mole/m2/day', 'mdi:white-balance-sunny'],
    'moisture_cal': ['Moisture', '%', 'mdi:water-percent'],
    'watertank_Level': ['Watertank level', '%', 'mdi:water-percent'],
    'conductivity': ['Conductivity', 'µS/cm', 'mdi:flash-circle'],
    'battery': ['Battery', '%', 'mdi:battery-charging'],
}


SENSOR_SCHEMA = vol.Schema({
    vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MEDIAN, default=DEFAULT_MEDIAN): cv.positive_int,
    vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
    vol.Optional(CONF_ADAPTER, default=DEFAULT_ADAPTER): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the ParrotPot sensor."""
    # from parrotpot import parrotpot_poller

    if (discovery_info is not None):
        sensor_config = discovery_info

    prefix = sensor_config.get(CONF_NAME)

    try:
        import bluepy.btle  # noqa: F401 pylint: disable=unused-import
        from btlewrap import BluepyBackend
        backend = BluepyBackend
    except ImportError:
        from btlewrap import GatttoolBackend
        backend = GatttoolBackend
    _LOGGER.debug('ParrotPot %s is using %s backend.', prefix, backend.__name__)

    poller = parrotpot_poller.ParrotPotPoller(
        mac=sensor_config.get(CONF_MAC),
        cache_timeout=sensor_config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL).total_seconds(),
        adapter=sensor_config.get(CONF_ADAPTER),
        backend=backend)
    force_update = sensor_config.get(CONF_FORCE_UPDATE)
    median = sensor_config.get(CONF_MEDIAN)

    devs = []

    for parameter in sensor_config[CONF_MONITORED_CONDITIONS]:
        name = SENSOR_TYPES[parameter][0]
        unit = SENSOR_TYPES[parameter][1]
        icon = SENSOR_TYPES[parameter][2]

        if prefix:
            name = "{} {}".format(prefix, name)

        devs.append(ParrotPotSensor(
            poller, parameter, name, unit, icon, force_update, median))

    async_add_entities(devs)


class ParrotPotSensor(Entity):
    """Implementing the ParrotPot sensor."""

    def __init__(
            self, poller, parameter, name, unit, icon, force_update, median):
        """Initialize the sensor."""
        self.poller = poller
        self.parameter = parameter
        self._unit = unit
        self._icon = icon
        self._name = name
        self._state = None
        self.data = []
        self._force_update = force_update
        # Median is used to filter out outliers. median of 3 will filter
        # single outliers, while  median of 5 will filter double outliers
        # Use median_count = 1 if no filtering is required.
        self.median_count = median

    async def async_added_to_hass(self):
        """Set initial state."""
        @callback
        def on_startup(_):
            self.async_schedule_update_ha_state(True)

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, on_startup)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    def update(self):
        """
        Update current conditions.

        This uses a rolling median over 3 values to filter out outliers.
        """
        from btlewrap import BluetoothBackendException
        try:
            _LOGGER.debug("Polling data for %s", self.name)
            data = self.poller.parameter_value(self.parameter)
        except IOError as ioerr:
            _LOGGER.warning("Polling error (IOError) %s", ioerr)
            return
        except BluetoothBackendException as bterror:
            _LOGGER.warning("Polling error (BTerror) %s", bterror)
            return
        except PollingError:
            _LOGGER.warning("Polling error, undefined %s", PollingError)
            return

        if data is not None:
            _LOGGER.debug("%s = %s", self.name, data)
            self.data.append(data)
        else:
            _LOGGER.warning("Did not receive any data from Parrot Pot sensor %s",
                         self.name)
            # Remove old data from median list or set sensor value to None
            # if no data is available anymore
            if self.data:
                self.data = self.data[1:]
            else:
                self._state = None
            return

        _LOGGER.debug("Data collected: %s", self.data)
        if len(self.data) > self.median_count:
            self.data = self.data[1:]

        if len(self.data) == self.median_count:
            median = sorted(self.data)[int((self.median_count - 1) / 2)]
            _LOGGER.debug("Median is: %s", median)
            self._state = median
        elif self._state is None:
            _LOGGER.debug("Set initial state")
            self._state = self.data[0]
        else:
            _LOGGER.debug("Not yet enough data for median calculation")
