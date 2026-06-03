# Lüfter-Steuerung mit Raspberry Pi 5 + BME280

A small school project. Goal in one sentence:

> From my **laptop**, over the local Wi-Fi, send commands to a **Raspberry Pi 5**
> to turn a fan **on / off**, set its **speed**, and read the **status**.
> While the fan is on, the Pi keeps measuring the temperature with a **BME280**
> sensor and keeps the fan running until the temperature drops and stays stable.

This file is the **plan / TODO list**. There is no code yet — we build it step by step.

---

## How it should work

```
   Laptop (you)                         Raspberry Pi 5 (same Wi-Fi)
┌──────────────┐    HTTP over Wi-Fi   ┌──────────────────────────────────┐
│   cli/       │ ───────────────────► │  pi/  (small web server)         │
│              │   fan on / off /     │   ├─ reads BME280 over I2C        │
│  fan on      │   status / speed     │   ├─ switches fan over GPIO       │
│  fan off     │ ◄─────────────────── │   └─ temp-loop: keep fan on until │
│  fan status  │     answers (JSON)   │       temperature is stable       │
│  fan speed 3 │                      │                                   │
└──────────────┘                      └──────────────────────────────────┘
```

Two folders, two jobs:

- **`pi/`** — runs **on the Raspberry Pi**. A tiny web server that owns the
  hardware (sensor + fan) and contains the automatic temperature logic.
- **`cli/`** — runs **on your laptop**. It only sends commands to the Pi over
  the network and prints the answers. It has no hardware code.

---

## TODO list

### 0. Hardware (one time)
- [ ] Wire the **BME280** to the Pi's **I2C** pins (SDA, SCL, 3V3, GND).
- [ ] Wire the **fan** to a **GPIO** pin (via a transistor/MOSFET, the fan
      draws more current than a GPIO pin can give directly).
- [ ] On the Pi: enable I2C → `sudo raspi-config` → *Interface Options* → *I2C*.
- [ ] Find the Pi's IP address on the network: `hostname -I` (e.g. `192.168.0.42`).

### 1. The Pi server (`pi/`)
    cd ~/donerkebabfans/pi
    source .venv/bin/activate
    sudo .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
    
- [ ] Small web server (FastAPI) that answers HTTP requests.
- [ ] **Sensor**: read temperature/humidity/pressure from the BME280 (I2C).
- [ ] **Fan**: turn GPIO pin on / off. (Speed = see note below.)
- [ ] **Endpoints** the CLI can call:
  - [ ] `GET  /status`  → `{ "on": true/false, "speed": 0-3, "temperature": 21.5 }`
  - [ ] `POST /fan/on`
  - [ ] `POST /fan/off`
  - [ ] `POST /fan/speed`  with `{ "speed": 0-3 }`
- [ ] **Temperature loop** (the important part):
  - [ ] When the fan is turned on, start a background task.
  - [ ] Every few seconds, read the temperature from the BME280.
  - [ ] Keep the fan on until the temperature has **dropped and stayed stable**
        (e.g. it stopped falling for X readings, or went below a target value).
  - [ ] Then turn the fan off automatically.

### 2. The CLI (`cli/`)
- [ ] Connect to the Pi by its IP, e.g. `python -m cli --host 192.168.0.42`.
- [ ] Commands:
  - [ ] `fan on`
  - [ ] `fan off`
  - [ ] `fan monitor`   (also shows the current temperature)
  - [ ] `fan speed <0-3>`
- [ ] Print clear answers and a friendly error if the Pi can't be reached.

### 3. Test
- [ ] Run the server on the Pi, run the CLI on the laptop, try every command.
- [ ] Warm up the sensor (e.g. with a hand) and check the fan stays on, then
      turns off by itself once the temperature settles back down.

---

## Note about "fan speed"

The small Raspberry Pi 5 fan is basically **on/off**. Real speed control needs a
fan that understands **PWM**. So we have two options — decide later:

- **Simple:** `speed` just means *off (0)* or *on (1)*.
- **Full:** use a PWM-capable fan and map `speed` to a duty cycle (0–100%).

We'll start simple and can upgrade later.

---

## Dev setup (already prepared)

- A Python virtual environment lives at **`.venv/`** in the project root.
  Zed/Pyright is configured to use it, so imports will resolve once we add code.
- Install/laptop packages: `httpx` (for the CLI) is already installed.
- On the **Raspberry Pi** we will additionally install: `fastapi`, `uvicorn`,
  `gpiozero`, and `adafruit-circuitpython-bme280`.

Activate the venv in a terminal with:

```bash
source .venv/bin/activate
```
