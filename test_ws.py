import asyncio
import websockets

async def test():
    uri = "ws://127.0.0.1:8081/ws/webrtc/?token=fake_token"
    try:
        print(f"Connecting to {uri}")
        async with websockets.connect(uri) as ws:
            print("OPEN")
    except Exception as e:
        print('ERROR TYPE:', type(e))
        print('ERROR:', e)
        if hasattr(e, 'response'):
            print("Response status:", e.response.status_code)
            print("Response Headers:")
            for k, v in e.response.headers.items():
                print(f"{k}: {v}")

asyncio.run(test())
