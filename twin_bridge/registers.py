"""
The Modbus register map, as code.

Transcribed from `plc/GVL_Godot.st` in the digital-twin repository, which is the
interface contract between the Godot plant model and the CODESYS soft PLC. That
file is the source of truth; this is a typed mirror of it and will go stale if it
changes — `test_bridge.py` guards the parts that can be checked locally, but a
change on the PLC side has to be brought over by hand.

Topology: the PLC is the Modbus TCP server. Godot connects as a client and writes
the holding registers. S.U.R.E. connects as a *second* client and reads. Modbus
TCP servers accept concurrent clients, so nothing on the twin side has to change
for this to work — which is the point of starting here.

Scaling matters and is easy to get silently wrong: DO, temperature, pH and
ammonia cross the wire multiplied by 100 because Modbus registers are 16-bit
integers. Reading HR0 as 812 and calling it 812 mg/L rather than 8.12 mg/L
produces a number that is wrong by two orders of magnitude and still looks like a
plausible sensor value.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Register:
    address: int
    name: str
    scale: float          # raw value is divided by this
    unit: str
    description: str

    def decode(self, raw: int) -> float:
        return raw / self.scale if self.scale != 1 else raw


# Godot -> PLC. Written by the plant model, read by the controller.
HOLDING = {
    "dissolved_oxygen_mgl": Register(0, "wDoRaw", 100, "mg/L", "SEN0237-A dissolved oxygen"),
    "temperature_c":        Register(1, "wTempRaw", 100, "°C", "DS18B20"),
    "ph":                   Register(2, "wPhRaw", 100, "", "SEN0169-V2"),
    "ammonia_mgl":          Register(3, "wNh3Raw", 100, "mg/L", "ammonia test kit"),
    "tds_ppm":              Register(4, "wTdsRaw", 1, "ppm", "SEN0189"),
    "appetite_index":       Register(5, "wAppetite", 1, "0-100", "camera + YOLO"),
    "stress_index":         Register(6, "wStress", 1, "0-100", "camera + YOLO"),
    "biomass_kg":           Register(7, "wBiomassKg", 1, "kg", "stereo size analysis"),
    "feed_button":          Register(8, "wFeedBtn", 1, "", "HMI feed-now"),
    "auto_feeding":         Register(9, "wAutoCmd", 1, "", "HMI automatic mode"),
}

# PLC -> Godot. The controller's actuation and its operator message.
INPUT = {
    "aerator_pct":     Register(0, "wAeratorPct", 1, "%", "air blower"),
    "heater_on":       Register(1, "wHeaterCmd", 1, "", "heater relay"),
    "feeder_on":       Register(2, "wFeederCmd", 1, "", "MG945 feeder servo"),
    "portion_g":       Register(3, "wPortionG", 1, "g", "computed portion"),
    "exchange_on":     Register(4, "wExchangeCmd", 1, "", "water exchange pump"),
    "alarm_flags":     Register(5, "wAlarmFlags", 1, "", "bitfield, see ALARM_BITS"),
    "advice_code":     Register(6, "wAdviceCode", 1, "", "operator message 0-6"),
    "feed_today_g":    Register(7, "wFeedTodayG", 1, "g", "dispensed today"),
}

ALARM_BITS = {
    0: "dissolved oxygen low",
    1: "ammonia high",
    2: "temperature out of band",
    3: "stress high",
}

# The PLC's own operator messages, from PLC_PRG.st. Kept here so S.U.R.E. can say
# what the controller decided alongside what it decided itself — the comparison
# is the reason for connecting at all.
ADVICE_CODES = {
    0: "normal",
    1: "oksijen düşüyor ve stres var — havalandırma artırıldı",
    2: "amonyak yüksek — su değişimi çalışıyor",
    3: "iştah düşük — porsiyon azaltıldı veya atlandı",
    4: "yemleme yapılıyor",
    5: "sıcaklık alarmı",
    6: "yemleme ertelendi — su kalitesi uygun değil",
}

HOLDING_COUNT = 10
INPUT_COUNT = 8


def decode_alarms(flags: int) -> list[str]:
    return [text for bit, text in ALARM_BITS.items() if flags & (1 << bit)]


def decode_holding(raw: list[int]) -> dict:
    """Raw holding registers to engineering units."""
    if len(raw) < HOLDING_COUNT:
        raise ValueError(f"expected {HOLDING_COUNT} holding registers, got {len(raw)}")
    return {key: reg.decode(raw[reg.address]) for key, reg in HOLDING.items()}


def decode_input(raw: list[int]) -> dict:
    """Raw input registers to engineering units, with the alarm bitfield expanded."""
    if len(raw) < INPUT_COUNT:
        raise ValueError(f"expected {INPUT_COUNT} input registers, got {len(raw)}")
    out = {key: reg.decode(raw[reg.address]) for key, reg in INPUT.items()}
    out["alarms"] = decode_alarms(int(out["alarm_flags"]))
    out["advice"] = ADVICE_CODES.get(int(out["advice_code"]), "bilinmeyen kod")
    return out


def to_sure_snapshot(holding: dict) -> dict:
    """Shape the twin's plant state the way `backend/rules.py` expects.

    Only the four parameters the rule engine knows about are carried across.
    Ammonia is deliberately dropped: the twin models it, S.U.R.E. does not have a
    sensor for it, and inventing a rule here would put a threshold outside the
    single source of truth. It stays available in the raw reading for the
    operator view.
    """
    return {
        "sensor": {
            "temperature_c": holding["temperature_c"],
            "dissolved_oxygen_mgl": holding["dissolved_oxygen_mgl"],
            "ph": holding["ph"],
            "tds_ppm": holding["tds_ppm"],
        },
        # The twin's appetite/stress indices are NOT mapped onto S.U.R.E.'s
        # vision channel. In the twin they are derived from water chemistry and
        # then noised, while S.U.R.E.'s channel measures movement — and the
        # simulated fish do not change how they move when stressed
        # (`activity` in tank_sim.gd is purely circadian). Feeding one into the
        # other would look like an integration and measure nothing.
        "vision": None,
    }
