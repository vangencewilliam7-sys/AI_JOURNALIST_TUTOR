import os
from dotenv import dotenv_values
from supabase import create_client, Client

env = dotenv_values(".env")
url: str = env.get("SUPABASE_URL")
key: str = env.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

res = supabase.table("interview_sessions").select("id, status, raw_transcript, snapshot").order("created_at", desc=True).limit(1).execute()
if res.data:
    session = res.data[0]
    print(f"Status: {session['status']}")
    print(f"Snapshot: {session['snapshot']}")
    transcript = session['raw_transcript']
    print(f"Transcript length: {len(transcript) if transcript else 0}")
    with open("transcript_debug.txt", "w", encoding="utf-8") as f:
        f.write(transcript or "")
else:
    print("No sessions found")
