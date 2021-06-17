# Dakuo Mosquito Dispeller Home Assistant Integration

Controll Dakuo Mosquito Dispeller via Miot

## Installation with HACS

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

The simplest way to install this integration is with the Home Assistant Community Store (HACS). This is not (yet) part of the default store and will need to be added as a custom repository.

Setting up a custom repository is done by:

1. Go into HACS from the side bar.
2. Click into Integrations.
3. Click the 3 dots menu in the top right and select `Custom repositories`
4. In the UI that opens, copy and paste the [url for this github repo](https://github.com/tsunglung/DakuoMosquitoDispeller) into the `Add custom repository URL` field.
5. Set the category to `Integration`.
6. Click the `Add` button. Further configuration is done within the Integrations configuration in Home Assistant. You may need to restart home assistant.
## Manual Installation

If you don't want to use HACS or just prefer manual installs, you can install this like any other custom component. Just copy the `dakuo_mosquito_dispeller` folder to `custom_components` folder in your Home Assistant config folder.

## Configuration

Configuration is done directly in the Home Assistant UI, no manual config file editing is required.

1. Go into the Home Assistant `Configuration`
2. Select `Integrations`
3. Click the `+` button at the bottom
4. Search for "Dakuo Mosquito Dispeller" and add it. If you do not see it in the list, ensure that you have installed the integration.
   1. If the integration didn't show up in the list please REFRESH the page
   2. If the integration is still not in the list, you need to clear the browser cache.
5. In the UI that opens, enter the host and token. You need [get the token](https://github.com/piotrmachowski/xiaomi-cloud-tokens-extractor).
6. Done!.

Buy Me A Coffee

|  LINE Pay | LINE Bank | JKao Pay |
| :------------: | :------------: | :------------: |
| <img src="https://github.com/tsunglung/OpenCWB/blob/master/linepay.jpg" alt="Line Pay" height="200" width="200">  | <img src="https://github.com/tsunglung/OpenCWB/blob/master/linebank.jpg" alt="Line Bank" height="200" width="200">  | <img src="https://github.com/tsunglung/OpenCWB/blob/master/jkopay.jpg" alt="JKo Pay" height="200" width="200">  |
