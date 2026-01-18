# 🌬️ Smart Vent Controller

This project transforms a standard ventilation grille into a smart device using an ESP8266 and a servo motor.

## 🚀 Quick Installation

You can flash the firmware directly to your ESP8266 via your browser. Click the button below:

[<img src="https://img.shields.io/badge/ESPHome-Install-orange?style=for-the-badge&logo=esphome" alt="Install Badge">](https://web.esphome.io/?dashboard_import=github://soesjie78/esphome-vent-control/ventcontrol.yaml@main)

*Note: Please use a browser that supports WebSerial (Chrome, Edge, or Opera).*

## ✨ Features
- **WiFi Setup:** Easily configure WiFi via USB (Improv) or via the built-in hotspot (Captive Portal).
- **Home Assistant:** Automatic discovery and seamless integration into your dashboard.
- **Servo Limits:** Set a maximum travel limit (e.g., 80%) to protect your mechanical setup.
- **Customizable Direction:** Software-based orientation toggle for left or right mounting.

## 🛠 Hardware Required
- ESP8266 (e.g., Wemos D1 Mini)
- Micro Servo motor (180 degree)
- 18650 Battery + Battery Shield (compatible with your ESP8266)
- (Optional) 6V, 1W or 2W Solar Panel
- **3D Files:** STL files will be available on Makerworld soon. I will post the link here once they are live.

## ⚙️ Post-Installation Configuration
Once the module is added to Home Assistant, you can configure the following settings:
1. **Module Orientation:** Select whether the servo is mounted on the left or right side.
2. **Maximum Swing/Travel:** Set a limit to prevent the servo from overextending and damaging the vent mechanism.
