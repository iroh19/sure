"""
Modbus TCP client for the digital twin, plus a fake for tests.

S.U.R.E. joins as a second client alongside Godot. It only reads: the plant is
Godot's to write and the actuation is the PLC's, and a monitoring system that can
write into a control loop it does not own is a hazard, not a feature.

The fake exists so the comparison logic can be tested without CODESYS, Godot or a
network. Everything above this layer is then exercised in CI.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol

from .registers import HOLDING_COUNT, INPUT_COUNT, decode_holding, decode_input

HOST = os.getenv("TWIN_MODBUS_HOST", "127.0.0.1")
PORT = int(os.getenv("TWIN_MODBUS_PORT", "502"))
UNIT = int(os.getenv("TWIN_MODBUS_UNIT", "1"))

# Writing into a control loop this system does not own is a hazard, so it is off
# unless asked for explicitly. When enabled, exactly one register is writable —
# HR6, the stress index the PLC already consumes to raise its aeration setpoint.
# Nothing else is reachable through this client by construction, not by policy.
WRITE_ENABLED = os.getenv("TWIN_WRITE_ENABLED", "0") not in ("0", "false", "False")
WRITABLE_REGISTER = 6


class TwinSource(Protocol):
    def read(self) -> tuple[dict, dict]: ...
    def close(self) -> None: ...


class TwinUnavailable(RuntimeError):
    """The twin is not reachable. Callers decide whether that is fatal."""


@dataclass
class FakeTwin:
    """Scripted plant states, for tests and offline development."""
    holding_frames: list[list[int]] = field(default_factory=list)
    input_frames: list[list[int]] = field(default_factory=list)
    cursor: int = 0
    fail_after: int | None = None
    written: list[int] = field(default_factory=list)

    def read(self) -> tuple[dict, dict]:
        if self.fail_after is not None and self.cursor >= self.fail_after:
            raise TwinUnavailable("scripted failure")
        if not self.holding_frames:
            raise TwinUnavailable("no frames scripted")
        i = min(self.cursor, len(self.holding_frames) - 1)
        j = min(self.cursor, len(self.input_frames) - 1) if self.input_frames else 0
        self.cursor += 1
        holding = decode_holding(self.holding_frames[i])
        inputs = decode_input(self.input_frames[j]) if self.input_frames else {}
        return holding, inputs

    def write_stress(self, index: int) -> None:
        if not WRITE_ENABLED:
            raise TwinUnavailable("writing is disabled")
        self.written.append(max(0, min(100, int(index))))

    def close(self) -> None:
        pass


class ModbusTwin:
    """Real client against the CODESYS soft PLC."""

    def __init__(self, host: str = HOST, port: int = PORT, unit: int = UNIT,
                 timeout: float = 3.0):
        self.host, self.port, self.unit, self.timeout = host, port, unit, timeout
        self._client = None

    def _connect(self):
        # `is_socket_open()` is checked on every call, not just when `_client` is
        # None. The first version only ever connected once: if the peer process
        # was killed and restarted (exactly what happened when the fake PLC was
        # bounced during testing), the stale client object survived and every
        # later read silently used a dead socket instead of reconnecting.
        if self._client is not None and self._client.is_socket_open():
            return self._client

        try:
            from pymodbus.client import ModbusTcpClient
        except ImportError as exc:
            raise TwinUnavailable(
                "pymodbus is not installed.\n  pip install 'pymodbus>=3.6'"
            ) from exc

        client = ModbusTcpClient(self.host, port=self.port, timeout=self.timeout)
        if not client.connect():
            self._client = None
            raise TwinUnavailable(
                f"no Modbus server at {self.host}:{self.port}. "
                f"Start the CODESYS soft PLC and the Godot scene first."
            )
        self._client = client
        return self._client

    @staticmethod
    def _unit_kwarg(fn, unit: int) -> dict:
        """pymodbus renamed the unit argument: `slave=` before 3.15, `device_id=`
        after. Inspecting once beats pinning the library or catching TypeError on
        every read."""
        import inspect

        params = inspect.signature(fn).parameters
        if "device_id" in params:
            return {"device_id": unit}
        if "slave" in params:
            return {"slave": unit}
        return {}

    def read(self) -> tuple[dict, dict]:
        # Every failure mode below funnels into TwinUnavailable. This is a
        # boundary to an external process (CODESYS/Godot, or the fake stand-in)
        # that can vanish at any moment, and the caller — the sensor loop running
        # as a background asyncio task — only catches TwinUnavailable. Letting a
        # raw pymodbus/socket exception escape here does not crash loudly; it
        # kills that task silently, and the dashboard is then frozen on the last
        # good reading with no error anywhere. That is exactly what the first
        # version did when the peer was bounced during testing.
        try:
            client = self._connect()
            unit_kw = self._unit_kwarg(client.read_holding_registers, self.unit)
            hr = client.read_holding_registers(0, count=HOLDING_COUNT, **unit_kw)
            ir = client.read_input_registers(0, count=INPUT_COUNT, **unit_kw)
        except TwinUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 — deliberate: see above
            self.close()
            raise TwinUnavailable(f"{type(exc).__name__}: {exc}") from exc

        if hr.isError() or ir.isError():
            self.close()
            raise TwinUnavailable(f"read failed: holding={hr}, input={ir}")

        return decode_holding(list(hr.registers)), decode_input(list(ir.registers))

    def write_stress(self, index: int) -> None:
        """Publish a stress index (0-100) to HR6.

        This is the one lever S.U.R.E. has on the plant: the controller raises
        its dissolved-oxygen setpoint when stress is high, so the aerator opens
        before the low-oxygen alarm would otherwise trip. Writing it is how an
        advisory system becomes a system whose advice can be measured.

        Refuses unless TWIN_WRITE_ENABLED is set. The register address is a
        module constant rather than a parameter: a caller cannot ask this client
        to write anywhere else even by mistake.
        """
        if not WRITE_ENABLED:
            raise TwinUnavailable(
                "writing is disabled. Set TWIN_WRITE_ENABLED=1 to let S.U.R.E. "
                "publish its stress index to the controller."
            )
        value = max(0, min(100, int(index)))

        client = self._connect()
        try:
            kw = self._unit_kwarg(client.write_register, self.unit)
            result = client.write_register(WRITABLE_REGISTER, value, **kw)
        except Exception as exc:  # noqa: BLE001
            self.close()
            raise TwinUnavailable(f"write failed: {type(exc).__name__}: {exc}") from exc

        if result.isError():
            self.close()
            raise TwinUnavailable(f"write rejected: {result}")

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
