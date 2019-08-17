"""Support for monitoring plants."""
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.plant import PLATFORM_SCHEMA, PLANT_SCHEMA
from homeassistant.components.plant import Plant
from homeassistant.const import CONF_MAC, CONF_NAME
from . import sensor

_LOGGER = logging.getLogger(__name__)

DOMAIN = "plant_parrot"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
}).extend(PLANT_SCHEMA.schema).extend(sensor.SENSOR_SCHEMA.schema)


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):

    mac = config[CONF_MAC]
    plant_name = 'ParrotPot ' + mac[-5:][:2] + mac[-2:]
    sensor_prefix = DOMAIN + '_' + mac[-5:][:2].lower() + mac[-2:].lower()
    config[CONF_NAME] = sensor_prefix

    _LOGGER.info("Adding sensors for plant %s (mac address: %s)", plant_name, mac)
    hass.helpers.discovery.load_platform('sensor', DOMAIN, config, config)

    _LOGGER.info("Adding plant %s (mac address %s)", plant_name, mac)
    entity = Plant(plant_name, config)
    for reading in Plant.READINGS:
        entity_id = 'sensor.' + sensor_prefix + '_' + reading
        entity._sensormap[entity_id] = reading
        entity._readingmap[reading] = entity_id

    async_add_entities([entity])
    _LOGGER.debug("Added plant %s", plant_name)
    return True


