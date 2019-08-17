"""Support for monitoring plants."""
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.plant import PLANT_SCHEMA
from homeassistant.components.plant import Plant
from homeassistant.const import CONF_SENSORS, CONF_FRIENDLY_NAME, CONF_NAME
from . import sensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the Plant component."""
    if (discovery_info is not None):
        plant_config = discovery_info

    plant_name = plant_config[CONF_FRIENDLY_NAME]
    sensor_prefix = plant_config[CONF_NAME]

    # plant_config[CONF_SENSORS] = {}
    # for reading in Plant.READINGS:
    #     plant_config[CONF_SENSORS][reading] = 'sensor.' + sensor_prefix + '_' + reading

    _LOGGER.info("Adding plant %s", plant_name)
    entity = Plant(plant_name, plant_config)
    for reading in Plant.READINGS:
        entity_id = 'sensor.' + sensor_prefix + '_' + reading
        entity._sensormap[entity_id] = reading
        entity._readingmap[reading] = entity_id

    async_add_entities([entity])
    _LOGGER.debug("Added plant %s", plant_name)
    return True


