# VULCAN - Automotive Cybersecurity Research Bench

> Static, isolated bench for CAN / UDS security research on a salvaged **Renault Clio 4 instrument cluster**.
> This file is the project handbook and single entry point. Read it first, then `docs/RESEARCH.md`.

---

## 1. What this project is

VULCAN is a hands-on research bench built around a used Clio 4 instrument cluster powered in isolation on a desk (the "third way": all the demonstrative value of live CAN fuzzing, **zero risk** to a real car).

**Short-term goal:** bring the cluster up on an isolated bench, map its CAN traffic, and enumerate its UDS (ISO 14229) diagnostic surface.

**Research differentiator (the reason this project exists):** combine **grammar-aware / stateful UDS fuzzing** with **side-channel analysis of the SecurityAccess (0x27) service** - a largely unexplored intersection, aimed at venues like ESCAR and competitions like Pwn2Own Automotive. See `docs/RESEARCH.md` for the literature and where the gap is.

This is **defensive security research on owned hardware**, conducted responsibly. See §4.

---

## 2. Current status

- **Phase:** 0 - hardware acquired, bench bring-up in progress (host + software pipeline ready).
- **Blocking unknowns** (fill these in as they resolve - see §11):
  -  Host machine: Windows 11 + WSL2 (Ubuntu 24.04, kernel 6.18 ships CAN/gs_usb/isotp).
  -  Cluster reference: **248106952R** confirmed; connector = 24 pins (2x12).
  - Cluster connector **pinout not yet decoded** (multimeter ordered; §4.2 gate).
  - Mating connector not yet sourced (spec after decode).
  - CAN bitrate not yet confirmed (expected 500 kbps).

---

## 3. Hardware inventory

| Item | Model | Notes |
|---|---|---|
| Target ECU | Renault Clio 4 instrument cluster | Ref. **248106952R** (verify exact digits on the physical label), supplier code VPFRRF-10849-BD, build **11/03/2016** (likely Phase 1). Rear connector confirmed intact. |
| CAN interface | **DSD TECH SH-C30G** (isolated, Canable 1.0 Pro base, STM32F072) | Classic CAN 2.0 A/B, candleLight firmware -> native SocketCAN. Screw terminal: CAN-H / CAN-L / GND. **Galvanically isolated** (protects the host USB). No built-in 120 Ω switch -> external termination required. |
| Power supply | **WANPTEK 30V / 5A (150 W)** | Adjustable, CV/CC auto-switch, OCP + short-circuit protection. **Bench rule: set 12.0 V, current limit ~2 A before connecting anything.** |
| Jumper wires | ELEGOO 120 pcs Dupont (M-F, M-M, F-F) | |
| Resistors | ALLECIN 250 pcs assortment | Use **120 Ω** for CAN termination. |
| Multimeter | *(confirm availability)* | Mandatory for pinout verification before power-up. |

---

## 4. Safety & ethics rules (NON-NEGOTIABLE)

These constrain all work on the bench.

1. **Bench-only.** All work happens on the isolated cluster on the desk - never a live/driven vehicle or a public network.
2. **Pinout before power.** Never apply 12 V until every pin (B+, +APC, GND, CAN-H, CAN-L) has been confirmed with a multimeter. When in doubt, do not power.
3. **Current-limited supply.** The PSU stays at 12.0 V with a ~2 A cap and OCP on. Any procedure that assumes an unlimited source is rejected.
4. **Isolation.** The SH-C30G is isolated for a reason - keep the host on the isolated side.
5. **Owned hardware only.** This is a salvaged cluster the researcher owns.
6. **Responsible disclosure.** Any genuine vulnerability found in a shipping product is handled via coordinated disclosure (e.g. the vendor's program / YesWeHack / ZDI) - never published raw. No secrets, keys, or vehicle-identifying data committed to the repo.

---

## 5. Software stack

Host runs Linux (native or on a Pi). SocketCAN is the backbone.

- **Bring-up / sniffing:** `can-utils` (candump, cansniffer, cansend, cangen), SocketCAN kernel drivers (`gs_usb` for candleLight).
- **Python tooling:** `python-can`, `cantools`, `can-isotp` (ISO 15765-2 transport).
- **UDS / discovery:** `caringcaribou` (uds discovery, service/DID enumeration), optionally `scapy` automotive layers.
- **Fuzzing:** `boofuzz` (protocol/state fuzzing) as a base for the custom stateful/grammar-aware UDS mutator (Phase 3).
- **GUI (optional):** SavvyCAN for visual traffic mapping.
- **Side-channel (Phase 4):** ChipWhisperer + NewAE tooling, TVLA methodology.

Interface bring-up (candleLight -> native SocketCAN), for reference:
```bash
# device usually enumerates as can0 with gs_usb; if using slcan firmware, use slcand instead
sudo ip link set can0 up type can bitrate 500000
candump can0
```

---

## 6. Repository structure (proposed)

```
.
├── PROJECT.md                # this file (project handbook)
├── README.md                # public-facing project description
├── docs/
│   ├── RESEARCH.md          # annotated bibliography / research grounding
│   ├── pinout.md            # cluster connector mapping (fill after decoding)
│   └── bench-setup.md       # wiring, PSU settings, photos
├── config/
│   └── bus.yaml             # interface name, bitrate, known arbitration IDs
├── src/
│   ├── bringup/             # interface up, sanity checks
│   ├── mapping/             # passive sniffing / cartography
│   ├── uds/                 # UDS client, discovery, DID/NRC enumeration
│   └── fuzzer/              # stateful + grammar-aware UDS mutator (core)
├── sidechannel/             # ChipWhisperer captures, TVLA analysis (Phase 4)
├── lab-notebook/            # dated experiment logs (see §8)
└── captures/                # raw candump logs (gitignored if large / sensitive)
```

---

## 7. Roadmap

- **Phase 0 - Bench bring-up.** Decode connector pinout (multimeter), power the cluster safely, bring up `can0`, confirm bitrate, first `candump`. Expect the isolated cluster to be quiet or to emit errors - normal.
- **Phase 1 - Passive mapping.** Log and cartography the cluster's transmitted frames; identify candidate diagnostic IDs.
- **Phase 2 - UDS discovery.** CaringCaribou discovery; DiagnosticSessionControl (0x10); enumerate services, ReadDataByIdentifier (0x22) DIDs, map negative response codes (NRCs). Detect SecurityAccess (0x27).
- **Phase 3 - Stateful / grammar-aware UDS fuzzer (core).** Encode a UDS/ISO-TP grammar; mutation engine that adapts to NRCs, response timings, and bus-off events. This is the primary engineering contribution.
- **Phase 4 - Side-channel-guided SecurityAccess (novel).** Instrument the 0x27 seed/key exchange; capture power/EM traces (ChipWhisperer); apply TVLA to locate leakage; use timing/side-channel feedback to guide the fuzzer and analyze the seed-key computation.
- **Phase 5 - Write-up & disclosure.** Technical article (English), reproducible repo, video demo; ESCAR / Pwn2Own framing; responsible disclosure if applicable.

---

## 8. Working conventions

- **Primary language:** Python for tooling; shell for SocketCAN setup. Keep scripts idempotent.
- **Single source of config:** interface name, bitrate, and known arbitration IDs live in `config/bus.yaml` - never hard-code them across scripts.
- **Documentation-first (this is where the CV value is).** Every experiment produces a dated entry in `lab-notebook/` (setup, hypothesis, commands run, observations, raw log path). Methodology rigor > raw results.
- **Safety gate:** before anything that energizes or drives the hardware, restate the relevant §4 rule and confirm the pinout is verified.
- **Cite the research:** when implementing a technique, point to the relevant entry in `docs/RESEARCH.md`.
- **Reproducibility:** prefer small, composable scripts over monoliths; log raw CAN to `captures/`.

---

## 9. Glossary

- **CAN** - Controller Area Network (ISO 11898), the physical/data-link bus.
- **ISO-TP** - ISO 15765-2 transport protocol; segments UDS messages over CAN.
- **UDS** - Unified Diagnostic Services (ISO 14229), application-layer diagnostics.
- **SID** - Service Identifier; positive response = request SID + 0x40.
- **Sub-function / DID** - service parameter / Data Identifier (read via 0x22).
- **NRC** - Negative Response Code (0x7F ...); key feedback signal for the fuzzer.
- **DTC** - Diagnostic Trouble Code (read 0x19 / clear 0x14).
- **DiagnosticSessionControl (0x10)** - switches diagnostic session (default/extended/programming).
- **SecurityAccess (0x27)** - seed/key challenge-response guarding privileged services.
- **bus-off** - CAN error state after excessive faults; a fuzzing observable.
- **TVLA** - Test Vector Leakage Assessment; detects side-channel leakage.
- **SPA / DPA / CPA** - Simple / Differential / Correlation Power Analysis.

---

## 10. External references

Full annotated bibliography in **`docs/RESEARCH.md`**. It grounds both the fuzzing side (stateful, diagnosis-guided, grammar-aware) and the side-channel side (power analysis, TVLA, automotive seed-key), and states explicitly where the VULCAN intersection is novel.

---

## 11. Open TODO (resolve and update §2)

- [x] **Host machine:** Windows 11 + WSL2 (Ubuntu 24.04). See `docs/bench-setup.md §4`.
- [x] **Connector photo** obtained -> 24 pins (2x12). Pinout decode into `docs/pinout.md` still pending.
- [x] **CAN bitrate confirmed:** 500 kbps (clean frames captured on the Clio 4 OBD bus, 2026-09-04).
- [x] **Confirm exact cluster reference:** 248106952R (label, 2026-07-31).
- [x] **Multimeter:** KAIWEETS ordered - mandatory before any power-up.
- [ ] **Source the mating connector** (24-pin) - spec after decode.
