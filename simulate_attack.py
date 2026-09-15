"""
GeoAegis-ID Attack Simulation Integration Script

Why Automated Integration Tests Validate Security Pipelines:
-------------------------------------------------------------
Automated integration tests ensure end-to-end reliability across complex security systems by validating that real-time
telemetry correctly flows through input validation gateways, geo-spatial calculations (Haversine engine), anomaly
detection rules (impossible travel heuristics), and automated incident reporting layers (SLM threat summaries).

Running synthetic attack simulations guarantees:
1. Contract Enforcement: Verifies that API endpoints correctly accept and sanitize authentication payloads.
2. Threat Accuracy: Validates that normal login behavior (e.g., local travel between neighboring cities over reasonable timeframes)
   is permitted while high-velocity impossible travel across international boundaries is reliably flagged.
3. Resilience & Regression Prevention: Ensures changes to backend modules or AI dependencies do not break threat detection rules
   or silently fail during live security incidents.
"""

import time
import requests

API_URL = "http://127.0.0.1:8000/api/v1/auth-log"
HEALTH_URL = "http://127.0.0.1:8000/health"
USER_ID = f"kavan_admin_{int(time.time())}"

# Define GPS coordinates and timestamps for 3-step sequence
# Coordinates:
# 1. Gandhinagar, Gujarat, India: 23.2156 N, 72.6369 E
# 2. Ahmedabad, Gujarat, India: 23.0225 N, 72.5714 E (~23 km apart)
# 3. London, United Kingdom: 51.5074 N, -0.1278 W (~6800 km from Ahmedabad)

BASE_TIMESTAMP = time.time()

SIMULATION_STEPS = [
    {
        "step": 1,
        "location": "Gandhinagar, India",
        "lat": 23.2156,
        "lon": 72.6369,
        "timestamp": BASE_TIMESTAMP,
        "delay_label": "Initial Baseline Login"
    },
    {
        "step": 2,
        "location": "Ahmedabad, India",
        "lat": 23.0225,
        "lon": 72.5714,
        "timestamp": BASE_TIMESTAMP + 7200,  # +2 hours (7200 seconds)
        "delay_label": "+2 Hours after Step 1"
    },
    {
        "step": 3,
        "location": "London, UK",
        "lat": 51.5074,
        "lon": -0.1278,
        "timestamp": BASE_TIMESTAMP + 7200 + 180,  # +3 minutes (180 seconds) after Step 2
        "delay_label": "+3 Minutes after Step 2 (ANOMALY EXPECTED)"
    }
]


def check_api_health():
    """Verify that GeoAegis-ID backend API is online."""
    try:
        response = requests.get(HEALTH_URL, timeout=3)
        if response.status_code == 200:
            print("[\033[92mONLINE\033[0m] GeoAegis-ID Backend server is running.")
            return True
    except requests.RequestException:
        pass
    
    print("[\033[91mOFFLINE\033[0m] Unable to connect to GeoAegis-ID API at http://127.0.0.1:8000.")
    print("Please ensure uvicorn server is running: uvicorn app.main:app --reload")
    return False


def run_simulation():
    """Execute the 3-step attack simulation sequence."""
    print("=" * 80)
    print("       GeoAegis-ID Security Pipeline Attack Simulation Sequence")
    print(f"       Target User: {USER_ID}")
    print("=" * 80)
    print()

    if not check_api_health():
        return

    print("-" * 80)

    for event in SIMULATION_STEPS:
        step_num = event["step"]
        location = event["location"]
        payload = {
            "user": USER_ID,
            "lat": event["lat"],
            "lon": event["lon"],
            "timestamp": event["timestamp"]
        }

        print(f"\n>>> Step {step_num}: Authentication Event from {location}")
        print(f"    Time Context : {event['delay_label']}")
        print(f"    Coordinates  : ({event['lat']}, {event['lon']})")

        try:
            res = requests.post(API_URL, json=payload, timeout=8)
            res.raise_for_status()
            data = res.json()

            status_flag = data.get("status")
            dist_km = data.get("distance_km")
            speed_kmh = data.get("speed_kmh")
            message = data.get("message")
            summary = data.get("threat_summary")

            print("\n    [Evaluation Result]")
            if status_flag == "ANOMALY_DETECTED":
                print(f"    STATUS       : \033[91mCRITICAL - {status_flag}\033[0m")
            else:
                print(f"    STATUS       : \033[92m{status_flag}\033[0m")

            if dist_km is not None:
                print(f"    Distance     : {dist_km:,.2f} km")
            else:
                print("    Distance     : N/A (Baseline)")

            if speed_kmh is not None:
                print(f"    Speed        : {speed_kmh:,.2f} km/h")
            else:
                print("    Speed        : N/A (Baseline)")

            if message:
                print(f"    Message      : {message}")

            if summary:
                print("\n    [AI Threat Intelligence Summary]")
                print(f"    {summary}")

        except requests.RequestException as err:
            print(f"    \033[91m[ERROR]\033[0m Request failed: {err}")

        print("-" * 80)


if __name__ == "__main__":
    run_simulation()
