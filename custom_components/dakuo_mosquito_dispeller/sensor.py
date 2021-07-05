""" Dakuo Mosquito Dispeller Sensor integration."""
import logging
from functools import partial

from miio import Device, DeviceException
from homeassistant.const import (
    CONF_HOST,
    CONF_TOKEN,
    PERCENTAGE
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.exceptions import PlatformNotReady
from .const import (
    ATTR_MODEL,
    DOMAIN,
    MANUFACTURER,
    MOSQUITO_DISPELLER_DATA
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Mosquito Dispeller Sensor from a config entry."""

    if MOSQUITO_DISPELLER_DATA not in hass.data:
        hass.data[MOSQUITO_DISPELLER_DATA] = {}

    if config_entry.data.get(CONF_HOST, None):
        host = config_entry.data[CONF_HOST]
        token = config_entry.data[CONF_TOKEN]
    else:
        host = config_entry.options[CONF_HOST]
        token = config_entry.options[CONF_TOKEN]

    name = config_entry.title

    _LOGGER.debug("Initializing with host %s (token %s...)", host, token[:5])
    unique_id = None

    try:
        miio_device = Device(host, token)
        device_info = miio_device.info()
        if device_info.model:
            model = device_info.model
        miio_uid = device_info.raw['uid']
        unique_id = "sensor-{}".format(device_info.mac_address)
    except DeviceException as ex:
        raise PlatformNotReady

    device = MosquitoDispellerSensor(
        "{} Liquid Left ".format(
            name[:-5]), miio_device, model, unique_id, miio_uid)
    hass.data[MOSQUITO_DISPELLER_DATA][host] = device
    async_add_entities([device], update_before_add=True)


class MosquitoDispellerSensor(SensorEntity):
    """Representation of a Mosquito Dispeller Sensor."""

    def __init__(self, name, device, model, unique_id, miio_uid):
        """Initialize the Mosquito Dispeller Sensor."""
        super().__init__()
        self._model = model
        self._unique_id = unique_id
        self._device = device
        self._name = name
        self._skip_update = False
        self._did = miio_uid
        self._available = False
        self._state = None
        self._state_attrs = {ATTR_MODEL: self._model}
        self._device_info = device.info()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        usage = self._state
        return usage

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return PERCENTAGE

    @property
    def device_class(self):
        """The type of sensor"""
        return None

    @property
    def unique_id(self):
        """Unique ID for the sensor"""
        return self._unique_id

    @property
    def device_info(self):
        """Return the device_info of the device.
        https://developers.home-assistant.io/docs/device_registry_index/
        """
        return {
            "name": self._name,
            "model": self._model,
            "sw_version": self._device_info.firmware_version,
            "manufacturer": MANUFACTURER,
            "identifiers": {(DOMAIN, self._did)}
        }

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a vacuum command handling error messages."""
        try:
            await self.hass.async_add_executor_job(partial(
                func, *args, **kwargs))
            return True
        except DeviceException as ex:
            _LOGGER.error(mask_error, ex)
            return False

    async def async_update(self):
        """Fetch state from the device."""

        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            if self._did is None:
                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 3, "siid": 1, "did": str(self._did)}]
                )
                if status[0]['code'] == 0:
                    self._did = status[0]['value']
                else:
                    self._did = self._unique_id

            status = await self.hass.async_add_job(
                self._device.raw_command,
                "get_properties",
                [{"piid": 1, "siid": 5, "did": str(self._did)}]
            )
            _LOGGER.info("Got new status: %s", status)

            if status[0]['code'] == 0:
                self._state = status[0]['value']
                self._available = True
            else:
                self._available = False

        except DeviceException as ex:
            self._available = False
            _LOGGER.error(
                "Got exception while fetching the state: %s",
                ex
            )
