# Alcohol Marker Production Line Simulator
### SRH Advanced Programming Project — June 2026

A simulated manufacturing production line for alcohol markers, built with Python, Flask, InfluxDB, Grafana, and Docker.

---

## Project structure

```
alcohol-marker-sim/
├── docker-compose.yml          ← starts everything
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                 ← FSM + Flask API
├── frontend/
│   └── index.html              ← HMI (open in browser)
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── influxdb.yml
        └── dashboards/
            ├── dashboard.yml
            └── alcohol_marker.json
```

---

## Production stages

| # | Stage           | Defect condition                          |
|---|-----------------|-------------------------------------------|
| 1 | Tip Insertion   | Nib holder misaligned (8% chance)         |
| 2 | Alcohol Fill    | Ethanol < 70% or > 90% concentration      |
| 3 | Body Assembly   | Barrel click-lock failed (6% chance)      |
| 4 | Cap & QC Check  | Cap absent or leak test failed (10% chance)|

---

## FSM states

```
IDLE ──[Start]──► RUNNING ──[Defect]──► FAULTED
 ▲                    │                     │
 └────[Stop]──────────┘                     │
 └────────────────[Reset]───────────────────┘
```

---

## Setup on Windows

### 1. Install Docker Desktop
Download from https://www.docker.com/products/docker-desktop/
During install, make sure **WSL 2** backend is enabled (it's the default).

### 2. Clone / download this project
Place the folder somewhere easy, e.g. `C:\Users\YourName\alcohol-marker-sim`

### 3. Start everything
Open **PowerShell** or **Command Prompt**, navigate to the project folder:

```powershell
cd C:\Users\YourName\alcohol-marker-sim
docker compose up --build
```

First run downloads images (~1 GB). Wait until you see:
```
backend  | [Server] Alcohol Marker Production Line – backend starting on port 5000
```

### 4. Open the HMI
Open `frontend/index.html` directly in your browser (double-click the file).

### 5. Open Grafana
Go to http://localhost:3000
- Username: `admin`
- Password: `admin`
- Dashboard: **Alcohol Marker Production Line** (auto-loaded)

### 6. Stop everything
```powershell
docker compose down
```

---

## API endpoints

| Method | Endpoint  | Description                        |
|--------|-----------|------------------------------------|
| GET    | /status   | Returns full machine state as JSON |
| POST   | /start    | IDLE → RUNNING                     |
| POST   | /stop     | RUNNING → IDLE                     |
| POST   | /reset    | FAULTED → IDLE (clears counters)   |

---

## Parameters sent to Grafana

- `fsm_state` — machine state string (IDLE / RUNNING / FAULTED)
- `parts_produced` — total good markers made
- `parts_defective` — total rejected markers
- `temperature_c` — simulated process temperature in °C
- `ethanol_pct` — alcohol concentration of fill (key quality parameter)
- `cycle_time_s` — time in seconds for the last complete marker
- `stage` — current active stage number (1–4)
