""" Support for Dakuo Mosquito Dispeller."""
import logging
from functools import partial

from miio import Device, DeviceException
from homeassistant.const import (
    CONF_HOST,
    CONF_TOKEN,
    ATTR_MODE
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.components.fan import (
    FanEntity,
    SUPPORT_PRESET_MODE,
    SPEED_OFF
)

from .const import (
    ATTR_FW_VER,
    ATTR_HW_VER,
    ATTR_LIQUID_LEFT,
    ATTR_MODEL,
    ATTR_PRESET_MODE,
    DOMAIN,
    FAN_SPEED_LEVEL1,
    FAN_SPEED_LEVEL2,
    MOSQUITO_DISPELLER_DATA,
    MANUFACTURER
)

_LOGGER = logging.getLogger(__name__)

AVAILABLE_ATTRIBUTES_FAN = {
    ATTR_MODE: "mode"
}

SUCCESS = ["ok"]

FAN_PRESET_MODES = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 0,
    FAN_SPEED_LEVEL2: 1,
}


async def async_setup_entry(hass,
                            config_entry,
                            async_add_entities,
                            discovery_info=None):
    # pylint: disable=unused-argument, too-many-locals
    """Set up the  Mosquito Dispeller Fan device from config."""

    if MOSQUITO_DISPELLER_DATA not in hass.data:
        hass.data[MOSQUITO_DISPELLER_DATA] = {}

    if config_entry.data.get(CONF_HOST, None):
        host = config_entry.data[CONF_HOST]
        token = config_entry.data[CONF_TOKEN]
    else:
        host = config_entry.options[CONF_HOST]
        token = config_entry.options[CONF_TOKEN]

    name = config_entry.title

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])
    unique_id = None

    try:
        miio_device = Device(host, token)
        device_info = miio_device.info()
        if device_info.model:
            model = device_info.model
        miio_uid = device_info.raw['uid']
        unique_id = "fan-{}".format(device_info.mac_address)
    except DeviceException:
        raise PlatformNotReady

    device = MosquitoDispellerFan(
        "{} Switch ".format(
            name[:-5]), miio_device, model, unique_id, miio_uid)
    hass.data[MOSQUITO_DISPELLER_DATA][host] = device
    async_add_entities([device], update_before_add=True)


class MosquitoDispellerFan(FanEntity):
    # pylint: disable=too-many-instance-attributes
    """Representation of a Mosquito Dispeller Fan."""

    def __init__(self, name, device, model, unique_id, miio_uid):
        """Initialize the Mosquito Dispeller Fan."""
        super().__init__()
        self._model = model
        self._unique_id = unique_id
        self._device = device
        self._name = name
        self._skip_update = False
        self._did = miio_uid
        self._available = False
        self._state = None
        self._preset_mode = None
        self._preset_modes = list(FAN_PRESET_MODES)
        self._preset_mode_attr = None
        self._liquid_left = 0
        self._device_info = device.info()

        self._state_attrs = {
            ATTR_MODEL: self._model,
            ATTR_FW_VER: self._device_info.firmware_version,
            ATTR_HW_VER: self._device_info.hardware_version
            }

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return (
            SUPPORT_PRESET_MODE
        )

    @property
    def should_poll(self):
        """Poll the device."""
        return True

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        attrs = {
            ATTR_PRESET_MODE: self._preset_mode_attr,
            ATTR_LIQUID_LEFT: self._liquid_left
        }
        self._state_attrs.update(attrs)
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def preset_mode(self):
        """Get the current preset mode."""
        if self._state:
            return self._preset_mode

        return None

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
        """Call a miio device command handling error messages."""

        try:
            result = await self.hass.async_add_job(partial(
                func, *args, **kwargs))

            _LOGGER.debug("Response received from miio device: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            self._available = False
            return False

    async def async_turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn the device on."""
        result = await self._try_command(
            "Turning the miio device on failed.",
            self._device.send,
            "set_properties",
            [{"piid": 1, "siid": 6, "did": str(self._did), "value": 1}]
        )

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        result = await self._try_command(
            "Turning the miio device off failed.",
            self._device.send,
            "set_properties",
            [{"piid": 1, "siid": 6, "did": str(self._did), "value": 0}]
        )

        if result:
            self._state = False
            self._skip_update = True

    @property
    def preset_modes(self):
        """Get the list of available preset modes."""
        return self._preset_modes

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""

        if preset_mode == SPEED_OFF:
            await self.async_turn_off()
            return

        if preset_mode == FAN_SPEED_LEVEL1:
            value = 0
        else:
            value = 1
        await self._try_command(
            "Setting fan speed of the miio device failed.",
            self._device.send,
            "set_properties",
            [{"piid": 2, "siid": 6, "did": str(self._did), "value": value}])

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
                [{"piid": 1, "siid": 6, "did": str(self._did)}]
            )

            if status[0]['code'] == 0:
                self._state = status[0]['value']
                self._available = True
            else:
                self._available = False

            status = await self.hass.async_add_job(
                self._device.raw_command,
                "get_properties",
                [{"piid": 2, "siid": 6, "did": str(self._did)}]
            )

            if status[0]['code'] == 0:
                self._preset_mode = status[0]['value']
                if self._preset_mode == 0:
                    self._preset_mode_attr = FAN_SPEED_LEVEL1
                else:
                    self._preset_mode_attr = FAN_SPEED_LEVEL2
                self._available = True
            else:
                self._available = False

            status = await self.hass.async_add_job(
                self._device.raw_command,
                "get_properties",
                [{"piid": 1, "siid": 5, "did": str(self._did)}]
            )

            if status[0]['code'] == 0:
                self._liquid_left = status[0]['value']
                self._available = True
            else:
                self._available = False

        except DeviceException as ex:
            self._available = False
            _LOGGER.error(
                "Got exception while fetching the state: %s",
                ex
            )
