"""
Alcohol Marker Production Line Simulator
SRH Advanced Programming Project

Author: [Your Name]
AI Assistance: Claude (Anthropic) - see appendix for prompts and corrections

Production stages:
  1. Tip Insertion   - polyester/felt tip is pressed into the nib holder
  2. Alcohol Fill    - ethanol-based ink is injected into the reservoir
  3. Body Assembly   - reservoir is inserted into the outer barrel
  4. Cap & QC        - cap is fitted; final quality check runs

FSM states:  IDLE → RUNNING → FAULTED → IDLE
"""

import os
import time
import random
import logging
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ── Logging ──────────────────────────────────────────────────────────────────
# Use the logging module (flushed line-by-line) instead of bare print() so that
# every message reliably shows up in `docker compose logs`.
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("marker-line")

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ── InfluxDB connection ───────────────────────────────────────────────────────
INFLUX_URL    = os.getenv("INFLUX_URL",    "http://localhost:8086")
INFLUX_TOKEN  = os.getenv("INFLUX_TOKEN",  "my-super-secret-token")
INFLUX_ORG    = os.getenv("INFLUX_ORG",    "srh")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "markers")

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api     = influx_client.write_api(write_options=SYNCHRONOUS)

# One-time connectivity check so a bad URL/token surfaces at startup
# instead of silently on the first write.
try:
    if influx_client.ping():
        log.info("InfluxDB reachable at %s (org=%s bucket=%s)",
                 INFLUX_URL, INFLUX_ORG, INFLUX_BUCKET)
    else:
        log.error("InfluxDB ping returned False – check URL/token/org")
except Exception as exc:
    log.error("InfluxDB not reachable at %s: %s", INFLUX_URL, exc)

# ── Production line state (shared, protected by a lock) ──────────────────────
state_lock = threading.Lock()

machine = {
    "fsm_state":        "IDLE",      # IDLE | RUNNING | FAULTED
    "current_stage":    0,           # 1–4 while running, 0 when idle
    "parts_produced":   0,
    "parts_defective":  0,
    "fault_reason":     "",
    "temperature":      22.0,        # °C  (simulated ambient)
    "ethanol_pct":      0.0,         # % concentration (filled at stage 2)
    "cycle_time_s":     0.0,         # seconds for last complete cycle
    "running":          False,       # background thread active?
}

# Stage names shown in the HMI
STAGE_NAMES = {
    1: "Tip Insertion",
    2: "Alcohol Fill",
    3: "Body Assembly",
    4: "Cap & QC Check",
}

# ── Defect detection logic ────────────────────────────────────────────────────
def run_stage(stage: int) -> dict:
    """
    Simulate one production stage.
    Returns {"ok": bool, "reason": str, "ethanol_pct": float}
    Each stage takes a realistic random duration and can raise a fault.
    """
    time.sleep(random.uniform(1.0, 2.5))   # realistic stage cycle time

    temp_spike = random.uniform(-1.5, 3.0)

    with state_lock:
        machine["temperature"] = round(22.0 + temp_spike, 1)
        machine["current_stage"] = stage

    if stage == 1:
        # Tip insertion: tip might be missing or mis-aligned
        if random.random() < 0.08:
            return {"ok": False, "reason": "Tip not seated – nib holder misaligned", "ethanol_pct": 0.0}

    elif stage == 2:
        # Alcohol fill: concentration must be 70–90 % for quality markers
        ethanol = round(random.uniform(60.0, 95.0), 1)
        with state_lock:
            machine["ethanol_pct"] = ethanol
        if ethanol < 70.0:
            return {"ok": False, "reason": f"Ethanol too low ({ethanol}%) – minimum 70%", "ethanol_pct": ethanol}
        if ethanol > 90.0:
            return {"ok": False, "reason": f"Ethanol too high ({ethanol}%) – maximum 90%", "ethanol_pct": ethanol}
        return {"ok": True, "reason": "", "ethanol_pct": ethanol}

    elif stage == 3:
        # Body assembly: barrel might not click into place
        if random.random() < 0.06:
            return {"ok": False, "reason": "Barrel click-lock failed – body not fully seated", "ethanol_pct": 0.0}

    elif stage == 4:
        # Cap & QC: cap may be missing or leak test fails
        if random.random() < 0.10:
            return {"ok": False, "reason": "Cap absent or loose – leak test failed", "ethanol_pct": 0.0}

    return {"ok": True, "reason": "", "ethanol_pct": machine["ethanol_pct"]}

# ── InfluxDB writer ───────────────────────────────────────────────────────────
def write_to_influx():
    """Write current machine state as one data point to InfluxDB."""
    with state_lock:
        snap = dict(machine)

    try:
        point = (
            Point("production")
            .tag("machine", "alcohol-marker-line-1")
            .field("fsm_state",       snap["fsm_state"])
            .field("stage",           snap["current_stage"])
            .field("parts_produced",  snap["parts_produced"])
            .field("parts_defective", snap["parts_defective"])
            .field("temperature_c",   snap["temperature"])
            .field("ethanol_pct",     snap["ethanol_pct"])
            .field("cycle_time_s",    snap["cycle_time_s"])
            .time(datetime.now(timezone.utc), WritePrecision.S)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        log.info("Influx write OK  state=%s stage=%s produced=%s defective=%s",
                 snap["fsm_state"], snap["current_stage"],
                 snap["parts_produced"], snap["parts_defective"])
    except Exception as exc:
        log.error("Influx write FAILED: %s", exc)

# ── Telemetry heartbeat (runs for the whole life of the process) ─────────────
HEARTBEAT_SECONDS = 2

def telemetry_heartbeat():
    """
    Write the current machine state to InfluxDB on a fixed interval, whether the
    line is running or idle. This keeps fresh data in the dashboard at all times
    so panels never fall back to "No data" when the machine is sitting idle.
    """
    while True:
        write_to_influx()
        time.sleep(HEARTBEAT_SECONDS)

# ── Production loop (runs in background thread) ───────────────────────────────
def production_loop():
    """
    Continuously produces markers until stopped or faulted.
    Each iteration = one full marker (4 stages).
    """
    log.info("[Machine] Production loop started")

    while True:
        with state_lock:
            if not machine["running"]:
                break
            if machine["fsm_state"] != "RUNNING":
                break

        cycle_start = time.time()
        defective   = False
        fault_msg   = ""

        for stage in range(1, 5):
            with state_lock:
                if not machine["running"]:
                    break

            result = run_stage(stage)
            write_to_influx()

            if not result["ok"]:
                defective = True
                fault_msg = result["reason"]
                log.info("[Stage %s] DEFECT: %s", stage, fault_msg)
                break

        else:
            # All 4 stages passed — good part
            cycle_time = round(time.time() - cycle_start, 2)
            with state_lock:
                machine["parts_produced"] += 1
                machine["cycle_time_s"]   = cycle_time
                machine["current_stage"]  = 0
            log.info("[Machine] Marker #%s complete  (%ss)",
                     machine["parts_produced"], cycle_time)
            write_to_influx()
            continue

        # A stage failed — count defect, transition to FAULTED
        if defective:
            with state_lock:
                machine["parts_defective"] += 1
                machine["fsm_state"]       = "FAULTED"
                machine["fault_reason"]    = fault_msg
                machine["running"]         = False
                machine["current_stage"]   = 0
            write_to_influx()
            log.warning("[Machine] → FAULTED: %s", fault_msg)
            break

        # Stopped by operator mid-cycle
        with state_lock:
            machine["current_stage"] = 0
        write_to_influx()
        break

    log.info("[Machine] Production loop ended")

# ── REST API endpoints ────────────────────────────────────────────────────────

@app.route("/status", methods=["GET"])
def get_status():
    """Return full machine snapshot to the HMI."""
    with state_lock:
        snap = dict(machine)
    snap["stage_name"] = STAGE_NAMES.get(snap["current_stage"], "—")
    return jsonify(snap)

@app.route("/start", methods=["POST"])
def start_machine():
    """IDLE → RUNNING  (rejected if already running or faulted)."""
    with state_lock:
        if machine["fsm_state"] == "RUNNING":
            return jsonify({"ok": False, "message": "Machine is already running"}), 400
        if machine["fsm_state"] == "FAULTED":
            return jsonify({"ok": False, "message": "Machine is faulted – reset first"}), 400
        machine["fsm_state"]   = "RUNNING"
        machine["running"]     = True
        machine["fault_reason"] = ""

    t = threading.Thread(target=production_loop, daemon=True)
    t.start()
    write_to_influx()
    return jsonify({"ok": True, "message": "Production started"})

@app.route("/stop", methods=["POST"])
def stop_machine():
    """RUNNING → IDLE  (graceful stop after current stage)."""
    with state_lock:
        if machine["fsm_state"] != "RUNNING":
            return jsonify({"ok": False, "message": "Machine is not running"}), 400
        machine["running"]   = False
        machine["fsm_state"] = "IDLE"
        machine["current_stage"] = 0
    write_to_influx()
    return jsonify({"ok": True, "message": "Production stopped"})

@app.route("/reset", methods=["POST"])
def reset_machine():
    """FAULTED → IDLE  (clears fault, resets counters)."""
    with state_lock:
        machine["fsm_state"]       = "IDLE"
        machine["running"]         = False
        machine["current_stage"]   = 0
        machine["parts_produced"]  = 0
        machine["parts_defective"] = 0
        machine["fault_reason"]    = ""
        machine["temperature"]     = 22.0
        machine["ethanol_pct"]     = 0.0
        machine["cycle_time_s"]    = 0.0
    write_to_influx()
    return jsonify({"ok": True, "message": "Machine reset"})

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("[Server] Alcohol Marker Production Line – backend starting on port 5000")
    # Continuous telemetry so the dashboard always has fresh data, even when idle.
    threading.Thread(target=telemetry_heartbeat, daemon=True).start()
    log.info("[Server] Telemetry heartbeat started (every %ss)", HEARTBEAT_SECONDS)
    app.run(host="0.0.0.0", port=5000, debug=False)
