"""Support for monitoring plants."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.plant import PLATFORM_SCHEMA, PLANT_SCHEMA
from homeassistant.components.plant import (
    READING_BATTERY,
    READING_TEMPERATURE,
    READING_MOISTURE,
    READING_CONDUCTIVITY,
    READING_BRIGHTNESS,
)
from homeassistant.components.plant import Plant

from homeassistant.const import (CONF_SENSORS, CONF_NAME)

_LOGGER = logging.getLogger(__name__)

CONF_SENSOR_BATTERY_LEVEL = READING_BATTERY
CONF_SENSOR_MOISTURE = READING_MOISTURE
CONF_SENSOR_CONDUCTIVITY = READING_CONDUCTIVITY
CONF_SENSOR_TEMPERATURE = READING_TEMPERATURE
CONF_SENSOR_BRIGHTNESS = READING_BRIGHTNESS


SCHEMA_SENSORS = vol.Schema({
    vol.Optional(CONF_SENSOR_BATTERY_LEVEL): cv.entity_id,
    vol.Optional(CONF_SENSOR_MOISTURE): cv.entity_id,
    vol.Optional(CONF_SENSOR_CONDUCTIVITY): cv.entity_id,
    vol.Optional(CONF_SENSOR_TEMPERATURE): cv.entity_id,
    vol.Optional(CONF_SENSOR_BRIGHTNESS): cv.entity_id,
})

# PLANT_SCHEMA = vol.Schema({
#     vol.Required(CONF_SENSORS): vol.Schema(SCHEMA_SENSORS),
# }).extend(PLANT_SCHEMA.schema)


# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
#     cv.string: PLANT_SCHEMA
# })

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SENSORS): vol.Schema(SCHEMA_SENSORS),
    vol.Required(CONF_NAME): cv.string,
}).extend(PLANT_SCHEMA.schema)


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the Plant component."""

    plant_name = config[CONF_NAME]
    _LOGGER.info("Adding plant %s", plant_name)

    entity = Plant(plant_name, config)
    for reading, entity_id in config[CONF_SENSORS].items():
        _LOGGER.debug("Associate sensor %s to plant %s", reading, plant_name)
        entity._sensormap[entity_id] = reading
        entity._readingmap[reading] = entity_id
    
    _LOGGER.debug("Added plant %s", plant_name)

    async_add_entities([entity])
    return True


