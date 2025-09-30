import asyncio
import websockets
import os
import json
from datetime import datetime
from google.cloud import speech
from openai import AsyncOpenAI
from aiohttp import web
import urllib.parse

# Ensure you have your OpenAI API key set as an environment variable
# export OPENAI_API_KEY='your-api-key'
client = AsyncOpenAI()
MEETINGS_DIR = "backend/meetings"
KNOWLEDGE_BASE_FILE = "backend/knowledge_base.json"

def load_knowledge_base():
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        with open(KNOWLEDGE_BASE_FILE, 'r') as f:
            return json.load(f)
    return {"custom_terms": []}

async def analyze_transcript(transcript, websocket, meeting_file, language_code):
    print(f"Analyzing transcript: {transcript}")
    knowledge_base = load_knowledge_base()
    custom_terms_prompt = "\n".join([f"- {item['term']}: {item['definition']}" for item in knowledge_base.get("custom_terms", [])])

    system_prompt = f"""You are a meeting assistant. Your task is to analyze the provided transcript of a meeting in {language_code}.
    Extract key concepts, identify any questions asked, and provide a brief summary of the context.
    The response should be in {language_code}.
    Here is a list of custom terms and their definitions that might be mentioned:
    {custom_terms_prompt}
    Respond with a JSON object containing 'summary', 'questions', and 'concepts'."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript}
            ]
        )
        analysis = response.choices[0].message.content
        print(f"AI Analysis: {analysis}")

        with open(meeting_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n--- ANALYSIS ---\n{analysis}")

        if websocket.open:
            await websocket.send(analysis)
    except Exception as e:
        print(f"Error analyzing transcript: {e}")

async def audio_handler(websocket, path):
    print("Client connected")

    query_params = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
    language_code = query_params.get('language', ['en-US'])[0]
    print(f"Language selected: {language_code}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    meeting_file = os.path.join(MEETINGS_DIR, f"meeting_{timestamp}.txt")
    print(f"Saving meeting to {meeting_file}")

    try:
        speech_client = speech.SpeechAsyncClient()
    except Exception as e:
        print(f"Failed to create SpeechAsyncClient: {e}")
        await websocket.close(code=1011, reason="Speech client initialization failed")
        return

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz=48000,
        language_code=language_code,
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    async def request_generator():
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
        try:
            while True:
                audio_chunk = await websocket.recv()
                if audio_chunk:
                    yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)
        except websockets.exceptions.ConnectionClosed:
            print("Client connection closed.")
        except Exception as e:
            print(f"Error in request_generator: {e}")

    print("Starting transcription stream...")
    responses = speech_client.streaming_recognize(requests=request_generator())

    try:
        full_transcript = []
        async for response in responses:
            for result in response.results:
                transcript = result.alternatives[0].transcript
                if result.is_final:
                    print(f"Final transcript: {transcript}")
                    full_transcript.append(transcript)

                    with open(meeting_file, "a", encoding="utf-8") as f:
                        f.write(f"{transcript}\n")

                    await analyze_transcript(transcript, websocket, meeting_file, language_code)
                else:
                    interim_message = json.dumps({"type": "interim", "transcript": transcript})
                    if websocket.open:
                        await websocket.send(interim_message)
                    print(f"Interim transcript: {transcript}")
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
    finally:
        print("Transcription stream ended.")

async def search_handler(request):
    query = request.rel_url.query.get('q', '')
    if not query:
        return web.json_response({'error': 'Query parameter "q" is required.'}, status=400)

    results = []
    for filename in os.listdir(MEETINGS_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(MEETINGS_DIR, filename)
            with open(filepath, 'r', encoding="utf-8") as f:
                for line in f:
                    if query.lower() in line.lower():
                        results.append({'file': filename, 'line': line.strip()})

    return web.json_response(results)

async def get_knowledge_base(request):
    knowledge_base = load_knowledge_base()
    return web.json_response(knowledge_base)

async def update_knowledge_base(request):
    data = await request.json()
    with open(KNOWLEDGE_BASE_FILE, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return web.json_response({"status": "success"})

async def main():
    os.makedirs(MEETINGS_DIR, exist_ok=True)

    websocket_server = websockets.serve(audio_handler, "localhost", 8765)

    app = web.Application()
    app.router.add_get("/search", search_handler)
    app.router.add_get("/knowledge-base", get_knowledge_base)
    app.router.add_post("/knowledge-base", update_knowledge_base)

    http_runner = web.AppRunner(app)
    await http_runner.setup()
    http_site = web.TCPSite(http_runner, 'localhost', 8080)

    print("WebSocket server started at ws://localhost:8765")
    print("HTTP server started at http://localhost:8080")

    await asyncio.gather(
        websocket_server,
        http_site.start()
    )

    await http_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")