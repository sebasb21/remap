# remap

Turns a normal self-centering joystick axis into a **virtual throttle lever** on Windows.

Push the stick forward → throttle increases. Pull back → throttle decreases. Release → the stick snaps back to center, but the virtual throttle stays where you left it. The further you deflect, the faster it moves. Output is sent as a virtual Xbox 360 stick axis via ViGEmBus, so any game that reads a standard gamepad will see a throttle that holds position.

## Requirements

- Windows 10/11
- [Python 3.10+](https://www.python.org/downloads/windows/) (check "Add Python to PATH" during install)
- [ViGEmBus driver](https://github.com/nefarius/ViGEmBus/releases) — provides the virtual Xbox 360 controller. Install once and reboot if prompted.
- A connected joystick / gamepad

## Setup

Open PowerShell in the project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If activation is blocked by execution policy:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Run

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

On start it lists detected joysticks, then begins forwarding the configured axis to the virtual gamepad.

### Identify which stick is which

If you have two identical controllers:

```powershell
python main.py identify
```

Press any button on a stick to highlight its index.

## Configuration

Edit `config.json` (or tweak live with the hotkeys below — changes are saved automatically).

| Field                          | Meaning                                                              |
| ------------------------------ | -------------------------------------------------------------------- |
| `input.joystick_index`         | Which detected joystick to read (see startup list)                   |
| `input.axis_index`             | Physical axis index (0=X, 1=Y, 2=Z/twist, 3=throttle on T.16000M)    |
| `input.invert`                 | Flip axis direction                                                  |
| `remapping.dead_zone`          | Ignore stick movement below this magnitude (0..1)                    |
| `remapping.max_rate`           | Max units/sec the output moves when stick is fully deflected         |
| `remapping.acceleration_power` | Curve exponent — higher = more sensitive near the edges, gentler near center |
| `output.virtual_axis`          | `left_x`, `left_y`, `right_x`, or `right_y`                          |
| `update_rate`                  | Polling/output Hz                                                    |

### Hotkeys (while running)

| Key   | Action                          |
| ----- | ------------------------------- |
| `i`   | Toggle invert                   |
| `d` / `D` | Dead zone −0.01 / +0.01     |
| `r` / `R` | Max rate −0.1 / +0.1        |
| `a` / `A` | Accel power −0.1 / +0.1     |
| `0`   | Reset output to 0               |
| `?`   | Show help                       |
| `q`   | Quit                            |

## Troubleshooting

- **`Failed to create virtual gamepad`** — install ViGEmBus and reboot.
- **No joysticks listed** — confirm Windows sees the device in `joy.cpl`.
- **Game doesn't react** — make sure the game is reading from the virtual Xbox 360 controller (it appears alongside your real devices).
