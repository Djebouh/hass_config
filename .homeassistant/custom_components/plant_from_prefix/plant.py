"""Support for monitoring plants."""
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.plant import PLATFORM_SCHEMA, PLANT_SCHEMA
from homeassistant.components.plant import Plant
from homeassistant.const import CONF_PREFIX

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PREFIX): cv.string,
}).extend(PLANT_SCHEMA.schema)


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the Plant component."""

    prefix = config[CONF_PREFIX]
    plant_name = prefix
    _LOGGER.info("Adding plant %s from sensors starting with %s", plant_name, prefix)

    entity = Plant(plant_name, config)
    for reading in Plant.READINGS:
        entity_id = 'sensor.' + prefix + '_' + reading
        entity._sensormap[entity_id] = reading
        entity._readingmap[reading] = entity_id
    
    _LOGGER.debug("Added plant %s", plant_name)

    async_add_entities([entity])
    return True


