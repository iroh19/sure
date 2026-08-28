"""
A stand-in Modbus server that speaks the twin's register map.

CODESYS runs on Windows and Godot needs a display, so neither is available in CI
or on a headless machine. This serves the same registers with a small plant model
of its own, which makes the whole backend -> Modbus -> rule-engine path runnable
and testable without either.

It is explicitly **not** the digital twin. The real plant model is far richer —
virtual clock, APHA oxygen saturation, feed-to-ammonia conversion, biomass growth.
This one moves oxygen on a scripted trajectory and drives a proportional aerator,
which is enough to exercise the wiring and to show the loop closing. Numbers it
produces are not results about aquaculture; they are a test fixture.

The controller here mirrors the twin's documented behaviour on the one path that
matters for the comparison: a DO-low alarm bit, and an aerator that opens as
oxygen falls.

    python -m twin_bridge.fake_plc                  # scripted oxygen crash
    python -m twin_bridge.fake_plc --scenario calm
"""
from __future__ import annotations

import argparse
import asyncio
import math

from .registers import HOLDING_COUNT, INPUT_COUNT

# Matches backend/rules.py. Duplicated here on purpose: this file stands in for a
# PLC written by someone else, and a stand-in that imports the system under test
# would agree with it by construction and prove nothing.
DO_ALARM_BELOW = 6.0

# Base aeration setpoint, and the bump applied when the stress index is high.
# This mirrors the behaviour the twin's README documents: high stress while
# oxygen is below setpoint raises the setpoint by 0.5 mg/L, so the aerator opens
# earlier than the alarm alone would make it. It is the single lever an advisory
# system has on this plant, which makes it the thing to measure.
DO_SETPOINT = 7.0
STRESS_SETPOINT_BUMP = 0.5
STRESS_HIGH = 60

SCENARIOS = {
    # Oxygen decays into the alarm band, the aerator responds, oxygen recovers.
    "crash": lambda t: 8.2 - 4.6 * math.exp(-((t - 60) ** 2) / 700),
    "calm": lambda t: 8.1 + 0.25 * math.sin(t / 25),
    # Slow decline with no recovery — the aerator cannot keep up.
    "decline": lambda t: max(3.4, 8.4 - t * 0.035),
}


class Plant:
    """Minimal plant + controller, enough to close the loop."""

    def __init__(self, scenario: str = "crash"):
        self.t = 0
        self.curve = SCENARIOS[scenario]
        self.aerator = 0
        self.feed_today = 0
        self.stress = 0          # HR6, writable by an external advisor
        self.last_do = None
        self.history: list[dict] = []

    def step(self) -> tuple[list[int], list[int]]:
        self.t += 1
        do = self.curve(self.t)

        # The advisor's lever: a high stress index raises the setpoint, so the
        # aerator opens sooner than the raw oxygen reading alone would justify.
        setpoint = DO_SETPOINT + (STRESS_SETPOINT_BUMP if self.stress >= STRESS_HIGH else 0.0)
        shortfall = max(0.0, setpoint - do)
        self.aerator = int(min(100, shortfall * 45))
        do += self.aerator / 100 * 0.9

        temp = 18.6 + 0.6 * math.sin(self.t / 90)
        ph = 7.35 - 0.0009 * self.t
        nh3 = 0.08 + 0.0016 * self.t
        tds = 318 + 0.11 * self.t

        alarms = 0
        if do < DO_ALARM_BELOW:
            alarms |= 1 << 0
        if nh3 > 0.40:
            alarms |= 1 << 1
        if abs(temp - 19.0) > 1.5:
            alarms |= 1 << 2

        advice = 1 if (alarms & 1) else (2 if (alarms & 2) else 0)
        self.feed_today = min(65000, self.feed_today + 3)

        self.last_do = do
        self.history.append({
            "t": self.t, "do": round(do, 3), "aerator": self.aerator,
            "stress": self.stress, "alarm": bool(alarms & 1),
        })

        holding = [
            round(do * 100), round(temp * 100), round(ph * 100), round(nh3 * 100),
            round(tds), 55, self.stress, 57, 0, 1,
        ]
        inputs = [
            self.aerator, 0, 0, 0, 1 if (alarms & 2) else 0,
            alarms, advice, self.feed_today,
        ]
        return holding, inputs


async def serve(host: str, port: int, scenario: str, tick: float) -> None:
    """Minimal Modbus TCP server: function codes 3 and 4 only.

    Hand-rolled rather than built on pymodbus's datastore. That API has changed
    shape twice recently — ModbusSlaveContext became ModbusDeviceContext and the
    mutable setValues path was removed in favour of SimData — and a test fixture
    that breaks on a dependency's refactor stops being a fixture. The client side
    still exercises the real pymodbus client, which is the part that ships.

    Frame layout (MBAP header + PDU):
        request   txn(2) proto(2) len(2) unit(1) fc(1) addr(2) count(2)
        response  txn(2) proto(2) len(2) unit(1) fc(1) bytecount(1) data(2n)
    """
    plant = Plant(scenario)
    state = {"hr": [0] * 32, "ir": [0] * 32}

    def refresh():
        hr, ir = plant.step()
        state["hr"][:len(hr)] = hr
        state["ir"][:len(ir)] = ir

    refresh()

    async def ticker():
        while True:
            await asyncio.sleep(tick)
            refresh()

    async def handle(reader, writer):
        try:
            while True:
                header = await reader.readexactly(8)
                txn = header[0:2]
                unit = header[6]
                fc = header[7]
                body = await reader.readexactly(4)
                addr = int.from_bytes(body[0:2], "big")
                count = int.from_bytes(body[2:4], "big")

                if fc == 6:
                    # Write single register. Only HR6 is accepted — the plant
                    # owns everything else, and an advisor that can write the
                    # oxygen reading could fake its own success.
                    value = count          # for FC 6 the second field is the value
                    if addr != 6:
                        pdu = bytes([fc | 0x80, 0x02])   # illegal data address
                    else:
                        plant.stress = max(0, min(100, value))
                        state["hr"][6] = plant.stress
                        pdu = bytes([fc]) + body        # echo the request
                elif fc not in (3, 4):
                    # Exception response: fc | 0x80, code 1 (illegal function).
                    pdu = bytes([fc | 0x80, 0x01])
                else:
                    src = state["hr"] if fc == 3 else state["ir"]
                    if addr + count > len(src):
                        pdu = bytes([fc | 0x80, 0x02])   # illegal data address
                    else:
                        values = src[addr:addr + count]
                        payload = b"".join(int(v).to_bytes(2, "big", signed=False)
                                           for v in values)
                        pdu = bytes([fc, len(payload)]) + payload

                frame = txn + b"\x00\x00" + (len(pdu) + 1).to_bytes(2, "big") \
                    + bytes([unit]) + pdu
                writer.write(frame)
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        finally:
            writer.close()

    print(f"fake PLC on {host}:{port}  scenario={scenario}  tick={tick}s")
    print("This is a stand-in for CODESYS, not the digital twin.")

    # Keep the reference: a task created and dropped can be garbage collected
    # mid-flight, and the plant then silently never advances — which is exactly
    # what happened the first time, with every reading frozen at t=1.
    ticker_task = asyncio.create_task(ticker())

    server = await asyncio.start_server(handle, host, port)
    try:
        async with server:
            await server.serve_forever()
    finally:
        ticker_task.cancel()


def main() -> int:
    ap = argparse.ArgumentParser(description="Stand-in Modbus PLC for the twin map")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5020)
    ap.add_argument("--scenario", default="crash", choices=sorted(SCENARIOS))
    ap.add_argument("--tick", type=float, default=1.0)
    args = ap.parse_args()

    try:
        asyncio.run(serve(args.host, args.port, args.scenario, args.tick))
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
