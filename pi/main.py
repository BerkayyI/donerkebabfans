import time

import board
from adafruit_bme280 import basic as adafruit_bme280
from fastapi import FastAPI

app = FastAPI()
i2c = board.I2C()
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)


def function_monitoring():
    time.sleep(1)
    print("\nTemperature: %0.1f C" % bme280.temperature)
    print("Humidity: %0.1f %%" % bme280.humidity)
    print("Pressure: %0.1f hPa" % bme280.pressure)
    time.sleep(2)


@app.get("/")
async def root():
    return {"message": "PI Fan API Functional, Server is running"}


@app.get("/fan/on")
async def set_fan_mode_on():
    return {"message": "Fan turns on neaw"}


@app.get("/fan/off")
async def set_fan_mode_off():
    return {"message": "Fan turns off neaw"}


@app.get("/fan/monitor")
async def fan_monitoring():
    return {"message": "get ascii art of fan monitoring stuff"}
