# Pico 2 W Keyboard Jiggler — Setup

## 1. Flash CircuitPython
Download the **Pico 2 W** UF2 (not the plain Pico 2 — needs the WiFi build)
from circuitpython.org, hold BOOTSEL while plugging in USB, drop the UF2
onto the RPI-RP2 drive. It'll reboot as a `CIRCUITPY` drive.

## 2. Copy libraries
From the Adafruit CircuitPython Library Bundle (match the bundle version to
your CircuitPython version), copy these into the `lib/` folder on CIRCUITPY:
- `adafruit_httpserver` (folder)
- `adafruit_hid` (folder)

Easiest way: `circup install adafruit_httpserver adafruit_hid` if you have
[circup](https://learn.adafruit.com/keep-your-circuitpython-libraries-on-devices-up-to-date-with-circup)
installed on your computer, or grab the folders from the bundle zip and
drag them into `lib/` manually.

## 3. Add your Wi-Fi credentials
Edit `settings.toml` with your real SSID/password, then copy it to the
root of CIRCUITPY (it'll overwrite the placeholder if one already exists).

### Optional: static IP
CircuitPython doesn't have a dedicated static-IP key, but `settings.toml`
entries are just environment variables, so the script reads a few custom
ones. Uncomment and fill in, in `settings.toml`:
```
STATIC_IP = "192.168.1.50"
STATIC_NETMASK = "255.255.255.0"
STATIC_GATEWAY = "192.168.1.1"
STATIC_DNS = "192.168.1.1"
```
Pick an IP outside your router's DHCP range so nothing else gets handed
the same address. Leave `STATIC_IP` out entirely to keep using DHCP —
that's the default and needs no changes. If `STATIC_IP` is set, the code
tries to apply it before connecting to Wi-Fi, and automatically retries
right after connecting if that fails (this varies a bit by board), so no
extra steps are needed either way.

## 4. Copy the code
Rename `code.py` — it's already named that — and copy it to the root of
CIRCUITPY. CircuitPython auto-runs `code.py` on boot.

## 5. Find the IP address
Open the Pico's serial console (Thonny, `screen`, `mu`, etc.) right after
boot — it prints:
```
Connected. IP: 192.168.x.x
Listening on http://192.168.x.x
```
Visit that address from any browser on the same network (phone, laptop,
whatever). No app needed.

## Using the web interface
- **START/STOP** — toggles the jiggler on and off. No more physical button.
- **Commands box** — one command per line: `KEY, SECONDS, PAUSE, MODE`
  - `W, 5, 2` → hold W for 5 seconds, release, pause 2 seconds (MODE
    defaults to `HOLD` if omitted)
  - `E, 1, 3, TAP` → **tap** E repeatedly (press/release) for 1 second,
    then pause 3 seconds. Use TAP for anything where holding the key
    would just sit there instead of acting — e.g. a pickup/interact key
    where you want the item grabbed and immediately tossed, not held.
  - `A, C` → hold A down continuously (runs until stopped or total
    runtime expires). `A, C, TAP` does the same but taps instead of
    holding.
  - Mouse buttons work the same way — use `MOUSE1`/`LMB` (left click),
    `MOUSE2`/`RMB` (right click), or `MOUSE3`/`MMB` (middle click) as
    the key. `MOUSE1, C, TAP` left-clicks continuously; `MOUSE2, 1, 2`
    holds right-click for 1s then pauses 2s. No extra library needed —
    `adafruit_hid` (already required) includes mouse support.
  - Commands run in order and loop back to the top when they reach the
    end (unless one is continuous, which just runs until the session ends)
  - **Tap interval** — how fast TAP mode presses/releases, in seconds
    (default 0.15s). Lower = faster tapping.
- **Total run time** — how long the whole session runs before
  auto-stopping, in seconds. Preset buttons fill in common durations.
- Settings save independently of START/STOP — click **Save Settings**
  any time; it takes effect the next time you press START (or
  immediately restarts the cycle if it was already running).

## Notes
- The onboard LED / GPIO toggle from the original script has been
  removed — the web UI is now the only control surface.
- If the Pico doesn't show up as a drive, hold BOOTSEL while plugging
  in USB to force it into bootloader mode, then re-flash.
- The page auto-refreshes every 3 seconds while running so you can see
  elapsed/remaining time without doing anything.
