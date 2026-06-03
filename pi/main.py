import time

import board
from adafruit_bme280 import basic as adafruit_bme280
from fastapi import FastAPI
from gpiozero import OutputDevice

app = FastAPI()
i2c = board.I2C()
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
fan_relay = OutputDevice(17, active_high=False, initial_value=False)


def bme280_monitoring():
    temp = bme280.temperature
    humidity = bme280.relative_humidity
    pressure = bme280.pressure

    return {
        "temperature": temp,
        "humidity": humidity,
        "pressure": pressure,
    }


@app.get("/")
async def root():
    return {"message": "PI Fan API Functional, Server is running"}


@app.post("/fan/on")
async def fan_on():
    statistics = bme280_monitoring()

    if statistics["temperature"] > 26.0:
        fan_relay.on()
        fan_state = "on"
    elif statistics["temperature"] < 24.0:
        fan_relay.off()
        fan_state = "off"
    else:
        fan_state = "unchanged"

    return {
        "fan": fan_state,
        "message": "Fan turns on above 26.0°C and shuts down below 24.0°C",
        "statistics": statistics,
    }


@app.post("/fan/off")
async def fan_off():
    fan_relay.off()
    return {"fan": "off"}


@app.get("/fan/monitor")
async def fan_monitoring():
    try:
        statistics = bme280_monitoring()

        return {
            "statistics": statistics,
            "in_fahrenheit": statistics["temperature"] * 9 / 5 + 32,
        }

    except Exception as error:
        return {"error": str(error)}
