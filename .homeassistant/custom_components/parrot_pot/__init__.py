""""
The Parrot POT component.
Support for smart flowerpots.
Instantiate Plant and Sensors.
"""
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.plant import PLANT_SCHEMA, SCHEMA_SENSORS, Plant
from homeassistant.const import CONF_SENSORS, CONF_MAC, CONF_NAME
from . import sensor

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent

from homeassistant.util import slugify

DOMAIN = "parrot_pot"
_LOGGER = logging.getLogger(__name__)


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
            # generate Plant Name
            plant_name = 'Parrot POT ' + mac[-5:][:2] + mac[-2:]
            device_config[CONF_NAME] = plant_name

        # generate sensor names, to reference them in the plant
        device_config[CONF_SENSORS] = {} 
        for key, sensor_type in sensor.SENSOR_TYPES.items():
            # loop on conditions handled by the device
            parameter = sensor_type[0].lower()
            if(Plant.READINGS.get(parameter)):
                # this parameter is supported by the plant platform, register this sensor in the plant
                device_config[CONF_SENSORS][parameter] = f"sensor.{slugify(plant_name)}_{parameter}".lower()

        _LOGGER.info("Adding sensors for plant %s", plant_name)
        await hass.helpers.discovery.async_load_platform('sensor', DOMAIN, device_config, config)

        _LOGGER.debug('Config for plant %s is %s .', plant_name, device_config)
        plants.append(Plant(plant_name, device_config))

    if (plants):
        _LOGGER.info("Adding plants for Parrot POTs")
        await EntityComponent(_LOGGER, 'plant', hass).async_add_entities(plants)


    return True
