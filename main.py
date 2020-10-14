from fastapi import FastAPI , HTTPException, status, Depends
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

@app.get('/')
def index():
    return {'key' : 'value'}

@app.get('/cities')
async def get_cities():
    cities =  await City_Pydantic.from_queryset(City.all())
    
    tasks = []
    for city in cities:
        task = asyncio.create_task(City.get_current_time(city))
        tasks.append(task)
    await asyncio.gather(*tasks)
    
    return cities
    

@app.get('/cities/{city_id}')
async def get_city(city_id: int):
    city = await City_Pydantic.from_queryset_single(City.get(id=city_id))
    city_obj = await City.get_current_time(city)
    return city
    


@app.post('/cities')
async def create_city(city: CityIn_Pydantic):
    city_obj = await City.create(**city.dict(exclude_unset=True))
    return await City_Pydantic.from_tortoise_orm(city_obj)

@app.delete('/cities/{city_id}')
async def delete_city(city_id: int):
    await City.filter(id=city_id).delete()
    return f"deleted successfully"
    