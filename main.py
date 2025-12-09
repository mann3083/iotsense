from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import os
from datetime import datetime
import math

app = FastAPI()

# --- CONFIGURATION ---
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
    # Insert at the beginning (newest first)
    data.insert(0, entry)
    # Optional: Limit total file size to 1000 records to prevent infinite growth
    data = data[:1000] 
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(page: int = 1):
    # 1. Load all data
    all_data = load_data()
    
    # 2. Extract Latest Reading for the Dashboard Cards
    latest = all_data[0] if all_data else None
    
    # 3. Handle Pagination for the History Table
    total_records = len(all_data)
    total_pages = math.ceil(total_records / ITEMS_PER_PAGE)
    
    # Ensure page is valid
    if page < 1: page = 1
    if page > total_pages and total_pages > 0: page = total_pages
    
    start_index = (page - 1) * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    
    # Slice the data for the current view
    history_page_data = all_data[start_index:end_index]

    # 4. Generate HTML (Embedded for single-file simplicity)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IoT Dashboard</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            
            /* Dashboard Cards */
            .dashboard {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }}
            .card {{ flex: 1; background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; min-width: 200px; }}
            .card-icon {{ font-size: 2.5rem; margin-bottom: 10px; }}
            .metric {{ font-size: 3rem; font-weight: bold; margin: 10px 0; }}
            .label {{ color: #666; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; }}
            
            /* Specific Colors */
            .temp-card {{ border-top: 5px solid #ff6b6b; }}
            .temp-icon {{ color: #ff6b6b; }}
            .humid-card {{ border-top: 5px solid #4ecdc4; }}
            .humid-icon {{ color: #4ecdc4; }}
            
            /* Table Styling */
            .history-section {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ text-align: left; padding: 15px; border-bottom: 2px solid #eee; color: #555; }}
            td {{ padding: 15px; border-bottom: 1px solid #eee; }}
            tr:last-child td {{ border-bottom: none; }}
            
            /* Pagination Controls */
            .pagination {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }}
            .btn {{ text-decoration: none; background: #0078d4; color: white; padding: 8px 16px; border-radius: 6px; font-size: 0.9rem; }}
            .btn.disabled {{ background: #ccc; pointer-events: none; }}
            .page-info {{ color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="text-align:center; margin-bottom: 30px;">Sensor Dashboard</h2>

            <div class="dashboard">
                <div class="card temp-card">
                    <div class="card-icon temp-icon"><i class="fas fa-temperature-high"></i></div>
                    <div class="label">Temperature</div>
                    <div class="metric">
                        {latest['temp'] if latest else '--'} <span style="font-size:1.5rem">°C</span>
                    </div>
                </div>

                <div class="card humid-card">
                    <div class="card-icon humid-icon"><i class="fas fa-tint"></i></div>
                    <div class="label">Humidity</div>
                    <div class="metric">
                        {latest['humidity'] if latest else '--'} <span style="font-size:1.5rem">%</span>
                    </div>
                </div>
            </div>
             <div style="text-align:center; color:#888; margin-bottom:20px;">
                <small>Last Update: {latest['timestamp'] if latest else 'Never'}</small>
            </div>

            <div class="history-section">
                <h3><i class="fas fa-history"></i> History Log</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Temp (°C)</th>
                            <th>Humidity (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f"<tr><td>{r['timestamp']}</td><td>{r['temp']}</td><td>{r['humidity']}</td></tr>" for r in history_page_data)}
                        {'<tr><td colspan="3" style="text-align:center">No data available</td></tr>' if not history_page_data else ''}
                    </tbody>
                </table>

                <div class="pagination">
                    <a href="/?page={page-1}" class="btn {'disabled' if page <= 1 else ''}">&laquo; Previous</a>
                    <span class="page-info">Page {page} of {total_pages if total_pages > 0 else 1}</span>
                    <a href="/?page={page+1}" class="btn {'disabled' if page >= total_pages else ''}">Next &raquo;</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/api/update")
async def update_sensor(reading: SensorReading):
    save_data(reading)
    return {"status": "success", "message": "Data saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)