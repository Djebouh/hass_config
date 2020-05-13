"""The miflora component."""
"""Support for monitoring plants."""
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.plant import PLANT_SCHEMA, Plant, SCHEMA_SENSORS
from homeassistant.const import CONF_SENSORS, CONF_MAC, CONF_FRIENDLY_NAME, CONF_NAME, CONF_PREFIX
from . import sensor

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent

DOMAIN = "parrot_platform"
_LOGGER = logging.getLogger(__name__)

# DEVICE_SCHEMA = vol.Schema(
#   {
#     vol.Required(CONF_MAC): cv.string,
#   }
# )

DEVICE_SCHEMA = PLANT_SCHEMA.extend({
    vol.Optional(CONF_SENSORS): vol.Schema(SCHEMA_SENSORS),
}).extend(sensor.SENSOR_SCHEMA.schema)


CONFIG_SCHEMA = vol.Schema(
  {
    DOMAIN: vol.All(cv.ensure_list, [DEVICE_SCHEMA])
  },
  extra=vol.ALLOW_EXTRA
)



async def async_setup(hass, config):
    """Set up the Plant component.""" 
    plants = []
    for device_config in config[DOMAIN]:

        mac = device_config[CONF_MAC]
        plant_name = device_config.get(CONF_NAME)
        if(plant_name is None):
            plant_name = 'ParrotPot ' + mac[-5:][:2] + mac[-2:] # used for plant name
            device_config[CONF_NAME] = plant_name
        
        sensor_prefix = DOMAIN + '_' + mac[-5:][:2].lower() + mac[-2:].lower()  # used for sensors prefix
        device_config[CONF_PREFIX] = sensor_prefix

        device_config[CONF_SENSORS] = {} 
        for key, sensor_type in sensor.SENSOR_TYPES.items():
            condition = sensor_type[0].lower()
            if(Plant.READINGS.get(condition)):
                device_config[CONF_SENSORS][condition] = f"sensor.{sensor_prefix}_{condition}".lower()

        _LOGGER.info("Adding sensors sensor.%s_* for plant %s", sensor_prefix, plant_name)
        await hass.helpers.discovery.async_load_platform('sensor', DOMAIN, device_config, config)

        _LOGGER.debug('Config for ParrotPot %s is %s .', plant_name, device_config)
        plants.append(Plant(plant_name, device_config))

    if (plants):
        _LOGGER.info("Adding plants for parrot pots")
        await EntityComponent(_LOGGER, 'plant', hass).async_add_entities(plants)


    return True
