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
    humidity = bme280.humidity
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
    elif statistics["temperature"] < 24.0:
        fan_relay.off()
    return {
        "fan": "on",
        "message": "Fan turns on when temperature is above 26.0°C, shuts down when it reaches below 24.0°C",
    }


@app.post("/fan/off")
async def fan_off():
    fan_relay.off()
    return {"fan": "off"}


@app.get("/fan/monitor")
async def fan_monitoring():
    try:
        return bme280_monitoring()
    except Exception as error:
        return {"error": str(error)}
