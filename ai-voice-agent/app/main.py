from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.twilio_handler import router as twilio_router


# -------------------
from fastapi import FastAPI
from app.twilio_handler import router as twilio_router  # import the router
# -----------------
# ✅ Create only one FastAPI instance
app = FastAPI(title="AI Voice Agent")

# ✅ Mount static folder (optional, if you have frontend files)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ✅ Include Twilio router
app.include_router(twilio_router)

# ✅ Root route
@app.get("/")
def home():
    return {"message": "AI Voice Agent backend is running ✅"}

# ✅ Health check route
@app.get("/health")
def health():
    return {"status": "✅ AI Voice Agent running properly"}

