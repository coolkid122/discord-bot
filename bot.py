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
        try:
            async with session.get(url, headers=headers) as response:
                print(f"Initial request status: {response.status}")
                if response.status != 200:
                    print(f"Initial request failed: {await response.text()}")
                    return
                messages = await response.json()
                print(f"Initial messages: {len(messages)} messages")
                last_message_id = messages[0]['id'] if messages else None
        except Exception as e:
            print(f"Initial request error: {str(e)}")
            return
        while True:
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages?after={last_message_id}&limit=10"
            try:
                async with session.get(url, headers=headers) as response:
                    print(f"Poll status: {response.status}")
                    if response.status != 200:
                        print(f"Poll failed: {await response.text()}")
                        continue
                    messages = await response.json()
                    print(f"Polled messages: {len(messages)} messages")
                    for message in reversed(messages):
                        await process_message(message, session)
                        last_message_id = message['id']
            except Exception as e:
                print(f"Poll error: {str(e)}")
            await asyncio.sleep(0.5)

async def process_message(message, session):
    global latest_code
    if str(message['channel_id']) != str(MONITORED_CHANNEL_ID):
        print(f"Skipping message from channel: {message['channel_id']}")
        return
    content = message.get('content', '')
    print(f"Processing message content: {content}")
    # Try both backtick and plain hex code patterns
    match = re.search(r'`([a-f0-9]{32})`', content, re.MULTILINE) or re.search(r'\b([a-f0-9]{32})\b', content, re.MULTILINE)
    if match:
        code = match.group(1)
        latest_code = code
        print(f"New code: {code}")
    else:
        print("No hex code found in message")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
