import asyncio
import time
from pathlib import Path

import board
from adafruit_bme280 import basic as adafruit_bme280
from fastapi import FastAPI, HTTPException
from gpiozero import OutputDevice

app = FastAPI()

i2c = board.I2C()
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)

fan_relay = OutputDevice(17, active_high=False, initial_value=False)

LOG_FILE = Path("status_log.txt")
LOG_INTERVAL_SECONDS = 10

logger_task = None


def bme280_monitoring():
    temp = bme280.temperature
    humidity = bme280.relative_humidity
    pressure = bme280.pressure

    return {
        "temperature": round(temp, 2),
        "humidity": round(humidity, 2),
        "pressure": round(pressure, 2),
    }


def get_fan_status():
    return "on" if fan_relay.value == 1 else "off"


def write_status_log(statistics: dict, fan_state: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    log_line = (
        f"[{timestamp}] "
        f"fan={fan_state} | "
        f"temperature={statistics['temperature']}°C | "
        f"humidity={statistics['humidity']}% | "
        f"pressure={statistics['pressure']}hPa\n"
    )

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(log_line)


async def automatic_status_logger():
    while True:
        try:
            statistics = bme280_monitoring()
            fan_state = get_fan_status()

            write_status_log(
                statistics=statistics,
                fan_state=fan_state,
            )

        except Exception as error:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            with LOG_FILE.open("a", encoding="utf-8") as file:
                file.write(f"[{timestamp}] error={str(error)}\n")

        await asyncio.sleep(LOG_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup_event():
    global logger_task

    if logger_task is None or logger_task.done():
        logger_task = asyncio.create_task(automatic_status_logger())


@app.on_event("shutdown")
async def shutdown_event():
    global logger_task

    if logger_task is not None:
        logger_task.cancel()


@app.get("/")
async def root():
    return {"message": "PI Fan API Functional, Server is running"}


@app.post("/fan/on")
async def fan_on():
    try:
        statistics = bme280_monitoring()

        if statistics["temperature"] > 31.0:
            fan_relay.on()
            fan_state = "on"
            message = "Fan turned on because temperature is above 28.0°C"

        elif statistics["temperature"] < 28.0:
            fan_relay.off()
            fan_state = "off"
            message = "Fan stayed/turned off because temperature is below 26.0°C"

        else:
            fan_state = get_fan_status()
            message = "Temperature is between 26.0°C and 28.0°C, fan state unchanged"

        return {
            "fan": fan_state,
            "message": message,
            "statistics": statistics,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/fan/off")
async def fan_off():
    try:
        fan_relay.off()

        statistics = bme280_monitoring()
        fan_state = get_fan_status()

        return {
            "fan": fan_state,
            "message": "Fan turned off manually",
            "statistics": statistics,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/fan/monitor")
async def fan_monitoring():
    try:
        statistics = bme280_monitoring()
        fan_state = get_fan_status()

        return {
            "fan": fan_state,
            "statistics": statistics,
            "in_fahrenheit": round(statistics["temperature"] * 9 / 5 + 32, 2),
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/fan/log/{number}")
async def fan_log(number: int):
    if number <= 0:
        raise HTTPException(
            status_code=400,
            detail="Number must be bigger than 0",
        )

    if not LOG_FILE.exists():
        return {
            "requested_lines": number,
            "logs": [],
            "message": "No log file exists yet",
        }

    with LOG_FILE.open("r", encoding="utf-8") as file:
        lines = file.readlines()

    last_lines = lines[-number:]

    return {
        "requested_lines": number,
        "returned_lines": len(last_lines),
        "logs": [line.strip() for line in last_lines],
    }
