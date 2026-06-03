import curses
import os
import time
from datetime import datetime
from typing import Any

import httpx

PI_URL = os.getenv("PI_URL", "http://172.30.23.13:8000")
REFRESH_SECONDS = 0.5


ASCII_LOGO = r"""
 ____                  _              _  __     _           _     _____
|  _ \  ___  _ __   __| | ___ _ __   | |/ /___ | |__   __ _| |__ |  ___|_ _ _ __  ___
| | | |/ _ \| '_ \ / _` |/ _ \ '__|  | ' // _ \| '_ \ / _` | '_ \| |_ / _` | '_ \/ __|
| |_| | (_) | | | | (_| |  __/ |     | . \ (_) | |_) | (_| | |_) |  _| (_| | | | \__ \
|____/ \___/|_| |_|\__,_|\___|_|     |_|\_\___/|_.__/ \__,_|_.__/|_|  \__,_|_| |_|___/
"""


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9 / 5) + 32


def api_get(endpoint: str) -> dict[str, Any]:
    response = httpx.get(f"{PI_URL}{endpoint}", timeout=5)
    response.raise_for_status()
    return response.json()


def api_post(endpoint: str) -> dict[str, Any]:
    response = httpx.post(f"{PI_URL}{endpoint}", timeout=5)
    response.raise_for_status()
    return response.json()


def normalize_stats(data: dict[str, Any]) -> dict[str, Any]:
    if "statistics" in data and isinstance(data["statistics"], dict):
        stats = data["statistics"]
    elif "fan" in data and isinstance(data["fan"], dict):
        stats = data["fan"]
    else:
        stats = data

    temperature = stats.get("temperature")
    humidity = stats.get("humidity")
    pressure = stats.get("pressure")

    result = {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
    }

    if "in_fahrenheit" in data:
        result["fahrenheit"] = data["in_fahrenheit"]
    elif temperature is not None:
        result["fahrenheit"] = celsius_to_fahrenheit(float(temperature))
    else:
        result["fahrenheit"] = None

    return result


def init_colors():
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)


def color(pair: int):
    return curses.color_pair(pair)


def safe_addstr(stdscr, y: int, x: int, text: str, attr=0):
    height, width = stdscr.getmaxyx()

    if y < 0 or y >= height:
        return

    if x < 0 or x >= width:
        return

    max_len = width - x - 1

    if max_len <= 0:
        return

    try:
        stdscr.addstr(y, x, text[:max_len], attr)
    except curses.error:
        pass


def temperature_color(temp: float | None):
    if temp is None:
        return color(3)

    if temp >= 26.0:
        return color(4) | curses.A_BOLD

    if temp <= 24.0:
        return color(2) | curses.A_BOLD

    return color(3) | curses.A_BOLD


def fan_color(fan_state: str):
    fan_state = fan_state.lower()

    if fan_state == "on":
        return color(2) | curses.A_BOLD

    if fan_state == "off":
        return color(4) | curses.A_BOLD

    if fan_state == "unchanged":
        return color(3) | curses.A_BOLD

    return color(3)


def draw_screen(
    stdscr,
    command_input: str,
    logs: list[str],
    stats: dict[str, Any],
    fan_mode: str,
    fan_state: str,
    error: str | None,
):
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    if height < 24 or width < 70:
        safe_addstr(
            stdscr,
            0,
            0,
            "Terminal too small. Make it bigger.",
            color(4) | curses.A_BOLD,
        )
        stdscr.refresh()
        return

    safe_addstr(stdscr, 0, 0, " DonerKebabFans CLI ", color(7) | curses.A_BOLD)

    logo_lines = ASCII_LOGO.strip("\n").splitlines()
    for index, line in enumerate(logo_lines[:5]):
        safe_addstr(stdscr, 2 + index, 2, line, color(5) | curses.A_BOLD)

    safe_addstr(stdscr, 8, 2, f"API: {PI_URL}", color(1))
    safe_addstr(
        stdscr, 9, 2, f"Updated: {datetime.now().strftime('%H:%M:%S')}", color(1)
    )

    mode_attr = (
        color(2) | curses.A_BOLD if fan_mode != "manual" else color(3) | curses.A_BOLD
    )
    safe_addstr(stdscr, 10, 2, "Mode: ", curses.A_BOLD)
    safe_addstr(stdscr, 10, 8, fan_mode.upper(), mode_attr)

    safe_addstr(stdscr, 11, 2, "Fan State: ", curses.A_BOLD)
    safe_addstr(stdscr, 11, 13, fan_state.upper(), fan_color(fan_state))

    safe_addstr(stdscr, 13, 2, "Live Statistics", color(1) | curses.A_BOLD)

    if error:
        safe_addstr(stdscr, 15, 4, f"Error: {error}", color(4) | curses.A_BOLD)
    else:
        temp_c = stats.get("temperature")
        temp_f = stats.get("fahrenheit")
        humidity = stats.get("humidity")
        pressure = stats.get("pressure")

        if temp_c is not None:
            temp_c_float = float(temp_c)
            temp_f_float = (
                float(temp_f)
                if temp_f is not None
                else celsius_to_fahrenheit(temp_c_float)
            )

            safe_addstr(stdscr, 15, 4, "Temperature: ", curses.A_BOLD)
            safe_addstr(
                stdscr,
                15,
                17,
                f"{temp_c_float:.2f} °C / {temp_f_float:.2f} °F",
                temperature_color(temp_c_float),
            )
        else:
            safe_addstr(stdscr, 15, 4, "Temperature: waiting for data...", color(3))

        if humidity is not None:
            safe_addstr(stdscr, 16, 4, "Humidity:    ", curses.A_BOLD)
            safe_addstr(
                stdscr, 16, 17, f"{float(humidity):.2f} %", color(6) | curses.A_BOLD
            )

        if pressure is not None:
            safe_addstr(stdscr, 17, 4, "Pressure:    ", curses.A_BOLD)
            safe_addstr(
                stdscr, 17, 17, f"{float(pressure):.2f} hPa", color(1) | curses.A_BOLD
            )

    command_x = 50
    safe_addstr(stdscr, 13, command_x, "Commands", color(1) | curses.A_BOLD)
    safe_addstr(
        stdscr, 15, command_x, "/fan-on       auto control every 500ms", color(2)
    )
    safe_addstr(stdscr, 16, command_x, "/fan-off      stop modes + turn off", color(4))
    safe_addstr(
        stdscr, 17, command_x, "/fan-monitor  monitor sensor every 500ms", color(3)
    )
    safe_addstr(stdscr, 18, command_x, "/status       check server", color(1))
    safe_addstr(stdscr, 19, command_x, "/clear        clear output", color(6))
    safe_addstr(stdscr, 20, command_x, "/exit         close CLI", color(5))

    log_start = 20
    safe_addstr(stdscr, log_start, 2, "Output", color(1) | curses.A_BOLD)

    max_log_lines = max(1, height - log_start - 3)
    visible_logs = logs[-max_log_lines:]

    for index, log in enumerate(visible_logs):
        attr = 0

        if "ERROR" in log:
            attr = color(4) | curses.A_BOLD
        elif "started" in log or "updated" in log:
            attr = color(2)
        elif log.startswith(">"):
            attr = color(5) | curses.A_BOLD

        safe_addstr(stdscr, log_start + 1 + index, 4, log, attr)

    input_line = height - 2
    safe_addstr(stdscr, input_line, 0, " " * (width - 1), color(7))
    safe_addstr(stdscr, input_line, 0, f"> {command_input}", color(7) | curses.A_BOLD)

    stdscr.refresh()


def main(stdscr):
    init_colors()

    curses.curs_set(1)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    command_input = ""
    logs = ["CLI started. Type /help for commands."]
    stats = {}
    error = None

    auto_fan_enabled = False
    monitor_enabled = False

    fan_mode = "manual"
    fan_state = "unknown"

    last_auto_request = 0.0
    last_monitor_request = 0.0

    running = True

    while running:
        now = time.time()

        if auto_fan_enabled and now - last_auto_request >= REFRESH_SECONDS:
            try:
                result = api_post("/fan/on")
                stats = normalize_stats(result)
                fan_state = str(result.get("fan", fan_state))
                fan_mode = "auto-control"
                error = None
            except Exception as exc:
                error = str(exc)

            last_auto_request = now

        if (
            monitor_enabled
            and not auto_fan_enabled
            and now - last_monitor_request >= REFRESH_SECONDS
        ):
            try:
                result = api_get("/fan/monitor")
                stats = normalize_stats(result)
                fan_mode = "monitor"
                error = None
            except Exception as exc:
                error = str(exc)

            last_monitor_request = now

        draw_screen(
            stdscr=stdscr,
            command_input=command_input,
            logs=logs,
            stats=stats,
            fan_mode=fan_mode,
            fan_state=fan_state,
            error=error,
        )

        key = stdscr.getch()

        if key == -1:
            continue

        if key in [10, 13]:
            command = command_input.strip()
            logs.append(f"> {command}")
            command_input = ""

            if command == "":
                continue

            if command == "/exit":
                running = False
                continue

            if command == "/help":
                logs.append(
                    "Commands: /fan-on, /fan-off, /fan-monitor, /status, /clear, /exit"
                )
                continue

            if command == "/clear":
                logs.clear()
                logs.append("Output cleared.")
                continue

            try:
                if command == "/fan-on":
                    auto_fan_enabled = True
                    monitor_enabled = False
                    fan_mode = "auto-control"

                    logs.append(
                        "Auto control started. Sending POST /fan/on every 500ms."
                    )

                    result = api_post("/fan/on")
                    stats = normalize_stats(result)
                    fan_state = str(result.get("fan", fan_state))
                    error = None

                elif command == "/fan-off":
                    auto_fan_enabled = False
                    monitor_enabled = False
                    fan_mode = "manual"

                    result = api_post("/fan/off")
                    fan_state = str(result.get("fan", "off"))
                    logs.append(f"/fan-off -> {result}")
                    error = None

                elif command == "/fan-monitor":
                    monitor_enabled = True
                    auto_fan_enabled = False
                    fan_mode = "monitor"

                    logs.append(
                        "Monitor mode started. Sending GET /fan/monitor every 500ms."
                    )

                    result = api_get("/fan/monitor")
                    stats = normalize_stats(result)
                    error = None

                elif command == "/status":
                    result = api_get("/")
                    logs.append(f"/status -> {result}")
                    error = None

                else:
                    logs.append(f"Unknown command: {command}")

            except Exception as exc:
                error = str(exc)
                logs.append(f"{command} -> ERROR: {exc}")

        elif key in [127, 8, curses.KEY_BACKSPACE]:
            command_input = command_input[:-1]

        elif key == 27:
            running = False

        elif 32 <= key <= 126:
            command_input += chr(key)


if __name__ == "__main__":
    curses.wrapper(main)
