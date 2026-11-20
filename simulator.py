import time
import random
import json
import threading
import asyncio
import requests
import websockets
import sys

# Backend URL configuration
BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"
ROBOT_ID = sys.argv[1] if len(sys.argv) > 1 else "ROBOT-01"

# Credentials for the robot owner account
USERNAME = "Jashwanth"
PASSWORD = "theflyingdutchman"

# Global state control for emergency halt
is_halted = threading.Event()  # False by default (running)

def get_auth_token():
    """Logs in to FastAPI OAuth2 endpoint and retrieves a Bearer access token."""
    login_url = f"{BASE_URL}/auth/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(login_url, data=payload)
        if response.status_code == 401:
            print("[AUTH ERROR] Invalid username or password. Check USERNAME/PASSWORD.")
            return None
        response.raise_for_status()
        token = response.json().get("access_token")
        print("[AUTH] Successfully acquired access token.")
        return token
    except requests.exceptions.RequestException as e:
        print(f"[AUTH ERROR] Failed to connect to auth endpoint: {e}")
        return None

def ensure_robot_registered(headers: dict):
    """Ensures the robot exists in the database under the current user."""
    check_url = f"{BASE_URL}/robots/{ROBOT_ID}"
    try:
        res = requests.get(check_url, headers=headers)
        if res.status_code == 200:
            print(f"[INIT] Robot {ROBOT_ID} is verified and ready.")
            return True
        elif res.status_code in (404,):
            print(f"[INIT] Robot {ROBOT_ID} not found. Registering it now...")
            reg_url = f"{BASE_URL}/robots/register"
            reg_payload = {
                "robot_id": ROBOT_ID,
                "Model": "KUKA-KR6",
                "Type": "Articulated Arm",
                "Location": "Assembly Line 1"
            }
            reg_res = requests.post(reg_url, json=reg_payload, headers=headers)
            if reg_res.status_code in (200, 201):
                print(f"[INIT] Successfully registered {ROBOT_ID}.")
                return True
            else:
                print(f"[INIT ERROR] Failed to register robot: {reg_res.text}")
                return False
        else:
            print(f"[INIT ERROR] Unexpected status when checking robot: {res.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[INIT ERROR] Could not reach backend: {e}")
        return False

# Base sensor state for realistic continuous drift
current_state = {
    "temperature": 45.0,
    "vibration": 0.45,
    "current_draw": 5.5,
    "proximity": 1.2
}

def generate_sensor_payload(robot_id: str):
    """Simulates realistic drifting telemetry with thresholds."""
    global current_state

    # Drift values slightly per cycle
    current_state["temperature"] = round(
        max(30.0, min(95.0, current_state["temperature"] + random.uniform(-1.5, 1.8))), 2
    )
    current_state["vibration"] = round(
        max(0.05, min(3.5, current_state["vibration"] + random.uniform(-0.08, 0.1))), 3
    )
    current_state["current_draw"] = round(
        max(1.0, min(18.0, current_state["current_draw"] + random.uniform(-0.4, 0.45))), 2
    )
    current_state["proximity"] = round(
        max(0.1, min(5.0, current_state["proximity"] + random.uniform(-0.2, 0.2))), 2
    )

    # Determine status based on thresholds
    temp = current_state["temperature"]
    vib = current_state["vibration"]
    curr = current_state["current_draw"]

    if temp > 85.0 or vib > 2.5 or curr > 15.0:
        status = "ERROR"
    elif temp > 72.0 or vib > 1.6 or curr > 12.0:
        status = "WARNING"
    else:
        status = "NORMAL"

    return {
        "robot_id": robot_id,
        "temperature": temp,
        "vibration": vib,
        "current_draw": curr,
        "proximity": current_state["proximity"],
        "status": status
    }

# ----------------- Downlink WebSocket Listener ----------------- #

async def websocket_command_listener():
    """Listens continuously for commands pushed from the FastAPI backend."""
    ws_endpoint = f"{WS_URL}/ws/robots/{ROBOT_ID}"
    
    while True:
        try:
            async with websockets.connect(ws_endpoint) as ws:
                print(f"[WS DOWNLINK] Connected to {ws_endpoint}. Listening for actuation commands...")
                while True:
                    msg = await ws.recv()
                    print(f"\n>>> [WS RAW INCOMING]: {msg}")  # Diagnoses raw incoming packets

                    if isinstance(msg, str):
                        try:
                            data = json.loads(msg)
                        except json.JSONDecodeError:
                            data = {"action": msg}
                    else:
                        data = msg

                    # Handle nested or double-encoded JSON
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            pass

                    # Extract action regardless of case or key name
                    action = str(data.get("action", data.get("command", ""))).strip().upper()
                    reason = data.get("reason", "No reason provided")
                    issued_by = data.get("issued_by", "Supervisor")

                    print(f">>> [PARSED ACTION]: '{action}'")

                    if any(keyword in action for keyword in ["STOP", "EMERGENCY", "HALT"]):
                        is_halted.set()
                        print(f"\n🚨 [ACTUATION TRIGGERED] EMERGENCY HALT ACTIVATED!")
                        print(f"   Issued by: {issued_by} | Reason: {reason}")
                        print(f"   Motors disengaged. Telemetry transmission paused.\n")

                    elif any(keyword in action for keyword in ["RESUME", "START", "RESET"]):
                        is_halted.clear()
                        print(f"\n✅ [ACTUATION TRIGGERED] RESUME COMMAND RECEIVED.")
                        print(f"   Issued by: {issued_by} | Machine restarted.\n")

        except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError):
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[WS LISTENER ERROR]: {e}")
            await asyncio.sleep(2)

def start_ws_listener_thread():
    """Starts the asyncio event loop for WebSockets in a background daemon thread."""
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(websocket_command_listener())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# ----------------- Main Telemetry Loop ----------------- #

def run_simulator(interval_seconds: int = 2):
    """Main transmission loop."""
    token = get_auth_token()
    if not token:
        print("[SHUTDOWN] Simulator cannot proceed without authentication.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Verify or register robot
    if not ensure_robot_registered(headers):
        print("[SHUTDOWN] Could not verify/register robot on backend.")
        return

    # Start the background command listener
    start_ws_listener_thread()

    endpoint = f"{BASE_URL}/robots/{ROBOT_ID}/sensor-data"
    print(f"\n--- Streaming telemetry for {ROBOT_ID} every {interval_seconds}s (Ctrl+C to stop) ---")

    while True:
        # Check if the robot has been emergency halted
        if is_halted.is_set():
            time.sleep(1)
            continue

        payload = generate_sensor_payload(ROBOT_ID)

        try:
            response = requests.post(endpoint, json=payload, headers=headers)

            if response.status_code == 401:
                print("[WARN] Access token expired. Re-authenticating...")
                token = get_auth_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    continue
                else:
                    time.sleep(5)
                    continue

            if response.status_code in (200, 201):
                status_symbol = "✓" if payload["status"] == "NORMAL" else "!"
                print(
                    f"[{status_symbol} {payload['status']:<7}] "
                    f"Temp: {payload['temperature']:>5.2f}°C | "
                    f"Vib: {payload['vibration']:>5.3f} mm/s | "
                    f"Current: {payload['current_draw']:>5.2f} A | "
                    f"Prox: {payload['proximity']:>4.2f} m"
                )
            else:
                print(f"[REJECTED {response.status_code}]: {response.text}")

        except requests.exceptions.ConnectionError:
            print("[SERVER OFFLINE] FastAPI is not reachable. Retrying in 4s...")
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR]: {e}")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_simulator(interval_seconds=2)