from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates # Import Templates
from pydantic import BaseModel
import json
import os
from datetime import datetime
import math

app = FastAPI()

# --- CONFIGURATION ---
# Initialize templates looking in the "templates" directory
templates = Jinja2Templates(directory="templates")

if os.getenv('WEBSITE_SITE_NAME'):
    DATA_FILE = "/home/site/wwwroot/sensor_data.json"
else:
    DATA_FILE = "sensor_data.json"

ITEMS_PER_PAGE = 10

# --- DATA MODEL ---
class SensorReading(BaseModel):
    temperature: float
    humidity: float

# --- HELPER FUNCTIONS ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_data(new_reading):
    data = load_data()
    entry = {
        "temp": new_reading.temperature,
        "humidity": new_reading.humidity,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data.insert(0, entry)
    data = data[:1000] # Limit file size
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ROUTES ---

@app.get("/")
async def home(request: Request, page: int = 1):
    # 1. Load Data
    all_data = load_data()
    
    # 2. Extract Latest for Cards
    latest = all_data[0] if all_data else None
    
    # 3. Pagination Logic
    total_records = len(all_data)
    total_pages = math.ceil(total_records / ITEMS_PER_PAGE)
    
    if page < 1: page = 1
    if page > total_pages and total_pages > 0: page = total_pages
    
    start_index = (page - 1) * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    history_page_data = all_data[start_index:end_index]

    # 4. View Logic (Should history be open or closed?)
    details_state = "open" if page > 1 else ""
    toggle_icon = "fa-chevron-up" if page > 1 else "fa-chevron-down"

    # 5. Render Template
    # We pass all our variables to the 'index.html' file here
    return templates.TemplateResponse("index.html", {
        "request": request,
        "latest": latest,
        "history_page_data": history_page_data,
        "page": page,
        "total_pages": total_pages,
        "details_state": details_state,
        "toggle_icon": toggle_icon
    })

@app.post("/api/update")
async def update_sensor(reading: SensorReading):
    save_data(reading)
    return {"status": "success", "message": "Data saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)