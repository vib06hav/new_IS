import requests
import time
import os
import json
import sys

# Ensure UTF-8 output even on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "http://localhost:8000"
PDF_PATH = "tests/pdfs/Dummy App (1)_v8_filled.pdf"
OUTPUT_LOG = "logs/stage_1_5_run_output.txt"

def log(msg):
    print(msg)
    with open(OUTPUT_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def run_pipeline():
    if os.path.exists(OUTPUT_LOG):
        os.remove(OUTPUT_LOG)
        
    log(f"--- Starting Stage 1.5 Pipeline Execution ---")
    
    # 1. Register/Login
    username = f"test_user_{int(time.time())}@example.com"
    password = "testpassword123"
    
    log(f"Registering user: {username}")
    reg_resp = requests.post(f"{API_BASE_URL}/auth/register", json={
        "email": username,
        "password": password,
        "role": "interviewer"
    })
    if reg_resp.status_code != 201:
        log(f"Registration failed: {reg_resp.text}")
        return

    log("Logging in...")
    login_resp = requests.post(f"{API_BASE_URL}/auth/login", data={
        "username": username,
        "password": password
    })
    if login_resp.status_code != 200:
        log(f"Login failed: {login_resp.text}")
        return
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Upload PDF
    if not os.path.exists(PDF_PATH):
        log(f"PDF file not found at {PDF_PATH}")
        return

    log(f"Uploading PDF: {PDF_PATH}")
    with open(PDF_PATH, "rb") as f:
        upload_resp = requests.post(
            f"{API_BASE_URL}/applications/upload",
            headers=headers,
            files={"file": (os.path.basename(PDF_PATH), f, "application/pdf")}
        )
    
    if upload_resp.status_code != 201:
        log(f"Upload failed: {upload_resp.text}")
        return
    
    app_data = upload_resp.json()
    app_id = app_data["id"]
    log(f"Upload successful. Application ID: {app_id}")
    
    # 3. Poll for completion
    log("Waiting for pipeline to complete...")
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        status_resp = requests.get(f"{API_BASE_URL}/applications/{app_id}", headers=headers)
        if status_resp.status_code != 200:
            log(f"Failed to get status: {status_resp.text}")
            break
        
        app_status = status_resp.json()
        log(f"Current Status: {app_status['status']}")
        
        if app_status["status"] == "complete":
            log("\n✅ Pipeline Execution SUCCESSFUL!")
            log("\n--- Synthesis Result ---")
            log(json.dumps(app_status["synthesis"], indent=2, ensure_ascii=False))
            return
        elif app_status["status"] == "failed":
            log(f"\n❌ Pipeline Execution FAILED.")
            return
        
        time.sleep(5)
        retry_count += 1
    
    log("Timeout waiting for pipeline completion.")

if __name__ == "__main__":
    run_pipeline()
