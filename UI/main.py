from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import subprocess
import os
import time
import json
import threading
from datetime import datetime
import yaml

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEATURE_DIR = os.path.join(BASE_DIR, "../features")
ALLURE_REPORT_DIR = os.path.join(BASE_DIR, "../reports/allure-report")
LOG_FILE_PATH = os.path.join(BASE_DIR, "../logs")
HISTORY_FILE = os.path.join(BASE_DIR, "../reports/executions.json")
CONFIG_FILE = os.path.join(BASE_DIR, "../config/ui_config.yaml")

execution_log = []

app.mount("/static", StaticFiles(directory="UI/static"), name="static")
templates = Jinja2Templates(directory="UI/templates")


def load_ui_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f)
        except:
            return {}
    return {}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    feature_files = [f for f in os.listdir(FEATURE_DIR) if f.endswith(".feature")]
    tags = ["@regression", "@smoke", "@critical"]
    config = load_ui_config()
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as h:
            try:
                history = json.load(h)
            except:
                pass
    return templates.TemplateResponse("index.html", {
        "request": request,
        "features": feature_files,
        "tags": tags,
        "config": config,
        "history": history
    })


@app.post("/run")
def run_tests(
    request: Request,
    tags: str = Form(""),
    env: str = Form("dev"),
    mode: str = Form("parallel"),
    features: str = Form("")
):
    def background_test_run():
        execution_log.clear()
        run_cmds = []
        selected_features = [f.strip() for f in features.split(',') if f.strip()]

        if mode == "parallel":
            run_cmds.append(f"python run_parallel.py --tags={tags} --env={env}")
        elif mode == "single" and selected_features:
            run_cmds.append(f"behave features/{selected_features[0]} --tags={tags} -D TEST_ENV={env}")
        elif mode == "multiple" and selected_features:
            run_cmds = [f"behave features/{f} --tags={tags} -D TEST_ENV={env}" for f in selected_features]
        else:
            execution_log.append(json.dumps({"step": "⚠️ No valid feature(s) selected", "status": "done", "passed": 0, "failed": 0, "time": "0s"}))
            return

        start = time.time()
        for cmd in run_cmds:
            execution_log.append(json.dumps({"step": f"🔄 Running: {cmd}", "status": "running"}))
            os.system(cmd)

        duration = round(time.time() - start, 2)

        result_path = os.path.join(BASE_DIR, "result.json")
        passed, failed = 0, 0
        if os.path.exists(result_path):
            try:
                with open(result_path, "r") as f:
                    parsed = json.load(f)
                    passed = parsed.get("passed", 0)
                    failed = parsed.get("failed", 0)
            except:
                pass

        result = {
            "step": f"✅ {passed} passed, ❌ {failed} failed (⏱ {duration}s)",
            "status": "done",
            "passed": passed,
            "failed": failed,
            "time": f"{duration}s",
            "env": env,
            "tags": tags,
            "feature": features,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        execution_log.append(json.dumps(result))
        with open(result_path, "w") as f:
            json.dump(result, f)

        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as h:
                try:
                    history = json.load(h)
                except:
                    history = []
        history.insert(0, result)
        with open(HISTORY_FILE, "w") as h:
            json.dump(history[:10], h, indent=2)

    threading.Thread(target=background_test_run).start()
    return RedirectResponse(url="/", status_code=303)


@app.get("/stream-status")
def stream_status():
    def event_stream():
        last_index = 0
        while True:
            if last_index < len(execution_log):
                yield f"data: {execution_log[last_index]}\n\n"
                if json.loads(execution_log[last_index]).get("status") == "done":
                    break
                last_index += 1
            time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/report")
def show_report():
    index_path = os.path.join(ALLURE_REPORT_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    return HTMLResponse(content="Allure report not found. Please run a test.", status_code=404)


@app.get("/logs")
def get_logs():
    log_files = [f for f in os.listdir(LOG_FILE_PATH) if f.endswith(".log")]
    latest_log = sorted(log_files)[-1] if log_files else None
    if latest_log:
        return FileResponse(os.path.join(LOG_FILE_PATH, latest_log), media_type='text/plain')
    return HTMLResponse(content="No logs found.", status_code=404)


@app.get("/download-report")
def download_report():
    zip_path = os.path.join(BASE_DIR, "../reports/allure-report.zip")
    subprocess.call(f"powershell Compress-Archive -Path ../reports/allure-report/* -DestinationPath {zip_path}", shell=True)
    return FileResponse(zip_path, media_type='application/zip', filename="allure-report.zip")


@app.get("/history")
def get_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as h:
            return HTMLResponse(content=h.read(), media_type="application/json")
    return HTMLResponse(content="[]", media_type="application/json")
