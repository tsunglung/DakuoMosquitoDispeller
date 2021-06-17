"""Config flow to configure Dakuo Mosquito Dispeller component."""
import logging
from collections import OrderedDict
from typing import Optional

import voluptuous as vol
from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_PUSH,
    ConfigFlow,
    OptionsFlow,
    ConfigEntry
    )
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.network import is_ip_address
from homeassistant.exceptions import PlatformNotReady

from miio import Device, DeviceException
from .const import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Import Dakuo Mosquito Dispeller configuration from YAML."""
    _LOGGER.warning(
        "Loading Dakuo Mosquito Dispeller via platform setup is deprecated; Please remove it from your configuration"
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )

async def validate_input(hass: HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    try:
        miio_device = Device(data[CONF_HOST], data[CONF_TOKEN])
        device_info = miio_device.info()

        if device_info.model:
            model = device_info.model
        _LOGGER.info(
            "%s %s %s detected",
            model,
            device_info.firmware_version,
            device_info.hardware_version,
        )

    except DeviceException:
        raise PlatformNotReady
    # Return info that you want to store in the config entry.
    return {
        "title": f"{DEFAULT_NAME}",
        "mac": f"{device_info.mac_address}",
    }

class MosquitoDispellerFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Dakuo Mosquito Dispeller config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize flow."""
        self._host: Optional[str] = None
        self._token: Optional[str] = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """ get option flow """
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: Optional[ConfigType] = None,
        error: Optional[str] = None
    ):  # pylint: disable=arguments-differ
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._set_user_input(user_input)
            if not is_ip_address(self._host):
                return self.async_abort(reason="connection_error")

            info = await validate_input(self.hass, user_input)
            #prevent setting up the same account twice
            await self.async_set_unique_id(info["mac"])
            self._abort_if_unique_id_configured()
            self._name = info["title"]
            return self._async_get_entry()

        fields = OrderedDict()
        fields[vol.Required(CONF_HOST,
                            default=self._host or vol.UNDEFINED)] = str
        fields[vol.Required(CONF_TOKEN,
                            default=self._token or vol.UNDEFINED)] = str

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(fields),
            errors={'base': error} if error else None
        )

    @property
    def _name(self):
        # pylint: disable=no-member
        # https://github.com/PyCQA/pylint/issues/3167
        return self.context.get(CONF_NAME)

    @_name.setter
    def _name(self, value):
        # pylint: disable=no-member
        # https://github.com/PyCQA/pylint/issues/3167
        self.context[CONF_NAME] = value
        self.context["title_placeholders"] = {"name": self._name}

    def _set_user_input(self, user_input):
        if user_input is None:
            return
        self._host = user_input.get(CONF_HOST, "")
        self._token = user_input.get(CONF_TOKEN, "")


    @callback
    def _async_get_entry(self):
        return self.async_create_entry(
            title=self._name,
            data={
                CONF_HOST: self._host,
                CONF_TOKEN: self._token,
                CONF_NAME: self._name
            },
        )


class OptionsFlowHandler(OptionsFlow):
    # pylint: disable=too-few-public-methods
    """Handle options flow changes."""
    _host = None
    _token = None

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            if not is_ip_address(user_input.get(CONF_HOST)):
                return self.async_abort(reason="connection_error")
            self._host = user_input.get(CONF_HOST)
            if len(user_input.get(CONF_TOKEN, "")) >= 1:
                self._token = user_input.get(CONF_TOKEN)
            return self.async_create_entry(
                title='',
                data={
                    CONF_HOST: self._host,
                    CONF_TOKEN: self._token,
                },
            )
        self._host = self.config_entry.options.get(CONF_HOST, '')
        self._token = self.config_entry.options.get(CONF_TOKEN, '')

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self._host): str,
                    vol.Required(CONF_TOKEN, default=self._token): str,
                }
            ),
        )
