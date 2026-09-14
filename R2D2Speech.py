import asyncio
import queue
import sounddevice as sd
import threading
import re
import time

from google import genai
from google.genai import types


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

TRANSCRIBE_MODEL = "gemini-3.5-transcribe-live"

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1600

client = genai.Client()

audio_queue = queue.Queue()
speaker_buffer = bytearray()
speaker_lock = threading.Lock()

speech_generation_done = threading.Event()
speech_playback_done = threading.Event()

speaker_active = False

is_speaking = False
audio_playing = False

CONVERSATION_TIMEOUT = 15

conversation_active = False
last_conversation_time = 0

WAKE_WORDS = [
    "hey r2d2",
    "hey r2 d2",
    "r2d2",
    "r2 d2",
    "r2"
]

# ---------------------------------------------------------
# Microphone callback
# ---------------------------------------------------------

def microphone_callback(indata, frames, time, status):

    global is_speaking

    if status:
        print("[MIC]", status)

    if is_speaking:
        return

    audio_queue.put(bytes(indata))


# ---------------------------------------------------------
# Start microphone
# ---------------------------------------------------------

def start_microphone():

    print("Starting microphone...")

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=CHANNELS,
        dtype="int16",
        callback=microphone_callback
    )

    stream.start()

    print("Microphone started.")

    return stream


# ---------------------------------------------------------
# Transcribe microphone
# ---------------------------------------------------------

async def transcribe_microphone():

    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        input_audio_transcription=types.AudioTranscriptionConfig()
    )

    print("Connecting to Gemini transcription...")

    async with client.aio.live.connect(
        model=TRANSCRIBE_MODEL,
        config=config
    ) as session:

        print("Connected to Gemini.")
        print("🎤 START SPEAKING\n")

        async def send_audio():

            while True:

                audio = await asyncio.to_thread(
                    audio_queue.get
                )

                if audio:

                    await session.send_realtime_input(
                        audio=types.Blob(
                            data=audio,
                            mime_type="audio/pcm;rate=16000"
                        )
                    )

        send_task = asyncio.create_task(send_audio())

        try:

            async for response in session.receive():

                if response.server_content is None:
                    continue

                transcription = response.server_content.input_transcription

                if transcription is not None:

                    text = transcription.text

                    if text:

                        print(
                            f"\nTRANSCRIPTION: {text}",
                            end="",
                            flush=True
                        )

                        yield text

        finally:
            send_task.cancel()


# ---------------------------------------------------------
# Test microphone
# ---------------------------------------------------------

def test_microphone():

    stream = start_microphone()

    try:

        asyncio.run(
            test_transcription()
        )

    except KeyboardInterrupt:

        print("\nStopping microphone...")

    finally:

        stream.stop()
        stream.close()


async def test_transcription():

    async for text in transcribe_microphone():

        print()
        
def voice_loop(send_function):

    mic_stream = start_microphone()
    speaker_stream = start_speaker()

    try:
        asyncio.run(
            _voice_loop(send_function)
        )

    except KeyboardInterrupt:
        print("\nReturning to text mode...")

    finally:
        mic_stream.stop()
        mic_stream.close()

        speaker_stream.stop()
        speaker_stream.close()

        print("Voice mode stopped.")


async def _voice_loop(send_function):

    global conversation_active
    global last_conversation_time

    exit_commands = [
        "exit voice mode",
        "stop voice mode",
        "disable voice mode",
        "turn off voice mode",
        "go to text mode",
        "switch to text mode",
        "stop listening",
        "stop",
        "exit"
    ]

    print("\n🔕 Waiting for wake word...")

    async for text in transcribe_microphone():

        if not text:
            continue

        # Normalize the transcription
        text_lower = normalize_wake_word(text)

        print(
            f"\n[VOICE LOOP] {text_lower}",
            flush=True
        )

        # -------------------------------------------------
        # EXIT COMMAND
        # Works even WITHOUT saying R2D2 first
        # -------------------------------------------------

        # Check for exit commands
        exit_text = re.sub(r"[.,!?;:'\"]", "", text_lower).strip()
        
        for command in exit_commands:
            if exit_text == command or exit_text.startswith(command + " "):
                print("\n🔇 Exiting voice mode...")
                conversation_active = False
                return

        # -------------------------------------------------
        # CHECK CONVERSATION TIMEOUT
        # -------------------------------------------------

        if conversation_active:

            if (
                time.time() - last_conversation_time
                >= CONVERSATION_TIMEOUT
            ):

                conversation_active = False

                print(
                    "\n🔕 Conversation timed out."
                )

                print(
                    "🎤 Say 'Hey R2D2' to wake me."
                )

        # -------------------------------------------------
        # FIND WAKE WORD
        # -------------------------------------------------

        sorted_wake_words = sorted(
            WAKE_WORDS,
            key=len,
            reverse=True
        )

        wake_word = None

        for word in sorted_wake_words:

            if word in text_lower:

                wake_word = word

                break

        # -------------------------------------------------
        # NOT CURRENTLY IN CONVERSATION
        # -------------------------------------------------

        if not conversation_active:

            # Ignore speech until wake word
            if wake_word is None:
                continue

            # Activate conversation
            conversation_active = True

            last_conversation_time = time.time()

            # Remove wake word
            command = text_lower.replace(
                wake_word,
                "",
                1
            ).strip()

            # Wake word by itself
            if not command:

                print(
                    "\n👋 R2D2 is listening..."
                )

                continue

        # -------------------------------------------------
        # ALREADY IN CONVERSATION
        # -------------------------------------------------

        else:

            # User doesn't need to say R2D2 anymore
            command = text_lower

            # If they happen to say R2D2 anyway,
            # remove it.
            if wake_word is not None:

                command = command.replace(
                    wake_word,
                    "",
                    1
                ).strip()

        # -------------------------------------------------
        # EMPTY COMMAND
        # -------------------------------------------------

        if not command:
            continue

        # -------------------------------------------------
        # UPDATE CONVERSATION TIMER
        # -------------------------------------------------

        last_conversation_time = time.time()

        # -------------------------------------------------
        # SEND TO GEMINI
        # -------------------------------------------------

        print(
            f"\nYou: {command}"
        )

        response = send_function(command)

        if response:

            print(
                f"R2D2: {response}\n"
            )

            speech_text = clean_for_speech(
                response
            )

            await generate_speech(
                speech_text
            )

            # Reset the timer AFTER R2D2 finishes talking
            last_conversation_time = time.time()
            
VOICE_MODEL = "gemini-3.1-flash-live-preview"

OUTPUT_SAMPLE_RATE = 24000


async def generate_speech(text):
    global speaker_active
    global is_speaking

    if not text:
        return

    # STOP LISTENING
    is_speaking = True

    speech_generation_done.clear()
    speech_playback_done.clear()

    with speaker_lock:
        speaker_buffer.clear()

    speaker_active = True

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=(
            "Read the provided text exactly as written. "
            "Do not summarize, paraphrase, shorten, add, or remove anything "
            "other than generated noises. "
            "Only convert the provided text into speech. "
            "Do not read the noises R2 makes. "
            "For grades, only read the class title and not the course number."
            "For all grades and assignments, read it in short simple sentences that makes flow easier."
        )
    )

    print("🔊 R2D2 speaking...")

    try:

        async with client.aio.live.connect(
            model=VOICE_MODEL,
            config=config
        ) as session:

            await session.send_realtime_input(text=text)

            async for response in session.receive():

                if response.server_content is None:
                    continue

                if response.server_content.model_turn:

                    for part in response.server_content.model_turn.parts:

                        if part.inline_data:
                            play_audio(part.inline_data.data)

                if response.server_content.turn_complete:
                    break

    except Exception as e:
        print(f"\n[VOICE ERROR] {e}")

    finally:
        # Gemini finished generating the audio
        speech_generation_done.set()

    # Wait until sounddevice has actually played everything
    await asyncio.to_thread(
        speech_playback_done.wait
    )

    # Remove any microphone audio that may have been queued
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break

    # START LISTENING AGAIN
    is_speaking = False

    print("🔇 R2D2 finished speaking.")
    print("🎤 Listening...")
            
def speak(text):


    if not text:
        return

    asyncio.run(
        generate_speech(text)
    )
    
def start_speaker():
    print("Starting speaker...")

    stream = sd.RawOutputStream(
        samplerate=OUTPUT_SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=2048,
        callback=speaker_callback
    )

    stream.start()

    print("Speaker started.")

    return stream

def speaker_callback(outdata, frames, time, status):
    global speaker_active

    if status:
        print("[SPEAKER]", status)

    bytes_needed = frames * 2

    with speaker_lock:
        if len(speaker_buffer) >= bytes_needed:
            audio = bytes(speaker_buffer[:bytes_needed])
            del speaker_buffer[:bytes_needed]

        else:
            audio = bytes(speaker_buffer)
            speaker_buffer.clear()

    # Fill the remainder with silence
    if len(audio) < bytes_needed:
        audio += b"\x00" * (bytes_needed - len(audio))

    outdata[:] = audio

    # Gemini has finished sending audio AND the buffer is empty
    with speaker_lock:
        if speech_generation_done.is_set() and len(speaker_buffer) == 0:
            speaker_active = False
            speech_playback_done.set()
    
def play_audio(audio_data):
    with speaker_lock:
        speaker_buffer.extend(audio_data)
    
def normalize_wake_word(text):

    text = text.lower().strip()

    replacements = {
        "hey artie": "hey r2d2",
        "artie": "r2d2",

        "hey r 2 d 2": "hey r2d2",
        "r 2 d 2": "r2d2",

        "hey r2 d2": "hey r2d2",
        "r2 d2": "r2d2",

        "hey r 2d 2": "hey r2d2",
        "r 2d 2": "r2d2",

        "hey r 2 d2": "hey r2d2",
        "r 2 d2": "r2d2",

        "hey r 2": "hey r2",
        "r 2": "r2",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

def clean_for_speech(text):
    # Remove Markdown bold
    text = text.replace("**", "")

    # Remove Markdown bullet markers
    text = re.sub(r"(?m)^\s*[\*\-]\s*", "", text)

    return text.strip()