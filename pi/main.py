from fastapi import FastAPI

app = FastAPI()

#   - [ ] `GET  /status`  → `{ "on": true/false, "speed": 0-3, "temperature": 21.5 }`
#   - [ ] `POST /fan/on`
#   - [ ] `POST /fan/off`
#   - [ ] `POST /fan/speed`  with `{ "speed": 0-3 }`


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
