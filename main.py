from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "registration_db")

app = FastAPI()

# CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
collection = db["registrations"]

# Pydantic schema
class TeamRegistration(BaseModel):
    teamName: str
    member1Name: str
    member1Email: EmailStr
    member1Usn: str
    member1Branch: str
    member2Name: str = ""
    member2Email: EmailStr = None
    member2Usn: str = ""
    member2Branch: str = ""

@app.get("/check-team")
async def check_team_name(teamName: str = Query(...)):
    team = await db.registrations.find_one({"teamName": teamName})
    if team:
        return {"exists": True}
    return {"exists": False}

@app.post("/register")
async def register_team(data: TeamRegistration):
    # Optional: check if team name already exists
    existing = await collection.find_one({"teamName": data.teamName})
    if existing:
        raise HTTPException(status_code=400, detail="Team name already registered.")

    # Insert into MongoDB
    await collection.insert_one(data.dict())
    return {"message": "Registration successful"}