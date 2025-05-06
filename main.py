from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import Optional, Union
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
    member2Email: Union[EmailStr, str, None] = ""
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
     # Debugging line to check the data being inserted
    # Insert into MongoDB
    await collection.insert_one(data.dict())
    return {"message": "Registration successful"}

def extract_year(usn: str) -> str:
    """Extract year from USN (e.g., '4MT23EC045' -> '23')"""
    usn = usn.strip().upper()
    return usn[3:5]

def extract_branch(usn: str) -> str:
    """Extract branch from USN (e.g., '4MT23EC045' -> 'EC')"""
    usn = usn.strip().upper()
    return usn[5:7]

@app.get("/api/total-participants")
async def total_participants():
    total = 0
    teams = 0
    async for doc in collection.find():
        if doc.get("member1Usn"): 
            total += 1
            teams += 1
        if doc.get("member2Usn"): total += 1
    return {"total_participants": total, "total_teams": teams}

@app.get("/api/participants-by-year")
async def participants_by_year():
    year_counts = {}
    async for doc in collection.find():
        for usn in [doc.get("member1Usn", ""), doc.get("member2Usn", "")]:
            year = extract_year(usn.strip())
            if len(year) == 2:
                year_counts[year] = year_counts.get(year, 0) + 1
    return {"participants_by_year": year_counts}

@app.get("/api/participants-by-branch")
async def participants_by_branch():
    branch_counts = {}
    async for doc in collection.find():
        for usn in [doc.get("member1Usn", ""), doc.get("member2Usn", "")]:
            branch = extract_branch(usn.strip())
            if len(branch) == 2:
                # Check if the branch is valid (e.g., 'EC', 'CS', etc.)
                branch_counts[branch] = branch_counts.get(branch, 0) + 1
    return {"participants_by_branch": branch_counts}
