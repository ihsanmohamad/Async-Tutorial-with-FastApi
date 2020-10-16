from fastapi import FastAPI 
from fastapi.encoders import jsonable_encoder

import asyncio

import httpx


app = FastAPI(title="Async example", description="Async example of worldtime api")

timezone_data = []

async def get_all_time(obj):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f'http://worldtimeapi.org/api/timezone/{obj}')
        # print(r.json())
        timezone = r.json()['timezone']
        current_time = r.json()['datetime']

        return {"timezone" : timezone, "current_time": current_time}
    except:
        pass

@app.get('/')
async def index():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f'http://worldtimeapi.org/api/timezone')
        timezone_data = r.json()
            
        tasks = []
        for timezone in timezone_data:
            task = asyncio.create_task(get_all_time(timezone))
            tasks.append(task)
        return await asyncio.gather(*tasks)
        
    except:
        return {"detail": "Unknown Error"}
