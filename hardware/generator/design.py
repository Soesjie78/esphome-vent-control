"""Single source of truth for the Vent Control PCB: parts and nets.

Both the schematic (gen_sch.py) and the PCB (gen_pcb.py) are generated from
this file, so they can never disagree.

Unit for schematic positions: grid units of 2.54 mm (100 mil).
"""

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
LED0603 = "LED_SMD:LED_0603_1608Metric"
SOD123 = "Diode_SMD:D_SOD-123"
SOT23 = "Package_TO_SOT_SMD:SOT-23"

# ref: (lib_id, value, footprint, MPN, LCSC, (sch_x, sch_y) in grid units, assembly)
# assembly: "smt" = placed by JLCPCB, "tht" = soldered by hand, "none" = not a part
PARTS = {
    # --- USB-C input + ESD ------------------------------------------------
    "J1": ("Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
           "HRO TYPE-C-31-M-12", "C165948", (14, 24), "smt"),
    "R1": ("Device:R", "5.1k", R0603, "0603WAF5101T5E", "C23186", (30, 34), "smt"),
    "R2": ("Device:R", "5.1k", R0603, "0603WAF5101T5E", "C23186", (34, 34), "smt"),
    "U4": ("Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
           "USBLC6-2SC6", "C7519", (46, 26), "smt"),
    "D1": ("Device:D_Schottky", "B5819W", SOD123, "B5819W", "C8598", (36, 12), "smt"),

    # --- Solar input + charger ------------------------------------------
    "J3": ("Connector_Generic:Conn_01x02", "Solar 5-6V", "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
           "JST S2B-PH-K-S", "", (62, 8), "tht"),
    "D2": ("Device:D_Schottky", "B5819W", SOD123, "B5819W", "C8598", (72, 12), "smt"),
    "U2": ("vent-control:TP4056", "TP4056", "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm",
           "TP4056-42-ESOP8", "C16581", (92, 22), "smt"),
    "C1": ("Device:C", "10uF", C0805, "CL21A106KAYNNNE", "C15850", (80, 22), "smt"),
    "R3": ("Device:R", "2.4k", R0603, "0603WAF2401T5E", "", (84, 32), "smt"),
    "R4": ("Device:R", "1k", R0603, "0603WAF1001T5E", "C21190", (104, 8), "smt"),
    "D3": ("Device:LED", "red CHRG", LED0603, "KT-0603R", "C2286", (110, 12), "smt"),
    "R5": ("Device:R", "1k", R0603, "0603WAF1001T5E", "C21190", (116, 8), "smt"),
    "D4": ("Device:LED", "green FULL", LED0603, "19-217/GHC-YR1S2/3T", "C72043", (122, 14), "smt"),
    "C2": ("Device:C", "10uF", C0805, "CL21A106KAYNNNE", "C15850", (108, 30), "smt"),
    "J2": ("Connector_Generic:Conn_01x02", "LiPo 1S", "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
           "JST S2B-PH-K-S", "", (122, 30), "tht"),

    # --- 3.3 V regulator + battery measurement ------------------------
    "U3": ("Regulator_Linear:XC6220B331MR", "XC6220B331MR", "Package_TO_SOT_SMD:SOT-23-5",
           "XC6220B331MR-G", "", (144, 14), "smt"),
    "C3": ("Device:C", "10uF", C0805, "CL21A106KAYNNNE", "C15850", (134, 16), "smt"),
    "C4": ("Device:C", "10uF", C0805, "CL21A106KAYNNNE", "C15850", (154, 16), "smt"),
    "R6": ("Device:R", "1M", R0603, "0603WAF1004T5E", "C22935", (140, 30), "smt"),
    "R7": ("Device:R", "1M", R0603, "0603WAF1004T5E", "C22935", (140, 38), "smt"),
    "C8": ("Device:C", "100nF", C0603, "CL10B104KB8NNNC", "C14663", (146, 38), "smt"),

    # --- ESP32-C6 module -------------------------------------------------
    "U1": ("vent-control:ESP32-C6-MINI-1", "ESP32-C6-MINI-1-N4", "vent-control:ESP32-C6-MINI-1",
           "ESP32-C6-MINI-1-N4", "", (48, 72), "smt"),
    "C5": ("Device:C", "22uF", C0805, "CL21A226MAQNNNE", "C45783", (14, 60), "smt"),
    "C6": ("Device:C", "100nF", C0603, "CL10B104KB8NNNC", "C14663", (20, 60), "smt"),
    "R8": ("Device:R", "10k", R0603, "0603WAF1002T5E", "C25804", (14, 76), "smt"),
    "C7": ("Device:C", "1uF", C0603, "CL10A105KB8NNNC", "C15849", (20, 86), "smt"),
    "SW1": ("Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
            "TS-1187A-B-A-B", "C318884", (14, 90), "smt"),
    "R9": ("Device:R", "10k", R0603, "0603WAF1002T5E", "C25804", (82, 60), "smt"),
    "R10": ("Device:R", "10k", R0603, "0603WAF1002T5E", "C25804", (88, 60), "smt"),
    "SW2": ("Switch:SW_Push", "BOOT", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
            "TS-1187A-B-A-B", "C318884", (82, 76), "smt"),
    "R11": ("Device:R", "1k", R0603, "0603WAF1001T5E", "C21190", (94, 70), "smt"),
    "D5": ("Device:LED", "green STATUS", LED0603, "19-217/GHC-YR1S2/3T", "C72043", (94, 78), "smt"),

    # --- Servo power switch ---------------------------------------------
    "Q1": ("Transistor_FET:AO3401A", "AO3401A", SOT23, "AO3401A", "C15127", (140, 62), "smt"),
    "R12": ("Device:R", "100k", R0603, "0603WAF1003T5E", "C25803", (128, 58), "smt"),
    "C9": ("Device:C", "100nF", C0603, "CL10B104KB8NNNC", "C14663", (122, 58), "smt"),
    "R13": ("Device:R", "10k", R0603, "0603WAF1002T5E", "C25804", (128, 72), "smt"),
    "Q2": ("Transistor_FET:2N7002", "2N7002", SOT23, "2N7002", "C8545", (126, 82), "smt"),
    "R14": ("Device:R", "10k", R0603, "0603WAF1002T5E", "C25804", (118, 88), "smt"),
    "C10": ("Device:C", "47uF", C1206, "CL31A476MQHNNNE", "", (148, 72), "smt"),
    "C11": ("Device:C", "100nF", C0603, "CL10B104KB8NNNC", "C14663", (154, 72), "smt"),
    "R15": ("Device:R", "1k", R0603, "0603WAF1001T5E", "C21190", (150, 86), "smt"),
    "J4": ("Connector_Generic:Conn_01x03", "Servo", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
           "2.54mm pin header 1x3", "", (162, 80), "tht"),

    # --- Mechanical ---------------------------------------------------------
    "H1": ("Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "", (130, 100), "none"),
    "H2": ("Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "", (136, 100), "none"),
    "H3": ("Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "", (142, 100), "none"),
    "H4": ("Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "", (148, 100), "none"),
}

# PWR_FLAGs (schematic only) - net names they sit on, with positions
PWR_FLAGS = {"#FLG01": ("GND", (40, 92)), "#FLG02": ("VCHG", (86, 6)), "#FLG03": ("VBUS", (28, 6))}

NETS = {
    "GND": ["J1.A1", "J1.A12", "J1.B1", "J1.B12", "J1.S1", "R1.2", "R2.2", "U4.2",
            "J3.2", "U2.3", "U2.9", "U2.1", "R3.2", "C1.2", "C2.2", "J2.2",
            "U3.2", "C3.2", "C4.2", "R7.2", "C8.2",
            "U1.1", "C5.2", "C6.2", "C7.2", "SW1.2", "SW2.2", "D5.1",
            "Q2.2", "R14.2", "C10.2", "C11.2", "J4.1"],
    "VBUS": ["J1.A4", "J1.A9", "J1.B4", "J1.B9", "U4.5", "D1.2"],
    "CC1": ["J1.A5", "R1.1"],
    "CC2": ["J1.B5", "R2.1"],
    "USB_DP": ["J1.A6", "J1.B6", "U4.1", "U4.6", "U1.18"],
    "USB_DN": ["J1.A7", "J1.B7", "U4.3", "U4.4", "U1.17"],
    "VSOLAR": ["J3.1", "D2.2"],
    "VCHG": ["D1.1", "D2.1", "U2.4", "U2.8", "C1.1", "R4.1", "R5.1"],
    "PROG": ["U2.2", "R3.1"],
    "LED_CHRG": ["R4.2", "D3.2"],
    "CHRG": ["D3.1", "U2.7"],
    "LED_STDBY": ["R5.2", "D4.2"],
    "STDBY": ["D4.1", "U2.6"],
    "VBAT": ["U2.5", "C2.1", "J2.1", "U3.1", "U3.3", "C3.1", "R6.1",
             "Q1.2", "R12.1", "C9.1"],
    "+3V3": ["U3.5", "C4.1", "U1.3", "C5.1", "C6.1", "R8.1", "R9.1", "R10.1"],
    "VBAT_ADC": ["R6.2", "R7.1", "C8.1", "U1.12"],
    "EN": ["U1.8", "R8.2", "C7.1", "SW1.1"],
    "BOOT": ["U1.23", "R9.2", "SW2.1"],
    "IO8": ["U1.22", "R10.2"],
    "LED_IO18": ["U1.24", "R11.1"],
    "LED_K": ["R11.2", "D5.2"],
    "SERVO_EN": ["U1.5", "Q2.1", "R14.1"],
    "SERVO_GDRV": ["Q2.3", "R13.1"],
    "SERVO_G": ["R13.2", "Q1.1", "R12.2", "C9.2"],
    "SERVO_V": ["Q1.3", "C10.1", "C11.1", "J4.2"],
    "SERVO_PWM": ["U1.13", "R15.1"],
    "SERVO_SIG": ["R15.2", "J4.3"],
}

# Pins deliberately left unconnected (get a no-connect flag in the schematic)
NO_CONNECT = ["J1.A8", "J1.B8"] + [f"U1.{p}" for p in (6, 9, 10, 15, 16, 19, 20, 25, 26, 27, 28, 29, 30, 31)]

# Net classes for the PCB
POWER_NETS = ["GND", "VBUS", "VSOLAR", "VCHG", "VBAT", "+3V3", "SERVO_V"]

TITLE = "Vent Control - ESP32-C6 solar servo controller"
REV = "1.0"

# All ground pads of the ESP32-C6-MINI-1 (stacked in the symbol, see gen_lib.py)
NETS["GND"] += [f"U1.{p}" for p in [2, 11, 14] + list(range(36, 54))]


def check():
    seen = {}
    for net, pins in NETS.items():
        assert len(pins) >= 2, net
        for p in pins:
            ref = p.split(".")[0]
            assert ref in PARTS, p
            assert p not in seen, f"{p} in {net} and {seen[p]}"
            seen[p] = net
    for p in NO_CONNECT:
        assert p not in seen, p
    return seen


PIN_NET = check()
