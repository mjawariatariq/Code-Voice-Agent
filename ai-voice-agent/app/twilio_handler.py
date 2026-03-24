# from fastapi import APIRouter, Form, Response
# from twilio.twiml.voice_response import VoiceResponse
# import requests
# import tempfile
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai
# from app.utils.stt_tts import transcribe_audio
# from app.database import save_conversation
# from app.utils.rag_faq import get_faq_response

# # Router configuration should be in the main.py file, not here


# # ✅ Load environment variables
# load_dotenv()

# # ✅ Get Gemini API key from .env
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise ValueError("⚠️ Missing GEMINI_API_KEY in .env file!")

# # ✅ Configure Gemini client
# genai.configure(api_key=GEMINI_API_KEY)

# # ✅ Initialize FastAPI router
# router = APIRouter()

# LANG_MAPPING = {
#     "en": "Polly.Joanna",  # English female voice
#     "ur": "Polly.Aditi"    # Closest to Urdu/Hindi
# }

# @router.post("/twilio/voice")
# async def voice_webhook(
#     CallSid: str = Form(...),
#     From: str = Form(...),
#     RecordingUrl: str = Form(None),
#     lang: str = Form("en")
# ):
#     """Handle incoming Twilio calls and respond using Gemini AI."""
#     resp = VoiceResponse()

#     # Step 1️⃣: First prompt
#     if not RecordingUrl:
#         resp.say("Hello! This is your AI assistant. Please speak after the beep.",
#                  voice=LANG_MAPPING.get(lang, "Polly.Joanna"))
#         resp.record(play_beep=True, max_length=10, action="/twilio/voice")
#         return Response(content=str(resp), media_type="application/xml")

#     # Step 2️⃣: Fetch recording
#     try:
#         audio_url = f"{RecordingUrl}.wav"
#         audio_data = requests.get(audio_url).content
#     except Exception as e:
#         resp.say("Sorry, I could not retrieve your audio.")
#         print(f"❌ Error fetching audio: {e}")
#         return Response(content=str(resp), media_type="application/xml")

#     # Step 3️⃣: Transcribe
#     try:
#         with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
#             f.write(audio_data)
#             user_text = transcribe_audio(f.name)
#     except Exception as e:
#         resp.say("Sorry, I could not understand that. Please try again.")
#         print(f"❌ Transcription error: {e}")
#         return Response(content=str(resp), media_type="application/xml")

#     # Step 4️⃣: Check FAQ
#     faq_reply = get_faq_response(user_text)

#     # Step 5️⃣: Generate Gemini reply
#     prompt = faq_reply if faq_reply else f"Reply in {lang}: {user_text}"
#     try:
#         model = genai.GenerativeModel("gemini-2.0-flash")
#         response = model.generate_content(prompt)
#         ai_reply = response.text.strip()
#     except Exception as e:
#         ai_reply = "Sorry, something went wrong with the AI response."
#         print(f"❌ Gemini error: {e}")

#     # Step 6️⃣: Respond via Twilio
#     resp.say(ai_reply, voice=LANG_MAPPING.get(lang, "Polly.Joanna"))
#     resp.record(play_beep=True, max_length=10, action="/twilio/voice")

#     # Step 7️⃣: Save conversation
#     try:
#         save_conversation(user_text, ai_reply, lang)
#     except Exception as e:
#         print(f"⚠️ Database save error: {e}")

#     print(f"📞 Caller {From} said: {user_text}")
#     print(f"🤖 AI replied: {ai_reply}")

#     return Response(content=str(resp), media_type="application/xml")


from fastapi import APIRouter, Form, Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import requests
import tempfile
import os
from dotenv import load_dotenv
import google.generativeai as genai
from app.utils.stt_tts import transcribe_audio
from app.database import save_conversation
from app.utils.rag_faq import get_faq_response

# ✅ Load environment variables
load_dotenv()

# ✅ Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    raise ValueError("⚠️ Missing Twilio credentials in .env file!")

# ✅ Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("⚠️ Missing GEMINI_API_KEY in .env file!")

genai.configure(api_key=GEMINI_API_KEY)

# ✅ Initialize
router = APIRouter()
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

LANG_MAPPING = {
    "en": "Polly.Joanna",  # English female voice
    "ur": "Polly.Aditi"    # Closest Urdu/Hindi-like voice
}

# ---------------------------------------------------------------------
# 🔹 VOICE WEBHOOK - Handles incoming/ongoing call conversation
# ---------------------------------------------------------------------
@router.post("/twilio/voice")
async def voice_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    RecordingUrl: str = Form(None),
    lang: str = Form("en")
):
    """Handles Twilio call conversation with Gemini AI."""
    resp = VoiceResponse()

    # Step 1️⃣: Initial greeting + record user message
    if not RecordingUrl:
        resp.say("Hello! This is your AI assistant. Please speak after the beep.",
                 voice=LANG_MAPPING.get(lang, "Polly.Joanna"))
        resp.record(play_beep=True, max_length=10, action="/twilio/voice")
        return Response(content=str(resp), media_type="application/xml")

    # Step 2️⃣: Fetch audio recording
    try:
        audio_url = f"{RecordingUrl}.wav"
        audio_data = requests.get(audio_url).content
    except Exception as e:
        print(f"❌ Error fetching audio: {e}")
        resp.say("Sorry, I could not retrieve your audio.")
        return Response(content=str(resp), media_type="application/xml")

    # Step 3️⃣: Transcribe to text
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            user_text = transcribe_audio(f.name)
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        resp.say("Sorry, I could not understand that. Please try again.")
        return Response(content=str(resp), media_type="application/xml")

    # Step 4️⃣: Get AI reply
    faq_reply = get_faq_response(user_text)
    prompt = faq_reply if faq_reply else f"Reply in {lang}: {user_text}"

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        ai_reply = response.text.strip()
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        ai_reply = "Sorry, something went wrong while processing your request."

    # Step 5️⃣: Speak the response
    resp.say(ai_reply, voice=LANG_MAPPING.get(lang, "Polly.Joanna"))
    resp.record(play_beep=True, max_length=10, action="/twilio/voice")

    # Step 6️⃣: Save conversation
    try:
        save_conversation(user_text, ai_reply, lang)
    except Exception as e:
        print(f"⚠️ Database save error: {e}")

    print(f"📞 Caller {From} said: {user_text}")
    print(f"🤖 AI replied: {ai_reply}")

    return Response(content=str(resp), media_type="application/xml")


# ---------------------------------------------------------------------
# 🔹 MAKE CALL - Twilio calls your number automatically
# ---------------------------------------------------------------------
@router.get("/make_call")
def make_call(to_number: str):
    """
    Make Twilio call your phone and connect to AI assistant.
    Example:
      /make_call?to_number=+923001234567
    """
    try:
        call = client.calls.create(
            to=+923368966858,  # your number (e.g., +923001234567)
            from_=15673722574,  # your Twilio number
            url="https://your-ngrok-url.ngrok.io/twilio/voice"  # webhook URL
        )
        return {"message": "📞 Twilio is calling you!", "sid": call.sid}
    except Exception as e:
        print(f"❌ Twilio Call Error: {e}")
        return {"error": str(e)}
