# Bench setup & power-up procedure

> Static, isolated bench. This document is a **gated checklist**: do not skip a step.
> Governing rules: PROJECT.md §4 (safety, NON-NEGOTIABLE).

## 0. Pre-power safety gate (STOP if any box is unchecked)

- [ ] `docs/pinout.md` fully decoded - B+, +APC, GND, CAN-H, CAN-L confirmed with multimeter (**§4.2**).
- [ ] Multimeter available and used (**§11**).
- [ ] PSU set to **12.0 V**, current limit **~2 A**, OCP **on**, BEFORE anything is connected (**§4.3**).
- [ ] SH-C30G on the isolated side; host never bridged to the cluster's ground directly (**§4.4**).
- [ ] CAN termination decided from the resistance reading (see `config/bus.yaml`).
- [ ] This is the owned salvaged cluster on the desk - no live/driven vehicle (**§4.1 / §4.5**).

## 1. Hardware

| Item | Setting / role |
|---|---|
| WANPTEK 30V/5A PSU | **12.0 V, ~2 A limit, OCP on** - the only power source |
| SH-C30G (isolated, gs_usb) | CAN interface; screw terminal CAN-H / CAN-L / GND |
| 120 Ω resistor | External termination if the pair does not already read ~120 Ω |
| Multimeter | Pinout verification (mandatory) |

## 2. Wiring (after the gate passes)

```
 PSU 12V (+) ──┬── B+  (cluster)
               └── +APC (cluster)      # tie switched rail high so it wakes; adjust after first boot
 PSU GND  (-) ──┬── GND (cluster)
               └── SH-C30G GND
 SH-C30G CAN-H ───── CAN-H (cluster)
 SH-C30G CAN-L ───── CAN-L (cluster)
 120 Ω across CAN-H/CAN-L  # only if the unpowered pair did not already read ~120 Ω
```

Notes:
- Bring current up slowly; a healthy cluster draws well under the 2 A cap. Any jump to the
  limit / OCP trip -> cut power, re-check wiring, do not force (**§4.3**).
- Expect the isolated cluster to be quiet, to light up partially, or to emit CAN error frames.
  All normal for a bench with no rest-of-car bus (PROJECT.md §7, Phase 0).

## 3. Bring up the CAN interface

Host-specific install steps live in the host section below. Once the device enumerates:

```bash
# from repo root - mirrors config/bus.yaml (can0 @ 500000)
sudo bash src/bringup/bring_up_can.sh can0 500000
candump can0            # first look at the bus
```

Then record the session in `lab-notebook/` (dated entry) and drop the raw log in `captures/`.

## 4. Host machine - Windows 11 + WSL2 (Ubuntu 24.04)

**Decided (TODO §11 resolved).** Host is the Windows 11 laptop via WSL2.

Audit done 2026-07-31 - the environment is friendlier than the usual WSL2/CAN horror stories:

| Component | State |
|---|---|
| WSL2 kernel `6.18.33.2-microsoft-standard-WSL2` | Ships `gs_usb`, `can`, `can-raw`, **`can-isotp`**, `vcan`, `slcan` as modules -> **no custom kernel build needed** |
| `usbipd-win` | 5.3.0 already installed |
| `can-utils`, Python stack | Not yet installed - done by `src/bringup/wsl_setup.sh` |

### 4a. One-time host setup (inside WSL Ubuntu, needs your password)

```bash
cd /mnt/c/Users/Marc/Desktop/VULCAN
bash src/bringup/wsl_setup.sh          # apt: can-utils + venv; pip: python-can, cantools, can-isotp, pyyaml
source ~/.venvs/vulcan/bin/activate
```

### 4b. Hardware-free pipeline test (do this before the cluster exists)

```bash
bash src/bringup/vcan_up.sh            # create virtual bus vcan0
cangen vcan0 -g 10 &                   # fake traffic
python src/bringup/sanity_check.py -c vcan0 -t 5   # should count frames on vcan0
bash src/bringup/vcan_up.sh down       # cleanup
```

### 4c. Attach the real SH-C30G (once pinout is decoded & cluster is safe to power)

1. Plug the SH-C30G into Windows. In an **elevated PowerShell**:
   ```powershell
   .\src\bringup\attach_can_usb.ps1     # binds + attaches candleLight (1d50:606f) to WSL
   ```
2. In WSL: `dmesg | tail` should show `gs_usb ... can0`.
3. `sudo bash src/bringup/bring_up_can.sh can0 500000` then `candump can0`.

> WSL2 caveat: `usbipd attach` must be re-run each time the device is re-plugged or WSL
> restarts. `usbipd bind` (admin) is one-time. If the adapter is in slcan/serial mode
> (shows as COMx), reflash candleLight for native gs_usb, or run `slcand` in WSL.

## 5. Power-down

1. `sudo ip link set can0 down`
2. PSU output off.
3. Disconnect. Log anything abnormal in the lab notebook.
