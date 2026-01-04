# 🌬️ Smart Ventilatie Rooster

Dit project maakt van een standaard ventilatierooster een slim apparaat met behulp van een ESP8266 en een servo motor.

## 🚀 Snelle Installatie

Je kunt de firmware direct op je ESP8266 flashen via de browser. Klik op de knop hieronder:

[<img src="[https://img.shields.io/badge/ESPHome-Install-orange?style=for-the-badge&logo=esphome]" alt="Installatie Badge">](https://web.esphome.io/?dashboard_import=github://soesjie78/esphome-vent-control/ventcontrol.yaml@main)

*Let op: Gebruik een browser die WebSerial ondersteunt (Chrome, Edge of Opera).*

## ✨ Functies
- **WiFi Setup:** Configureer WiFi via USB (Improv) of via de mobiele hotspot (Captive Portal).
- **Home Assistant:** Automatische ontdekking en eenvoudige toevoeging aan ruimtes.
- **Servo Limiet:** Stel een maximale uitslag in (bijv. 80%) om je mechanisme te beschermen.
- **Richting aanpasbaar:** Softwarematig om te draaien voor links/rechts montage.

## 🛠 Hardware nodig
- ESP8266 (bijv. Wemos D1 Mini)
- Micro Servo motor (180 graden)
- 18650 Batterij + Batterijschild (behorende bij de gebruikte ESP8266)
- (Optioneel) 6V, 1 of 2W Zonnepaneel
- Op Makerworld komen binnenkort de 3D print files te staan waarna ik hier een linkje zal plaatsen.

## ⚙️ Configuratie na installatie
Zodra de module in Home Assistant staat, kun je de volgende zaken instellen:
1. **Module Oriëntatie:** Kies of de servo links of rechts gemonteerd is.
2. **Maximale Uitslag:** Voorkom dat de servo het rooster kapot trekt door een limiet in te stellen.
