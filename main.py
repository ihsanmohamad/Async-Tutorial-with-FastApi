from fastapi import FastAPI , HTTPException, status, Depends, Query
from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel

from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.contrib.fastapi import register_tortoise

from datetime import datetime

from tortoise import fields
from tortoise.models import Model

import asyncio

import httpx

def createApp():
    fastApp = FastAPI()

    register_tortoise(
        fastApp,
        db_url="postgres://postgres:q@localhost:5432/timeapi",
        # modules={"models" : ["timemodel"]},
        modules={"models" : ["main"]},
        generate_schemas=True,
        add_exception_handlers=True
    )
    return fastApp

app = createApp()

timezone_data = []

class City(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(50, unique=True)
    timezone = fields.CharField(50)
    

    def current_time(self) -> str:
        return ''

   
    @classmethod
    async def get_current_time(cls, obj):
        async with httpx.AsyncClient() as client:
            r = await client.get(f'http://worldtimeapi.org/api/timezone/{obj.timezone}')
        current_time = r.json()['datetime']
        obj.current_time = current_time

    class PydanticMeta:
        computed = ('current_time', )

City_Pydantic = pydantic_model_creator(City, name='City')
CityIn_Pydantic = pydantic_model_creator(City, name='CityIn', exclude_readonly=True)


async def get_all_time(obj):
    async with httpx.AsyncClient() as client:
        r = await client.get(f'http://worldtimeapi.org/api/timezone/{obj}')
    timezone = r.json()['timezone']
    current_time = r.json()['datetime']

    return {"timezone" : timezone, "current_time": current_time}
        
@app.get('/')
async def index():
    async with httpx.AsyncClient() as client:
        r = await client.get(f'http://worldtimeapi.org/api/timezone')
    timezone_data = r.json()
    
    tasks = []
    for timezone in timezone_data:
        task = asyncio.create_task(get_all_time(timezone))
        tasks.append(task)
    return await asyncio.gather(*tasks)


@app.get('/cities')
async def get_cities():
    cities =  await City_Pydantic.from_queryset(City.all())
    
    tasks = []
    for city in cities:
        task = asyncio.create_task(City.get_current_time(city))
        tasks.append(task)
    await asyncio.gather(*tasks)
    
    return cities
    

@app.get('/city/{city_name}')
async def get_city(city_name: str):
    city = await City_Pydantic.from_queryset_single(City.get(name=city_name))
    city_obj = await City.get_current_time(city)
    city_data = jsonable_encoder(city)

    print(city_data['name'])
    print(city_data['current_time'])
    return city
    


@app.post('/cities')
async def create_city(city: CityIn_Pydantic):
    city_obj = await City.create(**city.dict(exclude_unset=True))
    return await City_Pydantic.from_tortoise_orm(city_obj)

@app.delete('/cities/{city_id}')
async def delete_city(city_id: int):
    await City.filter(id=city_id).delete()
    return f"deleted successfully"
    
