import asyncio
from app.database import connect_to_mongo, get_db

async def fix():
    await connect_to_mongo()
    db = get_db()
    r = await db['policies'].update_many(
        {'status': 'processing'},
        {'$set': {'status': 'failed', 'error': 'Processing interrupted — please re-upload.'}}
    )
    print(f'Fixed {r.modified_count} stuck → failed')
    r2 = await db['policies'].count_documents({'status': 'ready'})
    print(f'Ready: {r2}')

asyncio.run(fix())

