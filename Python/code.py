# SPDX-License-Identifier: MIT
# Keyboard Jiggler w/ Web Interface
# Raspberry Pi Pico 2 W + CircuitPython
#
# Rename this file to code.py on the CIRCUITPY drive.
# Requires settings.toml with CIRCUITPY_WIFI_SSID / CIRCUITPY_WIFI_PASSWORD.
# Requires lib/: adafruit_httpserver, adafruit_hid

import os
import time
import board
import digitalio
import wifi
import ipaddress
import socketpool
import microcontroller
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
from adafruit_httpserver import Server, Request, Response, Redirect, POST


def url_decode(value):
    """Manually decode application/x-www-form-urlencoded text.

    Some adafruit_httpserver versions return form field values without
    percent/plus decoding applied, so we do it ourselves rather than
    depend on the library's behavior."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeError:
            value = value.decode("latin-1")
    text = value.replace("+", " ")
    if "%" not in text:
        return text
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "%" and i + 2 < n:
            hex_pair = text[i + 1 : i + 3]
            try:
                out.append(chr(int(hex_pair, 16)))
                i += 3
                continue
            except ValueError:
                pass
        out.append(ch)
        i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# HID setup
# ---------------------------------------------------------------------------
keyboard = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

# Map friendly names to Keycode constants. Extend this if you need more keys.
KEY_MAP = {
    "SPACE": Keycode.SPACE,
    "SPC": Keycode.SPACE,
    " ": Keycode.SPACE,
    "SHIFT": Keycode.SHIFT,
    "CTRL": Keycode.CONTROL,
    "ALT": Keycode.ALT,
    "TAB": Keycode.TAB,
    "ENTER": Keycode.ENTER,
    "UP": Keycode.UP_ARROW,
    "DOWN": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW,
}

# Map friendly names to mouse buttons. MOUSE1/2/3 match common game/software
# convention for left/right/middle click.
MOUSE_MAP = {
    "MOUSE1": Mouse.LEFT_BUTTON,
    "MOUSE_LEFT": Mouse.LEFT_BUTTON,
    "LMB": Mouse.LEFT_BUTTON,
    "MOUSE2": Mouse.RIGHT_BUTTON,
    "MOUSE_RIGHT": Mouse.RIGHT_BUTTON,
    "RMB": Mouse.RIGHT_BUTTON,
    "MOUSE3": Mouse.MIDDLE_BUTTON,
    "MOUSE_MIDDLE": Mouse.MIDDLE_BUTTON,
    "MMB": Mouse.MIDDLE_BUTTON,
}


def resolve_key(raw):
    """Turn a user-typed key name into a Keycode. Returns None if unknown."""
    token = raw.strip().upper()
    if token in KEY_MAP:
        return KEY_MAP[token]
    if len(token) == 1:
        # single letters/digits map directly, e.g. "W" -> Keycode.W
        attr = token
        return getattr(Keycode, attr, None)
    return getattr(Keycode, token, None)


def resolve_input(raw):
    """Resolve a user-typed name to ('keyboard', keycode) or ('mouse',
    button). Returns None if unrecognized."""
    token = raw.strip().upper()
    if token in MOUSE_MAP:
        return ("mouse", MOUSE_MAP[token])
    keycode = resolve_key(raw)
    if keycode is not None:
        return ("keyboard", keycode)
    return None


def press_input(cmd):
    if cmd["device"] == "mouse":
        mouse.press(cmd["key"])
    else:
        keyboard.press(cmd["key"])


def release_input(cmd):
    if cmd["device"] == "mouse":
        mouse.release(cmd["key"])
    else:
        keyboard.release(cmd["key"])


# ---------------------------------------------------------------------------
# Optional external toggle button
# ---------------------------------------------------------------------------
# Wire a momentary button between physical pin 2 (GP1) and physical pin 3
# (GND) -- they're adjacent, matching a 2-pin connector. No resistor needed:
# the internal pull-up keeps GP1 HIGH when the button is open, and pressing
# it pulls the pin to GND (LOW). Set BUTTON_PIN to None to disable this
# entirely and rely on the web UI only.
BUTTON_PIN = board.GP1
BUTTON_DEBOUNCE_SECONDS = 0.05

button = None
if BUTTON_PIN is not None:
    button = digitalio.DigitalInOut(BUTTON_PIN)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP

button_raw_state = True       # last raw reading (True = released, pulled high)
button_stable_state = True    # debounced state
button_last_change = 0        # monotonic time of the last raw-state change


# ---------------------------------------------------------------------------
# Jiggler state
# ---------------------------------------------------------------------------
class JigglerState:
    def __init__(self):
        self.running = False
        self.commands = []          # list of dicts: key,label,mode,duration,pause
        self.total_runtime = 1200   # seconds (default 20 min)
        self.start_time = None
        self.cmd_index = 0
        self.phase = "press"        # "press" or "pause"
        self.phase_end = None       # monotonic time, None = no timeout (continuous)
        self.last_error = ""
        self.last_key_label = ""
        self.tap_interval = 0.15    # seconds between press/release cycles in TAP mode
        self.next_tap = 0           # monotonic time of next tap, used in TAP mode
        # raw text so the web form can redisplay exactly what was typed
        self.commands_text = "W, 5, 2\nA, 3, 4\nS, 5, 2\nD, 3, 4\nE, 1, 3, TAP"

    def elapsed(self):
        if not self.running or self.start_time is None:
            return 0
        return time.monotonic() - self.start_time

    def remaining(self):
        if not self.running:
            return 0
        return max(0, self.total_runtime - self.elapsed())


state = JigglerState()


def parse_commands(text):
    """Parse the textarea contents into a list of command dicts.
    Raises ValueError with a human-readable message on bad input."""
    parsed = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        # Some form-encoding implementations don't fully percent-decode
        # punctuation (commas can arrive as literal "%2C"). Normalize
        # that before splitting.
        normalized = line.replace("%2C", ",").replace("%2c", ",")
        parts = [p.strip() for p in normalized.split(",")]
        if len(parts) < 2:
            # Fallback: accept space-separated tokens too, in case commas
            # were lost entirely (e.g. "W C TAP" instead of "W, C, TAP").
            ws_parts = normalized.split()
            if len(ws_parts) >= 2:
                parts = ws_parts
            else:
                print("Command parse debug - raw line:", repr(line))
                raise ValueError(
                    "Line %d: need at least 'KEY, SECONDS' or 'KEY, C'" % lineno
                )
        key_label = parts[0]
        resolved = resolve_input(key_label)
        if resolved is None:
            raise ValueError("Line %d: unknown key '%s'" % (lineno, key_label))
        device, keycode = resolved

        mode_token = parts[1].strip().upper()
        if mode_token == "C":
            action = "hold"
            if len(parts) > 2 and parts[2] != "":
                action_token = parts[2].strip().upper()
                if action_token not in ("HOLD", "TAP"):
                    raise ValueError(
                        "Line %d: mode must be HOLD or TAP, got '%s'" % (lineno, parts[2])
                    )
                action = action_token.lower()
            parsed.append(
                {
                    "key": keycode,
                    "device": device,
                    "label": key_label.upper(),
                    "mode": "continuous",
                    "duration": None,
                    "pause": 0,
                    "action": action,
                }
            )
            continue

        try:
            duration = float(parts[1])
        except ValueError:
            raise ValueError("Line %d: '%s' is not a number or 'C'" % (lineno, parts[1]))
        pause = 0.0
        if len(parts) > 2 and parts[2] != "":
            try:
                pause = float(parts[2])
            except ValueError:
                raise ValueError("Line %d: pause '%s' is not a number" % (lineno, parts[2]))
        action = "hold"
        if len(parts) > 3 and parts[3] != "":
            action_token = parts[3].strip().upper()
            if action_token not in ("HOLD", "TAP"):
                raise ValueError(
                    "Line %d: mode must be HOLD or TAP, got '%s'" % (lineno, parts[3])
                )
            action = action_token.lower()

        parsed.append(
            {
                "key": keycode,
                "device": device,
                "label": key_label.upper(),
                "mode": "timed",
                "duration": duration,
                "pause": pause,
                "action": action,
            }
        )

    if not parsed:
        raise ValueError("No commands entered.")
    return parsed


# ---------------------------------------------------------------------------
# Jiggler control (non-blocking state machine, advanced from the main loop)
# ---------------------------------------------------------------------------
def release_all():
    try:
        keyboard.release_all()
    except Exception:  # pylint: disable=broad-except
        pass
    try:
        mouse.release_all()
    except Exception:  # pylint: disable=broad-except
        pass


def begin_command(idx):
    cmd = state.commands[idx]
    now = time.monotonic()
    if cmd["action"] == "tap":
        press_input(cmd)
        release_input(cmd)
        state.next_tap = now + state.tap_interval
    else:
        press_input(cmd)
    state.last_key_label = cmd["label"] + (" (tap)" if cmd["action"] == "tap" else "")
    state.phase = "press"
    if cmd["mode"] == "continuous":
        state.phase_end = None
    else:
        state.phase_end = now + cmd["duration"]


def end_press(idx):
    cmd = state.commands[idx]
    release_input(cmd)  # no-op if already released (TAP mode)
    state.phase = "pause"
    state.phase_end = time.monotonic() + cmd["pause"]


def start_jiggler():
    if not state.commands:
        state.last_error = "Add at least one command before starting."
        return False
    state.start_time = time.monotonic()
    state.cmd_index = 0
    state.running = True
    state.last_error = ""
    begin_command(0)
    return True


def stop_jiggler():
    release_all()
    state.running = False
    state.phase_end = None


def do_toggle():
    """Shared start/stop toggle used by both the web button and the
    physical button, so they always agree on state."""
    if state.running:
        stop_jiggler()
    else:
        start_jiggler()


def check_button():
    """Call every loop iteration. Non-blocking debounce: a raw reading
    has to hold steady for BUTTON_DEBOUNCE_SECONDS before it counts,
    and only the release-to-press edge triggers a toggle."""
    global button_raw_state, button_stable_state, button_last_change

    if button is None:
        return

    now = time.monotonic()
    reading = button.value

    if reading != button_raw_state:
        button_raw_state = reading
        button_last_change = now

    if now - button_last_change >= BUTTON_DEBOUNCE_SECONDS:
        if reading != button_stable_state:
            button_stable_state = reading
            if reading is False:  # HIGH (released) -> LOW (pressed)
                do_toggle()


def tick():
    """Call every loop iteration. Advances the jiggler without blocking."""
    if not state.running:
        return

    now = time.monotonic()

    if now - state.start_time >= state.total_runtime:
        stop_jiggler()
        return

    cmd = state.commands[state.cmd_index]

    if state.phase == "press":
        if cmd["action"] == "tap" and now >= state.next_tap:
            press_input(cmd)
            release_input(cmd)
            state.next_tap = now + state.tap_interval
        if cmd["mode"] != "continuous" and state.phase_end is not None and now >= state.phase_end:
            end_press(state.cmd_index)
    elif state.phase == "pause":
        if state.phase_end is not None and now >= state.phase_end:
            state.cmd_index = (state.cmd_index + 1) % len(state.commands)
            begin_command(state.cmd_index)


# ---------------------------------------------------------------------------
# Wi-Fi + web server
# ---------------------------------------------------------------------------
print("Connecting to WiFi...")

# Optional static IP. Set these in settings.toml to use a fixed address
# instead of DHCP: STATIC_IP, STATIC_NETMASK, STATIC_GATEWAY, and
# optionally STATIC_DNS. If STATIC_IP isn't set, DHCP is used as normal.
static_ip = os.getenv("STATIC_IP")
static_ip_applied = False


def apply_static_ip():
    wifi.radio.set_ipv4_address(
        ipv4=ipaddress.IPv4Address(static_ip),
        netmask=ipaddress.IPv4Address(os.getenv("STATIC_NETMASK", "255.255.255.0")),
        gateway=ipaddress.IPv4Address(os.getenv("STATIC_GATEWAY")),
        ipv4_dns=ipaddress.IPv4Address(os.getenv("STATIC_DNS"))
        if os.getenv("STATIC_DNS")
        else None,
    )


if static_ip:
    # Most boards want the static address set before connect(); a few
    # need it set after. Try before first, fall back to after.
    try:
        apply_static_ip()
        static_ip_applied = True
    except Exception as err:  # pylint: disable=broad-except
        print("Static IP before connect failed, will retry after connect:", err)

wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))

if static_ip and not static_ip_applied:
    try:
        apply_static_ip()
        static_ip_applied = True
    except Exception as err:  # pylint: disable=broad-except
        print("Static IP after connect also failed, staying on DHCP:", err)

print("Connected. IP:", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

RUNTIME_PRESETS = [
    ("10 min", 600),
    ("15 min", 900),
    ("20 min", 1200),
    ("30 min", 1800),
    ("1 hour", 3600),
    ("2 hours", 7200),
    ("4 hours", 14400),
]


def fmt_hms(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return "%dh %dm %ds" % (h, m, s)
    if m:
        return "%dm %ds" % (m, s)
    return "%ds" % s


def render_page():
    status = "RUNNING" if state.running else "STOPPED"
    status_color = "#2ecc71" if state.running else "#e74c3c"
    elapsed_txt = fmt_hms(state.elapsed())
    remaining_txt = fmt_hms(state.remaining())
    current = state.last_key_label if state.running else "-"
    error_html = ""
    if state.last_error:
        error_html = '<p class="error">%s</p>' % state.last_error

    preset_buttons = "".join(
        '<button type="button" class="preset" '
        "onclick=\"document.getElementById('runtime').value=%d\">%s</button>"
        % (secs, label)
        for label, secs in RUNTIME_PRESETS
    )

    refresh_tag = '<meta http-equiv="refresh" content="3">' if state.running else ""

    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{refresh_tag}
<title>Pico Jiggler</title>
<style>
  body {{ font-family: sans-serif; background:#1e1e1e; color:#eee; margin:0; padding:20px; }}
  .card {{ background:#2b2b2b; border-radius:8px; padding:20px; max-width:520px; margin:0 auto 16px auto; }}
  h1 {{ font-size:1.4rem; margin-top:0; }}
  .status {{ display:inline-block; padding:4px 12px; border-radius:4px; font-weight:bold; color:#111; background:{status_color}; }}
  textarea {{ width:100%; box-sizing:border-box; height:140px; font-family:monospace; font-size:0.95rem;
              background:#111; color:#0f0; border:1px solid #444; border-radius:4px; padding:8px; }}
  input[type=number] {{ width:120px; padding:6px; font-size:1rem; background:#111; color:#eee; border:1px solid #444; border-radius:4px; }}
  button {{ cursor:pointer; border:none; border-radius:4px; padding:10px 18px; font-size:1rem; margin:4px 4px 4px 0; }}
  .toggle {{ background:{toggle_color}; color:#111; font-weight:bold; }}
  .save {{ background:#3498db; color:#fff; }}
  .preset {{ background:#444; color:#eee; font-size:0.85rem; padding:6px 10px; }}
  .row {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:8px; }}
  .error {{ color:#ff6b6b; font-weight:bold; }}
  label {{ display:block; margin-top:14px; margin-bottom:4px; font-size:0.9rem; color:#aaa; }}
  small {{ color:#888; }}
</style>
</head>
<body>

<div class="card">
  <h1>Pico Keyboard Jiggler</h1>
  <p>Status: <span class="status">{status}</span></p>
  <p>Current key: <b>{current}</b><br>
     Elapsed: {elapsed_txt} &nbsp;|&nbsp; Remaining: {remaining_txt}</p>
  {error_html}
  <form method="POST" action="/toggle">
    <button class="toggle" type="submit">{toggle_label}</button>
  </form>
</div>

<div class="card">
  <form method="POST" action="/update">
    <label>Commands (one per line: KEY, SECONDS, PAUSE, MODE)</label>
    <textarea name="commands">{commands_text}</textarea>
    <small>
      "W, 5, 2" holds W for 5s then pauses 2s (MODE defaults to HOLD).<br>
      "E, 1, 3, TAP" taps E repeatedly for 1s, pauses 3s &mdash; use TAP for
      pickup/interact keys you want to toss rather than hold.<br>
      "A, C" holds A continuously. "A, C, TAP" taps A continuously.<br>
      Mouse buttons: MOUSE1/LMB (left), MOUSE2/RMB (right), MOUSE3/MMB
      (middle) &mdash; e.g. "MOUSE1, C, TAP" taps left-click continuously.
    </small>

    <label>Tap interval (seconds between press/release in TAP mode)</label>
    <input type="number" step="any" min="0.05" name="tap_interval" value="{tap_interval}">

    <label>Total run time (seconds)</label>
    <div class="row">
      <input type="number" id="runtime" step="any" name="runtime" min="1" value="{total_runtime}">
      <span>= {runtime_human}</span>
    </div>
    <div class="row">
      {preset_buttons}
    </div>

    <div class="row">
      <button class="save" type="submit">Save Settings</button>
    </div>
  </form>
</div>

</body>
</html>
""".format(
        refresh_tag=refresh_tag,
        status_color=status_color,
        toggle_color="#e74c3c" if state.running else "#2ecc71",
        status=status,
        current=current,
        elapsed_txt=elapsed_txt,
        remaining_txt=remaining_txt,
        error_html=error_html,
        toggle_label="STOP" if state.running else "START",
        commands_text=state.commands_text,
        tap_interval=state.tap_interval,
        total_runtime=int(state.total_runtime),
        runtime_human=fmt_hms(state.total_runtime),
        preset_buttons=preset_buttons,
    )
    return html


@server.route("/")
def index(request: Request):
    return Response(request, render_page(), content_type="text/html")


@server.route("/toggle", POST)
def toggle(request: Request):
    try:
        do_toggle()
    except Exception as err:  # pylint: disable=broad-except
        state.last_error = "Toggle failed: %s: %s" % (type(err).__name__, err)
    return Redirect(request, "/")


@server.route("/update", POST)
def update(request: Request):
    try:
        commands_text = url_decode(request.form_data.get("commands", ""))
        runtime_raw = url_decode(request.form_data.get("runtime", ""))
        tap_interval_raw = url_decode(request.form_data.get("tap_interval", ""))
        print("Update received - commands:", repr(commands_text))

        new_commands = parse_commands(commands_text)
        new_runtime = float(runtime_raw)
        if new_runtime <= 0:
            raise ValueError("Runtime must be greater than 0.")
        new_tap_interval = float(tap_interval_raw) if tap_interval_raw else state.tap_interval
        if new_tap_interval < 0.05:
            raise ValueError("Tap interval must be at least 0.05 seconds.")
    except ValueError as err:
        state.last_error = str(err)
        return Redirect(request, "/")
    except Exception as err:  # pylint: disable=broad-except
        # Anything unexpected (bad form encoding, etc.) still gets a
        # visible response instead of silently dropping the request.
        state.last_error = "Save failed: %s: %s" % (type(err).__name__, err)
        return Redirect(request, "/")

    # Save. If currently running, stop first so the new settings take
    # effect cleanly on the next START.
    if state.running:
        stop_jiggler()

    state.commands = new_commands
    state.commands_text = commands_text
    state.total_runtime = new_runtime
    state.tap_interval = new_tap_interval
    state.last_error = ""
    return Redirect(request, "/")


# Parse the default commands at boot so START works immediately.
try:
    state.commands = parse_commands(state.commands_text)
except ValueError as err:
    state.last_error = str(err)

print("Starting server...")
try:
    server.start(str(wifi.radio.ipv4_address))
    print("Listening on http://%s" % wifi.radio.ipv4_address)
except OSError as err:
    print("Server failed to start:", err)
    time.sleep(5)
    microcontroller.reset()

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    try:
        server.poll()
        check_button()
        tick()
    except Exception as e:  # pylint: disable=broad-except
        try:
            import traceback

            traceback.print_exception(e)
        except ImportError:
            print("Loop error:", e)
        continue
