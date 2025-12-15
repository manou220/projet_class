"""Simulate upload + forecast via the running Flask app.

Usage: run after the server is started (http://localhost:5000)
This script uploads a sample CSV from the project `uploads/` folder and
submits a forecast request, then polls the jobs result endpoint.
"""
import os
import time
import json
import requests

BASE = 'http://localhost:5000'
UPLOAD_ENDPOINT = BASE + '/upload_file'
PREV_ENDPOINT = BASE + '/previsions'
JOBS_DIR = os.path.join('logs', 'jobs')

session = requests.Session()

# choose a sample file
candidates = [
    os.path.join('projet_coorrige', 'uploads', 'stock_data.csv'),
    os.path.join('projet_coorrige', 'uploads', 'test_data.csv'),
    os.path.join('uploads', 'stock_data.csv'),
    os.path.join('uploads', 'test_data.csv')
]
file_path = None
for c in candidates:
    if os.path.exists(c):
        file_path = c
        break
if not file_path:
    print('No sample CSV found in uploads/. Aborting.')
    raise SystemExit(1)

print('Using file:', file_path)

# upload
with open(file_path, 'rb') as fh:
    files = {'data_file': (os.path.basename(file_path), fh, 'text/csv')}
    r = session.post(UPLOAD_ENDPOINT, files=files, timeout=30)

print('Upload status:', r.status_code)
try:
    resp = r.json()
except Exception:
    print('Upload response not JSON; body:', r.text[:400])
    raise

if not resp.get('success'):
    print('Upload failed:', resp)
    raise SystemExit(1)

filename = resp.get('filename')
columns = resp.get('columns', [])
print('Uploaded filename:', filename)
print('Columns sample:', columns[:6])

# list jobs before
before = set(os.listdir(JOBS_DIR)) if os.path.exists(JOBS_DIR) else set()

# choose a model file from app/models
models_dir = os.path.join('app', 'models')
models = [f for f in os.listdir(models_dir) if f.endswith('.joblib')]
if not models:
    print('No model files found in app/models. Aborting.')
    raise SystemExit(1)
model_choice = models[0]
print('Using model:', model_choice)

# choose target column
target_col = 'Close' if 'Close' in columns else (columns[0] if columns else 'Close')

form = {
    'filename': filename,
    'selected_model': model_choice,
    'target_column': target_col,
    'forecast_type': 'close_price',
    'forecast_interval': 'jour',
    'forecast_steps': '5',
    'confidence_level': '95'
}

r2 = session.post(PREV_ENDPOINT, data=form, timeout=30)
print('Forecast submit status:', r2.status_code)
# After submit, a new job file should exist
after = set(os.listdir(JOBS_DIR)) if os.path.exists(JOBS_DIR) else set()
new = after - before
if not new:
    print('No new job file detected. Listing jobs dir:', after)
    print('Response body snippet:', r2.text[:800])
    raise SystemExit(1)
jobfile = sorted(list(new))[-1]
jobid = os.path.splitext(jobfile)[0]
print('Detected job id:', jobid)

# poll for result
result_url = BASE + f'/jobs/result/{jobid}'
status_url = BASE + f'/jobs/status/{jobid}'
print('Polling job result at', result_url)
for _ in range(60):
    try:
        rr = session.get(result_url, timeout=10)
        if rr.status_code == 200:
            data = rr.json()
            print('Job done. Result keys:', list(data.keys())[:10])
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
            break
        else:
            print('Job not ready, status code:', rr.status_code)
    except Exception as e:
        print('Error polling:', e)
    time.sleep(1)
else:
    print('Timeout waiting for job to finish.')
