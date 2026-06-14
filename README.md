🛠️ Smart Solar-Powered Ventilation Control (Matter / Home Assistant)
Convert your standard home ventilation grill or window register into a smart, energy-independent ventilation system! This 3D-printed project mounts a servo motor to your ventilation control and uses a super energy-efficient ESP32-C6 (FireBeetle 2) to operate automatically via Home Assistant (Matter/Thread or WiFi).

Thanks to advanced deep sleep optimization, this project can run entirely on a small LiPo battery topped up by a tiny solar panel!

## 🚀 Quick Installation

You can flash the firmware directly to your ESP8266 via your browser. Click the button below:

[<img src="https://img.shields.io/badge/ESPHome-Install-orange?style=for-the-badge&logo=esphome" alt="Install Badge">](https://web.esphome.io/?dashboard_import=github://soesjie78/esphome-vent-control/ventcontrol.yaml@main)

*Note: Please use a browser that supports WebSerial (Chrome, Edge, or Opera).*

✨ Features
Smart Home Integration: Works natively with Home Assistant and Matter via ESPHome.
Extreme Battery Life: The controller stays in ultra-low-power Deep Sleep, waking up every 20 minutes to sync and check for new commands. No massive battery needed!
Zero Latency "Queuing": Uses a Home Assistant Helper (input_select). You can change the desired position at any time in your dashboard; the device picks it up instantly the moment it wakes up.
Smart Memory: The servo only moves if the requested position has actually changed, saving tons of mechanical wear and battery power.
Solar Ready: Designed around the DFRobot FireBeetle 2 form factor for easy solar charging integration.


Further information can be foud at the Makerworld 3D model houding area: https://makerworld.com/en/models/2931636-smart-solar-vent-control-matter-home-assistant#profileId-3281956
