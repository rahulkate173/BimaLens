import asyncio
from app.database import connect_to_mongo, get_db

async def check():
    await connect_to_mongo()
    db = get_db()
    async for p in db['policies'].find({}, {'filename':1,'status':1,'_id':1}):
        print(p['status'], '|', str(p['_id']), '|', p.get('filename',''))
asyncio.run(check())

