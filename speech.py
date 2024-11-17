import asyncio
from realtime_client import RealtimeClient

async def main():
    client = RealtimeClient()
    await client.connect()

    # Example: Send a sample audio snippet
    with open("sample_audio.wav", "rb") as f:
        audio_data = f.read()
        await client.send_audio(audio_data)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())