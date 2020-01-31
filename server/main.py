#!/usr/local/bin/python3

import asyncio
import json
import logging
import websockets
import datetime
from collections import namedtuple

logging.basicConfig()

class Message:
    def __init__(self, user, dt, text):
        self.user = user
        self.dt = dt
        self.text = text

    def serialize(self):
        return {
            "type": "MSG",
            "user": self.user,
            "time": self.dt.strftime("%Y-%m-%d %H:%M:%S"),
            "text": self.text
        }

USERS = set()
MSG_HISTORY = []

async def on_msg(user, text):
    # Add new message to message history
    msg = Message(str(user), datetime.datetime.now(), text)
    MSG_HISTORY.append(msg)
    # Send new message to all users
    data = json.dumps([msg.serialize()])
    await asyncio.wait([user.send(data) for user in USERS])

async def rewind(user):
    # Rewind message history to new user
    if len(MSG_HISTORY) == 0: return
    await asyncio.wait([user.send(json.dumps([msg.serialize() for msg in MSG_HISTORY]))])

async def register(ws):
    if ws in USERS: return
    USERS.add(ws)  # Each websocket is one user
    await rewind(ws)

async def unregister(websocket):
    USERS.remove(websocket)

async def handle(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "NEW":
                await on_msg(websocket, data["text"])
            else:
                logging.error("unsupported event: {}", data)
    finally:
        await unregister(websocket)

start_server = websockets.serve(handle, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
