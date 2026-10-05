"""VULCAN - a small UDS (ISO 14229) client over ISO-TP (ISO 15765-2) / SocketCAN.

Built on `can-isotp` (pure-Python CanStack) + `python-can`, so it runs identically
on a real bus (`can0`) and on the virtual bus (`vcan0`) - which is how we test it
against `sim_ecu.py` before touching the real cluster.

    from src.uds.uds_client import UdsClient
    with UdsClient("vcan0", tx_id=0x7E0, rx_id=0x7E8) as ecu:
        r = ecu.read_data_by_identifier(0xF190)   # VIN
        print(r)

Requires: python-can, can-isotp  (both in the project venv).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import can
import isotp

from . import nrc


@dataclass
class UdsResponse:
    """Parsed UDS response. `positive` distinguishes a real answer from a 0x7F refusal."""
    raw: bytes
    positive: bool
    service: int | None = None      # echoed request SID (raw[0] - 0x40 on a positive response)
    data: bytes = b""               # payload after the SID
    nrc: int | None = None          # negative response code, when positive is False

    @property
    def nrc_name(self) -> str | None:
        return nrc.nrc_name(self.nrc) if self.nrc is not None else None

    def __str__(self) -> str:
        if self.positive:
            svc = nrc.service_name(self.service) if self.service is not None else "?"
            return f"+ {svc}: {self.data.hex(' ') or '(no data)'}"
        return f"- NRC 0x{self.nrc:02X} {self.nrc_name}"


class Timeout(Exception):
    pass


class UdsClient:
    """One diagnostic conversation with one ECU, at a fixed (tx_id, rx_id) pair."""

    def __init__(self, channel: str, tx_id: int, rx_id: int,
                 bustype: str = "socketcan", padding: int = 0x00):
        self._own_bus = True
        self.bus = can.Bus(channel=channel, interface=bustype, receive_own_messages=False)
        addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=tx_id, rxid=rx_id)
        params = {"tx_padding": padding, "blocking_send": False}
        self.stack = isotp.CanStack(bus=self.bus, address=addr, params=params)
        self.tx_id, self.rx_id = tx_id, rx_id

    # ---- lifecycle ----
    def close(self) -> None:
        try:
            self.stack.stop()
        except Exception:
            pass
        if self._own_bus:
            self.bus.shutdown()

    def __enter__(self) -> "UdsClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---- the one primitive everything else is built on ----
    def request(self, payload: bytes | list[int], timeout: float = 2.0,
                expect_response: bool = True) -> UdsResponse | None:
        """Send a UDS request; pump ISO-TP until a full response arrives or `timeout`.

        Transparently waits through 0x78 'responsePending' (the ECU asking for more time).
        Returns None if `expect_response` is False, or on timeout with no reply.
        """
        self.stack.send(bytes(payload))
        deadline = time.time() + timeout
        # transmit phase
        while self.stack.transmitting() and time.time() < deadline:
            self.stack.process()
            time.sleep(self.stack.sleep_time())
        if not expect_response:
            return None
        # receive phase (loop through any responsePending)
        while time.time() < deadline:
            self.stack.process()
            if self.stack.available():
                resp = self._parse(self.stack.recv())
                if resp.nrc == 0x78:        # responsePending -> keep waiting
                    deadline = time.time() + timeout
                    continue
                return resp
            time.sleep(self.stack.sleep_time())
        return None

    @staticmethod
    def _parse(raw: bytes) -> UdsResponse:
        if not raw:
            return UdsResponse(raw=raw, positive=False)
        if raw[0] == 0x7F and len(raw) >= 3:
            return UdsResponse(raw=raw, positive=False, service=raw[1], nrc=raw[2])
        return UdsResponse(raw=raw, positive=True, service=raw[0] - 0x40, data=raw[1:])

    # ---- high-level UDS services ----
    def diagnostic_session_control(self, session: int = 0x03, **kw) -> UdsResponse | None:
        return self.request([0x10, session], **kw)

    def tester_present(self, **kw) -> UdsResponse | None:
        return self.request([0x3E, 0x00], **kw)

    def ecu_reset(self, reset_type: int = 0x01, **kw) -> UdsResponse | None:
        return self.request([0x11, reset_type], **kw)

    def read_data_by_identifier(self, did: int, **kw) -> UdsResponse | None:
        return self.request([0x22, (did >> 8) & 0xFF, did & 0xFF], **kw)

    def read_dtc_information(self, subfunction: int = 0x02, mask: int = 0xFF, **kw):
        return self.request([0x19, subfunction, mask], **kw)

    def security_access_request_seed(self, level: int = 0x01, **kw) -> UdsResponse | None:
        """Request the SecurityAccess (0x27) seed. Odd sub-functions request a seed."""
        return self.request([0x27, level], **kw)

    def security_access_send_key(self, level: int, key: bytes, **kw) -> UdsResponse | None:
        return self.request(bytes([0x27, level]) + bytes(key), **kw)
