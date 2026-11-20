# 🤖 Industrial IoT Robot Fleet Monitoring & Supervisory Control System

A full-stack, real-time Industrial IoT (IIoT) monitoring and supervisory control portal built with **FastAPI**, **WebSockets**, **SQLite**, **Streamlit**, and a multi-threaded **Python Edge Simulator**.

The system enables authenticated operators and administrators to monitor multi-metric robot telemetry in real time, detect threshold anomalies automatically, manage incident tickets, and execute instant bidirectional **Emergency Stop (E-Stop)** and **Resume** commands down to edge devices.

---

## ✨ Core Features

* **Role-Based Access Control (RBAC) & JWT Authentication:**
  * OAuth2 Bearer token authentication (`POST /auth/login`) powered by `security.py`.
  * **Admin-Only Operator Provisioning:** Public self-registration is locked down; only the designated administrator account can create new operator accounts via the UI or API.
  * **Multi-Tenant Fleet Isolation:** Users only view and control robots registered under their respective accounts.
* **Bidirectional Real-Time Communication (Uplink & Downlink):**
  * **Telemetry Uplink:** Edge devices stream temperature (`°C`), vibration (`mm/s`), current draw (`A`), and proximity (`m`) metrics at configurable intervals.
  * **Actuation Downlink:** Persistent WebSocket connections (`/ws/robots/{robot_id}`) deliver sub-second `EMERGENCY_STOP` and `RESUME` commands directly to the robot controller, immediately halting simulated motor execution.
* **Automated Anomaly & Threshold Engine:**
  * Evaluates incoming sensor payloads against safety thresholds (`NORMAL`, `WARNING`, `ERROR`/`CRITICAL`).
  * Automatically logs incident tickets in SQLite when thresholds are breached and broadcasts live alerts over WebSockets.
* **Interactive Supervisory Dashboard (Streamlit):**
  * Live metric cards and auto-refreshing multi-metric trend charts (`st.fragment`).
  * One-click **Emergency Stop** and **Resume Operations** controls with operator reason logging and visual halt state lockouts.
  * **Incident Management Center:** View active unresolved faults, resolve incidents with a single click, and audit the resolved incident archive.
  * **In-App Fleet Onboarding:** Register new robots directly from the dashboard without needing external API clients.
* **Multi-Robot CLI Edge Simulator:**
  * Simulates realistic continuous sensor drift across four physical metrics.
  * Supports command-line arguments (`<ROBOT_ID> <USERNAME> <PASSWORD>`) to run multiple independent robots and user accounts simultaneously across separate terminals.
---
## 📸 Dashboard Preview

### 1. Fleet Overview & Supervisory Actuation Control
Fleet Overview and E-Stop Control
<img width="1920" height="864" alt="{19B5D3FF-629F-4285-8995-715D04A1495D}" src="https://github.com/user-attachments/assets/bc8e1544-8526-4899-8b34-57b6f7a70bf9" />

### 2. Real-Time Multi-Metric Telemetry Trends
Multi-Metric Telemetry Trends
<img width="1559" height="624" alt="{D280B5A7-9748-48BB-A2B6-D6727D5CFDE8}" src="https://github.com/user-attachments/assets/65d96a3d-b0a8-45cd-85db-ce916340a698" />

### 3. Live Incident Management Center
Incident Management Center
<img width="1524" height="796" alt="{EC47A36F-5F1E-4DDF-B1E4-2886F2A72B61}" src="https://github.com/user-attachments/assets/2cc6b79c-29ff-4e0b-9328-c9d0efaae097" />

### 4. Resolved Incidents Audit Archive
Resolved Incidents Archive
<img width="1023" height="455" alt="af29571c-2798-4f8a-a373-0dd72d580960" src="https://github.com/user-attachments/assets/d562de3d-6d8d-4aa6-ae2d-d2f95b3d41d7" />
### Special features for admin
### 5. Register New Robot
Register New Robot (only for admin user)
<img width="593" height="391" alt="{270B580C-3B85-46C3-9939-3D895D71BA03}" src="https://github.com/user-attachments/assets/a2d28787-2055-4788-bc84-d281815fca20" />

### 6.  Admin: Create Operator
Admin: Create Operator (only for admin)
<img width="327" height="603" alt="{B2FFED71-D9F4-40D7-838B-DCC54D583859}" src="https://github.com/user-attachments/assets/66415a8c-4bea-4586-9297-ea3b4b5de23a" />

## 📈 Version History & Evolution

### **Version 2.0 (Current — Full Supervisory Control & Multi-User Portal)**
* **Bidirectional WebSocket Downlink:** Added an asynchronous background WebSocket listener (`websockets` + `threading.Event`) in `simulator.py` to receive real-time actuation commands (`EMERGENCY_STOP` / `RESUME`) and halt telemetry transmission immediately.
* **Resilient Connection Management:** Hardened FastAPI's `ConnectionManager` to safely handle client disconnections without triggering `RuntimeError` or `KeyError` crashes during active broadcasts.
* **Dashboard Supervisory Controls:** Integrated **Emergency Stop**, **Resume Operations**, and halt-state warning banners directly into `dashboard.py`.
* **In-App Onboarding & Admin Security:**
  * Removed public user self-registration and restricted operator account creation (`POST /auth/register`) to the Admin account both at the API level and in the Streamlit sidebar.
  * Added the **Register New Robot** form directly to the Streamlit dashboard for seamless fleet expansion.
* **Multi-Instance CLI Simulator:** Updated `simulator.py` to accept `sys.argv` parameters (`ROBOT_ID`, `USERNAME`, `PASSWORD`) so multiple robots owned by different operators can run concurrently.

### **Version 1.0 (Initial Release — Core Telemetry & Alert Pipeline)**
* Built the foundational FastAPI REST backend with SQLite persistence (`SQLAlchemy`) and JWT OAuth2 login.
* Created the initial single-robot simulator (`ROBOT-01`) with hardcoded credentials and unidirectional HTTP `POST` telemetry streaming.
* Implemented basic threshold evaluation (`WARNING` / `ERROR`) and database incident logging.
* Built the initial read-only Streamlit dashboard for viewing metric cards, historical line charts, and resolving alerts.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.12, FastAPI, Uvicorn, SQLAlchemy, Pydantic, JWT (`python-jose` / `pwdlib`)
* **Real-Time Transport:** FastAPI WebSockets, `websockets` (asyncio client)
* **Database:** SQLite (`robots.db`)
* **Frontend UI:** Streamlit, Pandas, Requests
* **Edge Simulation:** Python (`threading`, `asyncio`, `requests`, `websockets`)

---

## 📂 Project Structure

```text
Iot-Robot monitoring system/
├── main.py             # Entry-point runner script to launch the Uvicorn server (port 8000)
├── app.py              # Main FastAPI application, REST endpoints, WebSocket manager & threshold engine
├── dashboard.py        # Streamlit operator/admin UI, live charts, E-Stop controls & incident center
├── simulator.py        # Edge-device telemetry generator & background WebSocket command listener
├── database.py         # SQLite database engine & session configuration
├── models.py           # SQLAlchemy ORM table definitions (Users, Robots, SensorData, Alerts)
├── schemas.py          # Pydantic request/response validation schemas
├── security.py         # Password hashing, JWT token generation, and user authentication dependencies
├── .env                # Environment variables (e.g., SECRET_KEY, algorithm settings — do not commit)
├── robots.db           # Local SQLite database file (auto-generated on startup)
├── add_column.py       # Utility script for database schema updates
├── migrate_owner.py    # Utility script for migrating robot ownership records
└── README.md           # Project documentation and setup guide
```

---

## 🚀 Getting Started (Step-by-Step Guide)

### 1. Prerequisites & Installation
Ensure you have **Python 3.10+** installed. Clone or navigate to the project directory and install the required dependencies:

```bash
pip install fastapi uvicorn sqlalchemy pydantic requests websockets streamlit pandas python-multipart python-dotenv
```

### 2. Configure Your Admin Account & Environment (Important for New Setup)
Before running the system for the first time, set your own administrator username and environment secrets:

1. **Configure `.env`:** Create a `.env` file in the root folder containing your JWT secret key (e.g., `SECRET_KEY=your_super_secret_key`).
2. **Set Your Admin Username:**
   * Open `app.py` and locate the `register_user` function (`@app.post("/auth/register")`). Update the admin check (`if current_user.username != "<YOUR_ADMIN_USERNAME>":`) to your chosen admin username.
   * Open `dashboard.py` and update `ADMIN_USERNAME = "<YOUR_ADMIN_USERNAME>"` at the top of the file to match.
   * *(Optional)* Open `simulator.py` and update the default fallback `USERNAME` and `PASSWORD` variables if you plan to run `simulator.py` without CLI arguments.
3. **Bootstrap Initial Admin Account:** Since `POST /auth/register` is protected by admin authentication, temporarily comment out the `current_user` check in `app.py` on a fresh database, register your initial admin account via `/docs` (`http://127.0.0.1:8000/docs`), and then uncomment the protection.

### 3. Start the Backend Server (Terminal 1)
Launch the FastAPI server using the entry-point script:

```bash
python main.py
```
*(Alternatively, you can run `uvicorn app:app --reload` directly.)*

* The API will be live at `http://127.0.0.1:8000` (bound to `0.0.0.0:8000`)
* Interactive Swagger API documentation is available at `http://127.0.0.1:8000/docs`

### 4. Launch the Supervisory Dashboard (Terminal 2)
Open a second terminal window and start the Streamlit web interface:

```bash
streamlit run dashboard.py
```
* Your browser will automatically open the dashboard at `http://localhost:8501`.

### 5. Start the Robot Edge Simulator (Terminal 3)
Open a third terminal window to start simulating sensor telemetry and listening for E-Stop commands.

**Syntax:**
```bash
python simulator.py <ROBOT_ID> <USERNAME> <PASSWORD>
```

* **Run using default fallback credentials configured in `simulator.py`:**
  ```bash
  python simulator.py
  ```
* **Run a specific robot under a specific operator account:**
  ```bash
  python simulator.py Mark1 operator1 operator1password
  ```
*(Tip: You can open additional terminals and run `simulator.py` with different `<ROBOT_ID>` values to simulate an entire factory floor simultaneously.)*

---

## 📖 How to Use the Portal

### **For Administrators**
1. **Log In:** Enter your configured admin username and password in the left sidebar of the Streamlit dashboard.
2. **Create Operator Accounts:** Expand **🔐 Admin: Create Operator** in the sidebar, fill in the new operator's username, full name, email, and password, and click **Create Account**.
3. **Provision Robots:** Click **➕ Register New Robot** at the top right of the dashboard to register a new `Robot ID`, `Model`, `Type`, and `Location`.

### **For Operators**
1. **Log In:** Sign in via the sidebar using the credentials provided by your administrator.
2. **Monitor Live Telemetry:** Select a robot from the dropdown menu. View real-time cards and rolling trend graphs for **Temperature**, **Vibration**, **Current Draw**, and **Proximity** (auto-refreshing every 2 seconds).
3. **Execute Emergency Stop (E-Stop):**
   * Enter an optional reason in the **Supervisory Actuation & Control** bar.
   * Click **🚨 EMERGENCY STOP**.
   * The backend pushes the command over WebSockets, and the corresponding `simulator.py` terminal immediately disengages motors and pauses telemetry transmission.
4. **Resume Operations:** Once the floor is safe, click **✅ RESUME OPERATIONS** to clear the halt state and restart telemetry streaming.
5. **Manage Incidents:** Scroll to the **⚠️ Incident Management Center** to inspect active `WARNING` or `CRITICAL` threshold breaches and click **Resolve** to archive them.
