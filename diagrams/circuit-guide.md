# Hardware / Electrical Schematic — Build Guide

> **Scope.** A *representative* circuit for **one room** (2 fans + 4 lights = 6 devices),
> exactly as the brief allows. It shows how an **ESP32** would (a) **sense the on/off
> state** of each device and (b) **sense the room's current draw** — the two things the
> problem statement asks for. This is a concept/simulation; no mains wiring is built.
>
> Build this yourself in **Wokwi** and drop a screenshot + share link into this folder.
> (This guide intentionally gives you the pin maps and reasoning to build it, not a
> ready-made project file.)

---

## 1. Design intent — how real sensing would work

Office fans and lights run on **220 V AC**. You never connect an ESP32 (3.3 V logic)
directly to mains. The physically-correct design isolates the two domains:

| What we need | Real-world part | Why |
|---|---|---|
| Know if a device is **ON/OFF** | **AC optocoupler** per device (e.g. `H11AA1` / `PC814`) across the device's live line | The opto's LED lights only when that line is energised; its transistor gives the ESP32 a clean, **galvanically isolated** 3.3 V HIGH/LOW. No mains touches the MCU. |
| Know the **current / power** | **Non-invasive CT clamp** (`SCT-013-030`) on the room's mains feed → burden resistor → ESP32 ADC | Clamps around the live wire without cutting it; outputs a small AC voltage proportional to current. Power (W) = V_rms × I_rms. |
| Brain / uplink | **ESP32** (Wi-Fi) | Reads the isolated states + ADC and reports to the backend over Wi-Fi. |

Each optocoupler output = one device's `status`. The CT reading → `watts`. That maps
**1:1 onto the simulated data model** (`status`, `watts`, `room`).

### Simulating this in Wokwi (low-voltage stand-ins)
Wokwi has no AC parts, so we model the **isolated outputs**, which are what the ESP32
actually sees:

- Each **optocoupler digital output** → a **slide switch / pushbutton** into a GPIO
  (switch = that device is energised). An LED on another GPIO **mirrors** the state so
  the board visually shows what's ON.
- The **CT clamp analog output** → a **potentiometer** on an ADC pin (turning it =
  more room current). Firmware scales the ADC value to Watts.

This keeps the *logic and firmware identical* to the real thing — only the sensor
front-end is swapped for safe 3.3 V equivalents.

---

## 2. Bill of materials (Wokwi)

| Qty | Part (Wokwi) | Represents |
|---|---|---|
| 1 | ESP32 DevKit V1 | The controller |
| 6 | Slide switch (or pushbutton) | Optocoupler state output per device (2 fans + 4 lights) |
| 6 | LED + 220 Ω resistor | Visual "device is ON" indicator |
| 1 | Potentiometer (10 kΩ) | CT-clamp analog current signal for the room |
| — | Jumper wires, common GND | Wiring |

---

## 3. ESP32 pin mapping

**Device-state inputs** (each switch: one leg to the GPIO, one leg to **3.3 V**; enable
the pin's **internal pull-down** so it reads LOW when open, HIGH when the device is "on"):

| Device | Input GPIO | Mirror-LED GPIO |
|---|---|---|
| Fan 1   | GPIO 13 | GPIO 12 |
| Fan 2   | GPIO 14 | GPIO 27 |
| Light 1 | GPIO 16 | GPIO 26 |
| Light 2 | GPIO 17 | GPIO 25 |
| Light 3 | GPIO 18 | GPIO 33 |
| Light 4 | GPIO 19 | GPIO 32 |

**Analog current sense:**

| Signal | Pin | Notes |
|---|---|---|
| Room current (pot wiper) | **GPIO 34** | Input-only, on **ADC1** (ADC2 is unusable while Wi-Fi is active). Pot ends → 3.3 V and GND. |

> Pins chosen to avoid the ESP32 **strapping/flash pins** (0, 2, 6–11, 15). GPIO 34 is
> input-only which is fine for the analog read.

---

## 4. Connection list

```
ESP32 3V3 ─┬─ switch A leg (Fan 1)      ESP32 GND ─┬─ every LED cathode (via 220Ω)
           ├─ switch A leg (Fan 2)                 ├─ potentiometer pin 1
           ├─ switch A leg (Light 1)               └─ common ground rail
           ├─ switch A leg (Light 2)
           ├─ switch A leg (Light 3)      Potentiometer pin 2 ── ESP32 3V3
           └─ switch A leg (Light 4)      Potentiometer wiper ── GPIO 34

Fan 1  switch B leg ── GPIO 13     LED (Fan 1)  anode ── GPIO 12 ─(220Ω)─ GND
Fan 2  switch B leg ── GPIO 14     LED (Fan 2)  anode ── GPIO 27 ─(220Ω)─ GND
Light1 switch B leg ── GPIO 16     LED (Light1) anode ── GPIO 26 ─(220Ω)─ GND
Light2 switch B leg ── GPIO 17     LED (Light2) anode ── GPIO 25 ─(220Ω)─ GND
Light3 switch B leg ── GPIO 18     LED (Light3) anode ── GPIO 33 ─(220Ω)─ GND
Light4 switch B leg ── GPIO 19     LED (Light4) anode ── GPIO 32 ─(220Ω)─ GND
```

All grounds are common. Every input GPIO uses `INPUT_PULLDOWN`.

---

## 5. Electrical reasoning (what a judge will look for)

- **Isolation:** optocouplers / CT clamp keep 220 V AC fully separated from 3.3 V logic —
  the only safe way to interface an MCU with mains.
- **Pull-downs:** without a defined pull, an open input floats and reads random noise.
  Internal pull-downs force a clean LOW when a device is off.
- **ADC choice:** current sensing must sit on **ADC1** (GPIO 32–39) because **ADC2 is
  used by the Wi-Fi radio** — a classic ESP32 gotcha.
- **Current → power:** a real CT gives RMS current; multiply by mains voltage for Watts.
  In simulation the pot's ADC value (0–4095) is linearly scaled to a plausible 0–540 W
  room range (the all-on load of one room).
- **Resistors:** 220 Ω limits LED current to a safe ~6 mA at 3.3 V.
- **Power budget:** the ESP32 (USB 5 V) easily drives six indicator LEDs; real relays/CTs
  would use their own supply, not the 3.3 V rail.

---

## 6. Firmware behaviour (concept — how it feeds the backend)

```
setup():
  for each device pin -> pinMode(pin, INPUT_PULLDOWN)
  for each LED pin    -> pinMode(pin, OUTPUT)

loop():
  for each device:
     state = digitalRead(devicePin)        // HIGH = ON
     digitalWrite(ledPin, state)           // mirror on the board
  raw   = analogRead(34)                    // 0..4095 from CT/pot
  watts = map(raw, 0, 4095, 0, 540)         // room current -> Watts
  // POST { room, devices:[{id,status}], watts } to the backend /ingest endpoint
  // (in this project the backend simulator generates this data directly)
```

In our submission the **backend simulator** produces exactly this shape of data, so the
firmware above is the drop-in replacement if real hardware were attached.

---

## 7. Wokwi vs Tinkercad — pick Wokwi

| | Wokwi | Tinkercad |
|---|---|---|
| ESP32 + Wi-Fi | ✅ yes | ❌ Arduino Uno only, no ESP32/Wi-Fi |
| ADC / analog sensor | ✅ potentiometer | ✅ |
| Shareable link + diagram | ✅ | limited |

Because the design centres on an **ESP32 reporting over Wi-Fi**, **build it in Wokwi**.
Save the screenshot as `diagrams/circuit-wokwi.png` and paste the share link below.

**Wokwi share link:** _(add after building)_
