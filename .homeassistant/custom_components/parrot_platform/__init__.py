"""The miflora component."""
"""Support for monitoring plants."""
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.plant import PLANT_SCHEMA, Plant
from homeassistant.const import CONF_MAC, CONF_FRIENDLY_NAME, CONF_NAME
from . import sensor

DOMAIN = "parrot_platform"
_LOGGER = logging.getLogger(__name__)

PLANT_SCHEMA = PLANT_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
}).extend(sensor.SENSOR_SCHEMA.schema)

CONFIG_SCHEMA = vol.Schema(
  {
    DOMAIN: vol.All(cv.ensure_list, [PLANT_SCHEMA])
  },
  extra=vol.ALLOW_EXTRA
)



async def async_setup(hass, config):
    """Set up the Plant component.""" 
    for plant_config in config[DOMAIN]:

        mac = plant_config[CONF_MAC]
        plant_config[CONF_NAME] = DOMAIN + '_' + mac[-5:][:2].lower() + mac[-2:].lower()  # used for sensors prefix
        plant_config[CONF_FRIENDLY_NAME] = 'ParrotPot ' + mac[-5:][:2] + mac[-2:] # used for plant name

        hass.helpers.discovery.load_platform('plant', DOMAIN, plant_config, config)

        hass.helpers.discovery.load_platform('sensor', DOMAIN, plant_config, config)

    return True
