# Godox TT685II stuck at 14mm: wide-panel sensor research

My **Godox TT685II (Sony, TT685IIS)** is stuck in 14mm mode. The flash
believes the pull-out wide-angle diffuser panel is deployed even when it is
fully stowed, so the zoom head no longer moves (no auto zoom, no manual zoom).
Reseating and cleaning the panel did not help.

The goal is to understand how Godox detects the wide panel in firmware and,
ideally, to build a patched TT685II firmware that ignores the sensor.

## 🙏 Call for help: TT685II firmware wanted

**Godox has never published a firmware file for the TT685II series**, and
the unit cannot be read back over USB. If you have any of the following,
please open an issue:

- An official TT685II / TT685IIS / IIC / IIN / IIF / IIO firmware file
  (e.g. received from Godox support, a service centre, or a beta program)
- Knowledge of the TT685II USB update protocol (packet captures of a real
  update would be great)
- Board photos showing the wide-panel switch / sensor location and MCU
  part number
- Experience with the V860III / TT685II internals in general

## What is known so far

### TT685II hardware (observed over USB)

| Item | Value |
|---|---|
| USB ID | `VID_0483` (STMicroelectronics) / `PID_572B` |
| Serial string | `GODOX` |
| Class | HID (vendor-defined), not ST's ROM DFU (`0483:DF11`) |

- The device is an **STM32** running a Godox HID bootloader/updater.
- The official updater ("Godox G3 / V2.0", Qt + hidapi) is **write-only**:
  it contains no firmware read-back path.
- No TT685II entry exists in Godox's current online firmware catalogue
  (`G3_firmwares.json`, 70 devices as of Nov 2026).

### Old TT685 (mk I) `.fri` format

The first-generation TT685 firmware (`TT685S_V2.1.fri`) is **not** encrypted.
It is Intel HEX text with each byte bit-rotated depending on its position:

```
plain[i] = rol8(enc[i], (i % 4) + 2)      # after a short header
```

The decoded image is AVR (ATmega) code. This is a different MCU from the
TT685II, so it is not useful for patching the mk II. A decoder is in
[`tools/decode_fri.py`](tools/decode_fri.py).

### V860IIIS firmware (closest relative with public updates)

`V860IIIS_V1.1.bin` is a plain, unencrypted ARM Cortex-M0 application image:

- Load address `0x08003000` (12 KB bootloader below it), SP `0x20001548`
- Peripherals point to an **STM32F0** with GPIOA–F (F071/F072/F091 class)
- The application never touches the USB peripheral, so USB lives in the bootloader

All addresses below refer to **V860IIIS V1.1 only**.

| What | Where | Notes |
|---|---|---|
| Zoom state byte | RAM `0x200004A8` | low nibble = zoom index 0–9, bit 4 = manual zoom |
| Zoom motor target | RAM `0x200004AA` | |
| Index → motor steps | `0x08016188` | `0, 36, 80, 216, 464, 660, 720, 800, 840, 896` |
| Camera focal length → index | `0x0800F356` | ≥200→9, ≥135→8, ≥105→7, ≥80→6, ≥70→5, ≥50→4, ≥35→3, ≥28→2, else 1 |
| Zoom LCD digits | `0x080078E0` | index 0..9 → 20/24/28/35/50/70/80/105/135/200 |
| Zoom stepper driver | `0x0800DDC0` | phases on PB10/PB11/PB13, enable PE15, end-stop on PA3 |
| `GPIO_ReadInputDataBit` | `0x0800A9D4` | standard SPL helper |

#### Wide-panel detection

- **Sensor input: `PA2`**, polled at `0x0800DC90` and debounced over 40 samples
  (also read once more at `0x0800DE98` after a motor homing move).
- **Wide flag: RAM `0x200004AC`**. It is set at `0x0800DEEA` and cleared at
  `0x0800DCEE` / `0x0800E064`.
- When the flag is `1`:
  - the zoom display (`0x080078F4`) jumps to a special case that draws
    **"14"**
  - zoom commands are rejected (`0x08012BDC`)

So the lock is just **one GPIO input → one RAM flag**. A V860III patch would
force the PA2 reads (`bl` at `0x0800DCA4` and `0x0800DE98`) to return the
"stowed" level, or stop the store at `0x0800DEEA`. Pin polarity and any
updater checksum have **not** been verified on hardware yet.

The TT685II almost certainly uses the same design. Its addresses and pin
will differ, which is why its firmware is needed.

## Related projects

None of these cover the TT685II yet, but they work on the same Godox
STM32F0 platform:

- [photosbyperkins/godox-firmware-patcher](https://github.com/photosbyperkins/godox-firmware-patcher):
  patch tiers for AD-series, V100N and iT30Pro. It notes that some firmware is
  "not on the public download page; request it from Godox support".
- [photosbyperkins/godox-firmware-patcher-requests](https://github.com/photosbyperkins/godox-firmware-patcher-requests):
  community repair / special-request patches (static Cortex-M0 RE).
- [shengmojiaogexing/godox-firmware-lab](https://github.com/shengmojiaogexing/godox-firmware-lab):
  13 devices including **V860III-C / V860III-S V1.1** (same image analysed above).
- [Shiba-inu666/godox-firmware-mods](https://github.com/Shiba-inu666/godox-firmware-mods):
  V100F / V480F mods with an offline firmware simulator.
- [mildsunrise/godox-flash-radio](https://github.com/mildsunrise/godox-flash-radio):
  Godox 2.4 GHz radio protocol documentation.

If you own a TT685II, try **asking Godox support for the firmware file**.
They have handed out unpublished files for other models.

## Non-firmware workarounds

- Pull the wide panel out and snap it back in firmly a few times.
- If the sensor is magnetic, a small magnet near the panel slot may toggle it.
- Repair route: free, clean, or bypass the wide-panel switch in the head.
  ⚠️ The flash capacitor holds ~300 V; remove the batteries and let it discharge
  before opening anything.

## Disclaimer

This is independent interoperability/repair research. No Godox firmware
binaries are included in this repository. Flashing modified firmware can
brick your device. Do it at your own risk.
