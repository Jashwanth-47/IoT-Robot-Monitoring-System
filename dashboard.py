import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"
ADMIN_USERNAME = "Jashwanth"

st.set_page_config(page_title="IoT Robot Fleet Monitor", layout="wide")
st.title("IoT Robot Fleet Monitor")

# Initialize session state keys
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "robot_halted" not in st.session_state:
    st.session_state.robot_halted = False

# Helper function for the Robot Registration Form
def render_robot_registration_form(headers: dict, form_key: str):
    with st.form(key=form_key):
        col1, col2 = st.columns(2)
        new_robot_id = col1.text_input("Robot ID *", placeholder="e.g., ROBOT-02")
        new_model = col2.text_input("Model *", placeholder="e.g., KUKA-KR6")
        
        col3, col4 = st.columns(2)
        new_type = col3.text_input("Type *", placeholder="e.g., Articulated Arm")
        new_location = col4.text_input("Location *", placeholder="e.g., Assembly Line 2")

        submitted = st.form_submit_button("Register Robot", type="primary", use_container_width=True)
        
        if submitted:
            if not new_robot_id or not new_model or not new_type or not new_location:
                st.warning("Please fill in all fields.")
                return

            reg_url = f"{API_URL}/robots/register"
            reg_payload = {
                "robot_id": new_robot_id.strip(),
                "Model": new_model.strip(),
                "Type": new_type.strip(),
                "Location": new_location.strip()
            }
            try:
                res = requests.post(reg_url, json=reg_payload, headers=headers)
                if res.status_code in (200, 201):
                    st.toast(f"Robot {new_robot_id} registered successfully!", icon="🤖")
                    st.rerun()
                else:
                    detail = res.json().get("detail", res.text)
                    st.error(f"Registration failed ({res.status_code}): {detail}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

# Sidebar Authentication Section (Login Only for Public)
with st.sidebar:
    st.header("Authentication")

    if not st.session_state.logged_in:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Log in", use_container_width=True):
            login_url = f"{API_URL}/auth/login"
            payload = {
                "username": username,
                "password": password
            }

            try:
                response = requests.post(login_url, data=payload)

                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data.get("access_token")
                    st.session_state.username = username
                    st.session_state.logged_in = True
                    st.rerun()
                elif response.status_code == 401:
                    st.error("Invalid username or password.")
                else:
                    st.error(f"Login failed: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Is FastAPI running on port 8000?")

    else:
        role_label = "Admin" if st.session_state.username == ADMIN_USERNAME else "Operator"
        st.success(f"Logged in as **{st.session_state.username}** ({role_label})")

        if st.button("Log out", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.logged_in = False
            st.session_state.robot_halted = False
            st.rerun()

        # --- ADMIN-ONLY OPERATOR REGISTRATION ---
       # --- ADMIN-ONLY OPERATOR REGISTRATION ---
        if st.session_state.username == ADMIN_USERNAME:
            st.divider()
            with st.expander("🔐 Admin: Create Operator"):
                with st.form("admin_create_user_form", clear_on_submit=True):
                    new_user = st.text_input("Operator Username")
                    new_full_name = st.text_input("Full Name", placeholder="e.g., Rahul Sharma")
                    new_email = st.text_input("Operator Email", placeholder="operator@factory.com")
                    new_pass = st.text_input("Password", type="password")
                    create_btn = st.form_submit_button("Create Account", use_container_width=True)

                    if create_btn:
                        if not new_user or not new_email or not new_pass:
                            st.warning("Username, email, and password are required.")
                        else:
                            register_url = f"{API_URL}/auth/register"
                            reg_payload = {
                                "username": new_user.strip(),
                                "full_name": new_full_name.strip() or None,
                                "email": new_email.strip(),
                                "password": new_pass
                            }
                            admin_headers = {"Authorization": f"Bearer {st.session_state.token}"}
                            try:
                                reg_res = requests.post(register_url, json=reg_payload, headers=admin_headers)
                                if reg_res.status_code in (200, 201):
                                    st.success(f"Operator '{new_user}' created!")
                                else:
                                    detail = reg_res.json().get("detail", reg_res.text)
                                    st.error(f"Failed ({reg_res.status_code}): {detail}")
                            except requests.exceptions.ConnectionError:
                                st.error("Backend unreachable.")
# Main Dashboard Area
if not st.session_state.logged_in:
    st.info("Authorized personnel only. Please log in using the sidebar to access fleet telemetry.")
else:
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }
    
    try:
        url = f"{API_URL}/robots"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            robots = response.json()
            
            # --- EMPTY FLEET ONBOARDING ---
# --- EMPTY FLEET ONBOARDING ---
            if not robots:
                if st.session_state.username == ADMIN_USERNAME:
                    st.info("No robots assigned to your account yet. Register a robot below to begin monitoring.")
                    st.subheader("➕ Register Robot")
                    render_robot_registration_form(headers, form_key="first_robot_form")
                else:
                    st.warning("No robots assigned to your account yet. Contact your administrator to provision a robot.")
            
            # --- ACTIVE FLEET DASHBOARD ---
            else:
                top_col1, top_col2 = st.columns([3, 2])
                with top_col1:
                    robot_ids = [r["robot_id"] for r in robots]
                    selected_robot_id = st.selectbox("Select Robot to Monitor", robot_ids)

                with top_col2:
                    if st.session_state.username == ADMIN_USERNAME:
                        st.write("")
                        with st.expander("➕ Register New Robot"):
                            render_robot_registration_form(headers, form_key="add_robot_form")

                selected_robot = next(r for r in robots if r["robot_id"] == selected_robot_id)

                col1, col2, col3 = st.columns(3)
                col1.metric("Model", selected_robot.get("Model", "N/A"))
                col2.metric("Type", selected_robot.get("Type", "N/A"))
                col3.metric("Location", selected_robot.get("Location", "N/A"))

                st.divider()

                # --- Supervisory Actuation & E-Stop Panel ---
                st.subheader("🛑 Supervisory Actuation & Control")

                if st.session_state.robot_halted:
                    st.error(f"🚨 **{selected_robot_id} IS EMERGENCY HALTED.** Motors disengaged. Click 'Resume Operations' to restart.")

                ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])

                with ctrl_col1:
                    estop_reason = st.text_input(
                        "Command Reason / Operator Note",
                        value="Manual operator override",
                        label_visibility="collapsed",
                        placeholder="Enter reason for E-Stop or Resume..."
                    )

                with ctrl_col2:
                    if st.button("🚨 EMERGENCY STOP", type="primary", use_container_width=True):
                        cmd_url = f"{API_URL}/robots/{selected_robot_id}/command"
                        cmd_payload = {
                            "command": "EMERGENCY_STOP",
                            "reason": estop_reason or "Emergency stop triggered from dashboard"
                        }
                        try:
                            cmd_res = requests.post(cmd_url, json=cmd_payload, headers=headers)
                            if cmd_res.status_code == 200:
                                st.session_state.robot_halted = True
                                st.toast(f"E-STOP sent to {selected_robot_id}!", icon="🚨")
                                st.rerun()
                            else:
                                st.error(f"Command failed: HTTP {cmd_res.status_code}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Connection error: {e}")

                with ctrl_col3:
                    if st.button("✅ RESUME OPERATIONS", use_container_width=True):
                        cmd_url = f"{API_URL}/robots/{selected_robot_id}/command"
                        cmd_payload = {
                            "command": "RESUME",
                            "reason": estop_reason or "Resumed from dashboard"
                        }
                        try:
                            cmd_res = requests.post(cmd_url, json=cmd_payload, headers=headers)
                            if cmd_res.status_code == 200:
                                st.session_state.robot_halted = False
                                st.toast(f"Resume signal sent to {selected_robot_id}!", icon="✅")
                                st.rerun()
                            else:
                                st.error(f"Command failed: HTTP {cmd_res.status_code}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Connection error: {e}")

                st.divider()

                # --- Live Telemetry & Incident Center ---
                @st.fragment(run_every="2s")
                def display_live_telemetry_and_alerts():
                    sensor_records = []
                    sensor_url = f"{API_URL}/robots/{selected_robot_id}/sensor-data?limit=25"

                    try:
                        sensor_response = requests.get(sensor_url, headers=headers)
                        if sensor_response.status_code == 200:
                            sensor_records = sensor_response.json()
                    except requests.exceptions.RequestException:
                        pass

                    if not sensor_records:
                        st.warning("No telemetry recorded yet for this robot.")
                        return

                    latest = sensor_records[0]

                    # Status Alert Badge
                    status = latest.get("status", "UNKNOWN")
                    if st.session_state.robot_halted:
                        st.warning("System State: **HALTED (Waiting for Resume Signal)**")
                    elif status == "NORMAL":
                        st.success("System State: **NORMAL**")
                    elif status == "WARNING":
                        st.warning("System State: **WARNING DETECTED**")
                    else:
                        st.error("System State: **CRITICAL FAULT**")

                    # Live Metric Cards
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Temperature", f"{latest['temperature']:.2f} °C")
                    m2.metric("Vibration", f"{latest['vibration']:.3f} mm/s")
                    m3.metric("Current Draw", f"{latest['current_draw']:.2f} A")
                    m4.metric("Proximity", f"{latest['proximity']:.2f} m")

                    st.divider()

                    # Telemetry Trend Charts
                    st.subheader("📊 Multi-Metric Telemetry Trends")
                    history = list(reversed(sensor_records))
                    df_history = pd.DataFrame(history)

                    tab1, tab2, tab3, tab4 = st.tabs([
                        "Temperature (°C)", 
                        "Vibration (mm/s)", 
                        "Current Draw (A)", 
                        "Proximity (m)"
                    ])

                    with tab1:
                        st.line_chart(df_history[["temperature"]])
                    with tab2:
                        st.line_chart(df_history[["vibration"]])
                    with tab3:
                        st.line_chart(df_history[["current_draw"]])
                    with tab4:
                        st.line_chart(df_history[["proximity"]])

                    st.divider()

                    # Incident & Alert Management Section
                    st.subheader("⚠️ Incident Management Center")
                    alerts_url = f"{API_URL}/robots/{selected_robot_id}/alerts"
                    
                    try:
                        alert_resp = requests.get(alerts_url, headers=headers)
                        if alert_resp.status_code == 200:
                            all_alerts = alert_resp.json()
                            open_alerts = [a for a in all_alerts if not a.get("resolved", False)]
                            resolved_alerts = [a for a in all_alerts if a.get("resolved", False)]

                            if not open_alerts:
                                st.success("No active unresolved incidents for this robot.")
                            else:
                                st.write(f"**Active Unresolved Incidents ({len(open_alerts)}):**")
                                for alert in open_alerts:
                                    alert_box, resolve_col = st.columns([5, 1])

                                    with alert_box:
                                        msg = f"**[{alert['severity']}]** {alert['message']} (Value: `{alert['value']}` | Metric: `{alert['metric']}`) — *{alert['problem_created']}*"
                                        if alert["severity"].upper() == "CRITICAL":
                                            st.error(msg)
                                        else:
                                            st.warning(msg)

                                    with resolve_col:
                                        if st.button("Resolve", key=f"btn_resolve_{alert['id']}", use_container_width=True):
                                            resolve_url = f"{API_URL}/alerts/{alert['id']}/resolve"
                                            patch_res = requests.patch(resolve_url, headers=headers)
                                            if patch_res.status_code == 200:
                                                st.toast(f"Incident #{alert['id']} resolved!", icon="✅")
                                                st.rerun()
                                            else:
                                                st.error("Failed to resolve alert")

                            if resolved_alerts:
                                with st.expander(f"View Resolved Incidents Archive ({len(resolved_alerts)})"):
                                    df_resolved = pd.DataFrame(resolved_alerts)[
                                        ["id", "severity", "metric", "value", "message", "problem_created"]
                                    ]
                                    st.dataframe(df_resolved, use_container_width=True)

                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not load alerts: {e}")

                display_live_telemetry_and_alerts()

        else:
            st.error(f"Failed to fetch robots: HTTP {response.status_code}")

    except requests.exceptions.ConnectionError:
        st.error("Backend server unreachable. Make sure FastAPI is running.")