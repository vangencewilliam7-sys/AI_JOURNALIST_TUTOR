import os
from dotenv import dotenv_values
from supabase import create_client, Client

env = dotenv_values(".env")
url: str = env.get("SUPABASE_URL")
key: str = env.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

res = supabase.table("interview_sessions").select("id, status, raw_transcript, snapshot").order("created_at", desc=True).limit(1).execute()
if res.data:
    print(f"Status: {res.data[0]['status']}")
    print(f"Snapshot: {res.data[0]['snapshot']}")
    print(f"Transcript length: {len(res.data[0]['raw_transcript']) if res.data[0]['raw_transcript'] else 0}")
    print(f"Transcript Content: {res.data[0]['raw_transcript']}")
else:
    print("No sessions found")
