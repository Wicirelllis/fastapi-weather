from datetime import datetime, timedelta, timezone

import openmeteo_requests
import requests_cache
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from geopy.geocoders import Nominatim
from retry_requests import retry


app = FastAPI()

templates = Jinja2Templates(directory="templates")

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)


@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "data": None})

@app.post("/", response_class=HTMLResponse)
async def handle_form(request: Request, city: str = Form(...)):
    geolocator = Nominatim(user_agent="wici-o-complex")
    location = geolocator.geocode(city)

    if location is None:
        data = {
            'city': city,
            'not_found': True
        }
        return templates.TemplateResponse("index.html", {"request": request, "data": data})
    
    hours_to_fc = 6

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "hourly": ["temperature_2m", "relative_humidity_2m"],
        "forecast_hours": hours_to_fc,
        "timezone": "auto",
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    temperature_fc = response.Hourly().Variables(0).ValuesAsNumpy().tolist()
    humidity_fc = response.Hourly().Variables(1).ValuesAsNumpy().tolist()
    current_hour = datetime.fromtimestamp(response.Hourly().Time(), tz=timezone(timedelta(hours=3)))
    timestamp_fc = [current_hour + timedelta(hours=i+1) for i in range(hours_to_fc)]

    data = {
        'city': city,
        'latitude': location.latitude,
        'longitude': location.longitude,
        'temperature': temperature_fc,
        'humidity': humidity_fc,
        'timestamp': timestamp_fc,
    }

    return templates.TemplateResponse("index.html", {"request": request, "data": data})
