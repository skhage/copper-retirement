# Databricks notebook source
# DBTITLE 1,Demo Reset — Copper Retirement Apps
# MAGIC %md
# MAGIC # Demo Reset — Copper Retirement Apps
# MAGIC
# MAGIC **Purpose:** Clear all user-session state in **copper-map** and **regulatory-assistant** apps so they start fresh for the live demo.
# MAGIC
# MAGIC **What gets reset:**
# MAGIC - **copper-map (Dash):** Server-side cached data (HEX_CELLS, KPIS, DEVICES, GOLD tables) + client-side Genie conversation store + filter dropdowns
# MAGIC - **regulatory-assistant (Express+React):** Server process restart clears any in-memory state; React client state resets on page load
# MAGIC
# MAGIC **How it works:**
# MAGIC 1. Stops both apps (flushes server-side cached data)
# MAGIC 2. Starts both apps (fresh process with live data reload from SQL warehouse)
# MAGIC 3. Polls until both apps are healthy
# MAGIC 4. Verifies cold-start load time < 5 seconds
# MAGIC 5. Prints clean demo URLs
# MAGIC
# MAGIC **Run this notebook before every live demo.**

# COMMAND ----------

# DBTITLE 1,Configuration
# App names and source paths
APPS = {
    "copper-map": {
        "source_path": "/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/copper-map",
        "beat": "Beat 1: Where is our copper / risk?",
    },
    "regulatory-assistant": {
        "source_path": "/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/regulatory-assistant",
        "beat": "Beat 4: Clear on regs?",
    },
}

# Timeouts
STOP_TIMEOUT_SEC = 60      # max wait for app to stop
START_TIMEOUT_SEC = 180    # max wait for app to start (reg-assistant does npm build)
HEALTH_TIMEOUT_SEC = 5     # cold-start load time target

print(f"Demo reset configured for {len(APPS)} apps: {', '.join(APPS.keys())}")

# COMMAND ----------

# DBTITLE 1,Step 1 — Stop both apps
import time
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

def get_app_state(app_name: str) -> str:
    """Get the app state as a string."""
    app = w.apps.get(app_name)
    return str(app.app_status.state) if app.app_status else "UNKNOWN"

def stop_app(app_name: str) -> str:
    """Stop an app and wait until it's no longer RUNNING. Returns final state string."""
    try:
        state = get_app_state(app_name)
        if 'RUNNING' not in state and 'STARTING' not in state:
            print(f"  {app_name}: already stopped ({state})")
            return state
        
        print(f"  {app_name}: stopping (was {state})...")
        w.apps.stop(app_name)
        
        for i in range(STOP_TIMEOUT_SEC // 5):
            time.sleep(5)
            state = get_app_state(app_name)
            if 'STOPPED' in state or 'IDLE' in state or 'UNAVAILABLE' in state:
                print(f"  {app_name}: stopped after {(i+1)*5}s")
                return state
        print(f"  {app_name}: stop timed out after {STOP_TIMEOUT_SEC}s (state: {state})")
        return state
    except Exception as e:
        print(f"  {app_name}: stop error — {e}")
        return f"ERROR: {e}"

print("Stopping apps (flushing server-side caches)...")
for name in APPS:
    stop_app(name)
print("\nAll apps stopped.")

# COMMAND ----------

# DBTITLE 1,Step 2 — Start both apps
def start_app(app_name: str) -> str:
    """Start an app and wait until it's RUNNING. Returns final state string."""
    try:
        state = get_app_state(app_name)
        if 'RUNNING' in state:
            print(f"  {app_name}: already running")
            return state
        
        print(f"  {app_name}: starting...")
        w.apps.start(app_name)
        
        for i in range(START_TIMEOUT_SEC // 5):
            time.sleep(5)
            state = get_app_state(app_name)
            if 'RUNNING' in state:
                print(f"  {app_name}: RUNNING after {(i+1)*5}s")
                return state
            if 'FAILED' in state or 'ERROR' in state:
                print(f"  {app_name}: FAILED — {state}")
                return state
            if (i+1) % 6 == 0:  # progress every 30s
                print(f"    ...still starting ({(i+1)*5}s, state: {state})")
        print(f"  {app_name}: start timed out after {START_TIMEOUT_SEC}s (state: {state})")
        return state
    except Exception as e:
        print(f"  {app_name}: start error — {e}")
        return f"ERROR: {e}"

print("Starting apps (fresh process = clean state + live data reload)...")
start_results = {}
for name in APPS:
    start_results[name] = start_app(name)

print("\nStart results:")
for name, state in start_results.items():
    icon = "✅" if "RUNNING" in state else "❌"
    print(f"  {icon} {name}: {state}")

# COMMAND ----------

# DBTITLE 1,Step 3 — Verify cold-start load time
import urllib.request
import urllib.error
import ssl

def check_app_health(app_name: str, timeout_sec: float = HEALTH_TIMEOUT_SEC) -> dict:
    """Hit the app URL and measure response time. Returns {url, status, latency_ms, ok}."""
    try:
        app = w.apps.get(app_name)
        url = getattr(app, 'url', None)
        if not url:
            return {"url": None, "status": "NO_URL", "latency_ms": None, "ok": False}
        
        # Ensure https
        if not url.startswith("http"):
            url = f"https://{url}"
        url = url.rstrip("/")
        
        ctx = ssl.create_default_context()
        start = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "demo-reset/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout_sec, context=ctx)
        latency_ms = (time.time() - start) * 1000
        status_code = resp.getcode()
        
        return {
            "url": url,
            "status": status_code,
            "latency_ms": round(latency_ms),
            "ok": status_code == 200 and latency_ms < (timeout_sec * 1000),
        }
    except urllib.error.HTTPError as e:
        latency_ms = (time.time() - start) * 1000
        return {"url": url, "status": e.code, "latency_ms": round(latency_ms), "ok": False}
    except Exception as e:
        return {"url": getattr(app, 'url', '?'), "status": str(e)[:80], "latency_ms": None, "ok": False}

print(f"Checking cold-start response times (target: <{HEALTH_TIMEOUT_SEC}s)...\n")
health_results = {}
for name in APPS:
    result = check_app_health(name)
    health_results[name] = result
    if result["ok"]:
        print(f"  ✅ {name}: {result['latency_ms']}ms (HTTP {result['status']})")
    elif result["latency_ms"] is not None:
        print(f"  ⚠️  {name}: {result['latency_ms']}ms (HTTP {result['status']}) — over target" 
              if result["latency_ms"] > HEALTH_TIMEOUT_SEC * 1000
              else f"  ⚠️  {name}: {result['latency_ms']}ms (HTTP {result['status']})")
    else:
        print(f"  ❌ {name}: {result['status']}")

all_ok = all(r["ok"] for r in health_results.values())
print(f"\n{'\u2705 All apps responding within target' if all_ok else '\u26a0\ufe0f  Some apps outside target — see above'}")

# COMMAND ----------

# DBTITLE 1,Step 4 — Demo-ready summary
print("=" * 70)
print("  DEMO RESET COMPLETE")
print("=" * 70)
print()

for name, cfg in APPS.items():
    hr = health_results.get(name, {})
    sr = start_results.get(name, "UNKNOWN")
    url = hr.get("url", "(unknown)")
    latency = hr.get("latency_ms")
    running = "RUNNING" in str(sr)
    
    icon = "✅" if running and hr.get("ok") else "⚠️ " if running else "❌"
    print(f"  {icon} {name}")
    print(f"     {cfg['beat']}")
    print(f"     URL: {url}")
    print(f"     Status: {'RUNNING' if running else sr}")
    if latency is not None:
        speed_icon = "⚡" if latency < 3000 else "⏱️ " if latency < 5000 else "⚠️ "
        print(f"     Load time: {speed_icon} {latency}ms")
    print()

print("Session state cleared:")
print("  • copper-map: Genie conversation, filter selections, server data cache")
print("  • regulatory-assistant: Chat history, jurisdiction filter, document state")
print()
print("Both apps will load with fresh data on first browser visit.")
print("Tip: Open each URL in a fresh incognito window for cleanest demo.")
print("=" * 70)