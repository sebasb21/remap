import sys
import time
import json
import msvcrt
from pathlib import Path

import pygame
import vgamepad as vg

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "input": {
        "joystick_index": 0,
        "axis_index": 1,
        "invert": False,
    },
    "remapping": {
        "dead_zone": 0.12,
        "max_rate": 2.0,
        "acceleration_power": 2.0,
    },
    "output": {
        "virtual_axis": "left_y",
    },
    "update_rate": 120,
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print("No config.json found — using defaults.")
        return DEFAULT_CONFIG
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    """Atomic-ish save: write to a temp file then rename over the original."""
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=4)
        f.write("\n")
    tmp.replace(CONFIG_PATH)


def print_help() -> None:
    print("Hotkeys (while running):")
    print("  i       toggle invert")
    print("  d / D   dead_zone   -0.01 / +0.01")
    print("  r / R   max_rate    -0.1  / +0.1")
    print("  a / A   accel power -0.1  / +0.1")
    print("  0       reset output to 0")
    print("  ?       show this help")
    print("  q       quit")
    print("Config is written back to config.json on every change.\n")


def apply_dead_zone(value: float, threshold: float) -> float:
    """Zero out values inside the dead zone and rescale the live range to 0..1."""
    if abs(value) < threshold:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - threshold) / (1.0 - threshold)


def apply_curve(value: float, power: float) -> float:
    """Power curve — larger exponent = more acceleration near the edges."""
    if value == 0.0:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * abs(value) ** power


def push_to_gamepad(gamepad: vg.VX360Gamepad, axis_name: str, value: float) -> None:
    v = max(-1.0, min(1.0, value))
    if axis_name == "left_x":
        gamepad.left_joystick_float(x_value_float=v, y_value_float=0.0)
    elif axis_name == "left_y":
        gamepad.left_joystick_float(x_value_float=0.0, y_value_float=v)
    elif axis_name == "right_x":
        gamepad.right_joystick_float(x_value_float=v, y_value_float=0.0)
    elif axis_name == "right_y":
        gamepad.right_joystick_float(x_value_float=0.0, y_value_float=v)
    else:
        print(f"Unknown virtual_axis '{axis_name}'. Use: left_x, left_y, right_x, right_y")
        sys.exit(1)
    gamepad.update()


def print_status(raw: float, output: float, cfg: dict) -> None:
    inp = cfg["input"]
    remap = cfg["remapping"]
    bar_len = 30
    pos = int((output + 1.0) / 2.0 * bar_len)
    pos = max(0, min(bar_len, pos))
    bar = "[" + "-" * pos + "|" + "-" * (bar_len - pos) + "]"
    inv = "T" if inp.get("invert", False) else "F"
    sys.stdout.write(
        f"\r raw={raw:+.3f} out={output:+.3f} {bar} "
        f"inv={inv} dz={remap['dead_zone']:.2f} "
        f"rate={remap['max_rate']:.2f} pow={remap['acceleration_power']:.2f}\033[K"
    )
    sys.stdout.flush()


def list_joysticks() -> None:
    count = pygame.joystick.get_count()
    print(f"\nDetected {count} joystick(s):")
    for i in range(count):
        j = pygame.joystick.Joystick(i)
        print(f"  [{i}] {j.get_name()}  ({j.get_numaxes()} axes)")
    print()


def identify_mode() -> None:
    """Highlight whichever joystick currently has a button held down.

    Useful when you have two identical controllers and need to know which
    physical stick maps to index 0 vs index 1.
    """
    pygame.init()
    pygame.joystick.init()

    count = pygame.joystick.get_count()
    if count == 0:
        print("No joysticks found.")
        return

    sticks = []
    for i in range(count):
        j = pygame.joystick.Joystick(i)
        sticks.append(j)

    print("\nIdentify mode — press any button on a stick to highlight it.")
    print("Press Ctrl+C to exit.\n")

    # Reserve N lines for the joystick rows so we can rewrite them in place.
    for _ in sticks:
        print()

    blink = 0
    try:
        while True:
            pygame.event.pump()

            # Move cursor up N lines to overwrite previous frame.
            sys.stdout.write(f"\033[{len(sticks)}A")

            for i, stick in enumerate(sticks):
                pressed_buttons = [
                    b for b in range(stick.get_numbuttons()) if stick.get_button(b)
                ]
                active = len(pressed_buttons) > 0

                if active and (blink // 3) % 2 == 0:
                    # Bright yellow background, black text — highly visible.
                    marker = "\033[1;30;43m►\033[0m"
                    name = f"\033[1;33m{stick.get_name()}\033[0m"
                else:
                    marker = " "
                    name = stick.get_name()

                btn_info = (
                    f" buttons={pressed_buttons}" if active else "                    "
                )
                # \033[K clears the rest of the line.
                sys.stdout.write(
                    f"  {marker} [{i}] {name}{btn_info}\033[K\n"
                )

            sys.stdout.flush()
            blink += 1
            time.sleep(1 / 30)

    except KeyboardInterrupt:
        print("\nDone.")


def main() -> None:
    cfg = load_config()
    inp = cfg["input"]
    remap = cfg["remapping"]
    out = cfg["output"]

    update_rate: int = cfg.get("update_rate", 120)
    tick: float = 1.0 / update_rate

    pygame.init()
    pygame.joystick.init()

    list_joysticks()

    joy_count = pygame.joystick.get_count()
    if joy_count == 0:
        print("No joysticks found. Connect a controller and try again.")
        sys.exit(1)

    joy_idx: int = inp["joystick_index"]
    if joy_idx >= joy_count:
        print(f"joystick_index {joy_idx} is out of range (0..{joy_count - 1}).")
        sys.exit(1)

    joystick = pygame.joystick.Joystick(joy_idx)

    axis_idx: int = inp["axis_index"]
    virtual_axis: str = out["virtual_axis"]

    print(f"Input : joystick [{joy_idx}] '{joystick.get_name()}', axis {axis_idx}")
    print(f"Output: virtual Xbox 360 → {virtual_axis}")
    print(f"Rate  : {update_rate} Hz\n")
    print("Push joystick UP to increase output, DOWN to decrease.")
    print("Release → output holds its current value.\n")
    print_help()

    try:
        gamepad = vg.VX360Gamepad()
    except Exception as e:
        print(f"\nFailed to create virtual gamepad: {e}")
        print("Make sure ViGEmBus driver is installed:")
        print("  https://github.com/nefarius/ViGEmBus/releases")
        sys.exit(1)

    output: float = 0.0
    last_time = time.perf_counter()

    try:
        while True:
            now = time.perf_counter()
            dt = now - last_time
            last_time = now

            # ---- handle key presses (non-blocking) ----
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    msvcrt.getwch()  # consume the second byte of arrow/function keys
                    continue
                changed = True
                if ch == "i":
                    inp["invert"] = not inp.get("invert", False)
                elif ch == "d":
                    remap["dead_zone"] = round(max(0.0, remap["dead_zone"] - 0.01), 3)
                elif ch == "D":
                    remap["dead_zone"] = round(min(0.95, remap["dead_zone"] + 0.01), 3)
                elif ch == "r":
                    remap["max_rate"] = round(max(0.0, remap["max_rate"] - 0.1), 3)
                elif ch == "R":
                    remap["max_rate"] = round(remap["max_rate"] + 0.1, 3)
                elif ch == "a":
                    remap["acceleration_power"] = round(
                        max(0.1, remap["acceleration_power"] - 0.1), 3
                    )
                elif ch == "A":
                    remap["acceleration_power"] = round(
                        remap["acceleration_power"] + 0.1, 3
                    )
                elif ch == "0":
                    output = 0.0
                    changed = False
                elif ch == "?":
                    sys.stdout.write("\n")
                    print_help()
                    changed = False
                elif ch == "q" or ch == "\x03":
                    raise KeyboardInterrupt
                else:
                    changed = False
                if changed:
                    save_config(cfg)

            # ---- joystick read & integrate ----
            pygame.event.pump()

            raw: float = joystick.get_axis(axis_idx)
            # pygame Y on most sticks: pulled-back = negative. We want
            # "push toward an increase" to bump output up — invert flips the
            # interpretation if the user's stick behaves the opposite way.
            effective = -raw if inp.get("invert", False) else raw

            processed = apply_dead_zone(effective, remap["dead_zone"])
            rate = apply_curve(processed, remap["acceleration_power"]) * remap["max_rate"]

            output = max(-1.0, min(1.0, output + rate * dt))

            push_to_gamepad(gamepad, virtual_axis, output)
            print_status(raw, output, cfg)

            elapsed = time.perf_counter() - now
            remaining = tick - elapsed
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        print("\n\nStopped.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "identify":
        identify_mode()
    else:
        main()
