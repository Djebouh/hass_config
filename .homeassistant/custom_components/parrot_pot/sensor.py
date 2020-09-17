""""
Support for Parrot POT BLE plant sensor.
Inspired from Mi Flora integration: https://github.com/home-assistant/core/tree/dev/homeassistant/components/miflora
"""

from datetime import timedelta
import logging

import btlewrap
from btlewrap import BluetoothBackendException

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

# from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    CONF_MAC,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    UNIT_PERCENTAGE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    CONDUCTIVITY,
    CONF_SENSORS,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_BATTERY,
    CONF_FORCE_UPDATE,
    EVENT_HOMEASSISTANT_START,
)
from homeassistant.core import callback

import homeassistant.util.dt as dt_util
from homeassistant.util.temperature import celsius_to_fahrenheit

from typing import Optional

from . import parrotpot_poller

try:
    import bluepy.btle  # noqa: F401 pylint: disable=unused-import

    BACKEND = btlewrap.BluepyBackend
except ImportError:
    BACKEND = btlewrap.GatttoolBackend

_LOGGER = logging.getLogger(__name__)

CONF_ADAPTER = 'adapter'
CONF_MEDIAN = 'median'
CONF_GO_UNAVAILABLE_TIMEOUT = "go_unavailable_timeout"

DEFAULT_ADAPTER = 'hci0'
DEFAULT_FORCE_UPDATE = False
DEFAULT_MEDIAN = 3
DEFAULT_GO_UNAVAILABLE_TIMEOUT = timedelta(seconds=7200)

SCAN_INTERVAL = timedelta(seconds=1200)

ATTR_LAST_SUCCESSFUL_UPDATE = "last_successful_update"

# Sensor types are defined like: Name, units, icon, device type (icon or device type are mandatory)
SENSOR_TYPES = {
    'soil_temperature': ['Temperature', TEMP_CELSIUS, 'mdi:thermometer', DEVICE_CLASS_TEMPERATURE],
    'light': ['Brightness', 'mole/m2/day', 'mdi:white-balance-sunny', DEVICE_CLASS_ILLUMINANCE],
    'moisture_cal': ['Moisture', UNIT_PERCENTAGE, 'mdi:water-percent', DEVICE_CLASS_HUMIDITY],
    'watertank_Level': ['Watertank level', UNIT_PERCENTAGE, 'mdi:water-percent', DEVICE_CLASS_HUMIDITY],
    'conductivity': ['Conductivity', CONDUCTIVITY, 'mdi:flash-circle', None],
    'battery': ['Battery', UNIT_PERCENTAGE, 'mdi:battery-charging', DEVICE_CLASS_BATTERY],
}


SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MAC): cv.string,
        # vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        #     vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_MEDIAN, default=DEFAULT_MEDIAN): cv.positive_int,
        vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
        vol.Optional(CONF_ADAPTER, default=DEFAULT_ADAPTER): cv.string,
        vol.Optional(
            CONF_GO_UNAVAILABLE_TIMEOUT, default=DEFAULT_GO_UNAVAILABLE_TIMEOUT
        ): cv.time_period,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the ParrotPot sensor."""
    # from parrotpot import parrotpot_poller

    if (discovery_info is not None):
        sensor_config = discovery_info

    plant_name = sensor_config.get(CONF_NAME)
    _LOGGER.debug('Config for %s is %s .', plant_name, sensor_config)

    backend = BACKEND
    _LOGGER.debug('%s is using %s BLE backend.', plant_name, backend.__name__)

    cache = sensor_config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL).total_seconds()
    poller = parrotpot_poller.ParrotPotPoller(
        mac=sensor_config.get(CONF_MAC),
        cache_timeout=cache,
        adapter=sensor_config.get(CONF_ADAPTER),
        backend=backend)
    force_update = sensor_config.get(CONF_FORCE_UPDATE)
    median = sensor_config.get(CONF_MEDIAN)

    go_unavailable_timeout = sensor_config.get(CONF_GO_UNAVAILABLE_TIMEOUT)

    sensors = []

    for key, sensor_type in SENSOR_TYPES.items():
        parameter = sensor_type[0]
        sensor_name = f"{plant_name} {parameter}"
        unit = (
            hass.config.units.temperature_unit
            if parameter == "Temperature"
            else sensor_type[1]
        )
        icon = sensor_type[2] if(not sensor_type[3]) else None

        _LOGGER.debug('Plant %s, adding sensor %s for key %s', plant_name, parameter, key)
        sensors.append(
            ParrotPotSensor(
                poller,
                key,
                sensor_name,
                unit,
                icon,
                sensor_type[3],
                force_update,
                median,
                go_unavailable_timeout,
            )
        )

    async_add_entities(sensors)


class ParrotPotSensor(Entity):
    """Implementing the ParrotPot sensor."""

    def __init__(
        self,
        poller,
        parameter,
        name,
        unit,
        icon,
        device_class,
        force_update,
        median,
        go_unavailable_timeout,
    ):
        """Initialize the sensor."""
        self.poller = poller
        self.parameter = parameter
        self._unit = unit
        self._icon = icon
        self._device_class = device_class
        self._name = name
        self._state = None
        self.data = []
        self._force_update = force_update
        self.go_unavailable_timeout = go_unavailable_timeout
        self.last_successful_update = dt_util.utc_from_timestamp(0)
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
    def available(self):
        """Return True if did update since 2h."""
        return self.last_successful_update > (
            dt_util.utcnow() - self.go_unavailable_timeout
        )

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {ATTR_LAST_SUCCESSFUL_UPDATE: self.last_successful_update}
        return attr

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    def update(self):
        """
        Update current conditions.

        This uses a rolling median over 3 values to filter out outliers.
        """
        try:
            _LOGGER.debug("Polling data for %s", self.name)
            data = self.poller.parameter_value(self.parameter)
        except (OSError, BluetoothBackendException) as err:
            _LOGGER.info("Polling error %s: %s", type(err).__name__, err)
            return
        # except PollingError:
        #     _LOGGER.warning("Polling error, undefined %s", PollingError)
        #     return

        if data is not None:
            _LOGGER.debug("%s = %s", self.name, data)
            if self._unit == TEMP_FAHRENHEIT:
                data = celsius_to_fahrenheit(data)
            self.data.append(data)
            self.last_successful_update = dt_util.utcnow()
        else:
            _LOGGER.warning("Did not receive any data from Parrot Pot sensor %s", self.name)
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
