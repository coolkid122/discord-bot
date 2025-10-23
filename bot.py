import os
import aiohttp
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
import re

app = FastAPI()

latest_code = None
MONITORED_CHANNEL_ID = 1429536067803021413
TOKEN = os.environ.get('TOKEN')

@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(monitor_discord_channel(TOKEN, MONITORED_CHANNEL_ID))
    yield

app.lifespan = lifespan

@app.get("/latest")
async def get_latest_code():
    return {"code": latest_code} if latest_code else {"error": "No code available"}

async def monitor_discord_channel(token, channel_id):
    global latest_code
    headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    async with aiohttp.ClientSession() as session:
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=1"
        async with session.get(url, headers=headers) as response:
            messages = await response.json()
            last_message_id = messages[0]['id'] if messages else None
        while True:
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages?after={last_message_id}&limit=10"
            async with session.get(url, headers=headers) as response:
                messages = await response.json()
                for message in reversed(messages):
                    await process_message(message, session)
                    last_message_id = message['id']
            await asyncio.sleep(0.5)

async def process_message(message, session):
    global latest_code
    if str(message['channel_id']) != str(MONITORED_CHANNEL_ID):
        return
    content = message.get('content', '')
    match = re.search(r'`([a-f0-9]{32})`', content)
    if match:
        code = match.group(1)
        latest_code = code
        print(f"New code: {code}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
