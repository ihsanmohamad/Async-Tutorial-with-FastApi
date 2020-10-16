from fastapi import FastAPI 

import asyncio

import requests


app = FastAPI(title="Sync example", description="Sync example of worldtime api")

timezone_data = []
data = []

def get_all_time(obj):
    try:
        
        r = requests.get(f'http://worldtimeapi.org/api/timezone/{obj}')
        print(r.json())
        timezone = r.json()['timezone']
        current_time = r.json()['datetime']

        return {"timezone" : timezone, "current_time": current_time}
    except:
        pass

@app.get('/')
def index():
    try:
        
        r = requests.get(f'http://worldtimeapi.org/api/timezone')
        timezone_data = r.json()
            
        for timezone in timezone_data:
            data.append(get_all_time(timezone))
            
        return data
        
    except:
        return {"detail": "Unknown Error"}
