import asyncio
import os
import json
from dotenv import load_dotenv

# Load env vars
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path, override=True)

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from supabase import create_client
from domains.interview import InterviewDomain

async def main():
    SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_DB_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Missing Supabase credentials in .env")
        return
        
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, timeout=300)
    llm_fast = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_tokens=1500, timeout=60)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    domain = InterviewDomain(llm, supabase, llm_fast, embeddings)
    
    # 1. Fetch any existing expert from the DB
    res = supabase.table("experts").select("id").limit(1).execute()
    if not res.data:
        print("No experts found in DB. Please create one via UI first.")
        return
    expert_id = res.data[0]["id"]
    print(f"Using Expert ID: {expert_id}")
    
    # 2. Setup Session
    print("Setting up session...")
    source_res = supabase.table("knowledge_sources").insert({
        "source_type": "transcript",
        "title": f"Simulated Interview",
        "global_summary": "Auto-generated vector memory for simulated session.",
        "author_or_channel": "Simulation Script"
    }).execute()
    source_id = source_res.data[0]["id"]
    
    session_res = supabase.table("interview_sessions").insert({
        "expert_id": expert_id,
        "iteration_number": 1,
        "status": "active",
        "live_transcript_source_id": source_id
    }).execute()
    session_id = session_res.data[0]["id"]
    print(f"Created Session: {session_id}")
    
    # 3. Generate Script
    print("\nGenerating Script (Testing the script generator prompt)...")
    script = await domain.generate_script(expert_id)
    print("Script Generated!")
    with open("sim_script.json", "w") as f:
        json.dump(script, f, indent=2)
    print("Saved generated script to: backend/sim_script.json")
    
    # 4. Simulate Live Turns
    print("\n⏳ Simulating Live Interview Turns...")
    dummy_answers = [
        "My origin story is I started in cloud engineering 10 years ago and saw how complex it was getting.",
        "A major challenge was scaling the database to handle 1M requests per minute without crashing.",
        "The core modules of my course should definitely be Cloud Architecture, Advanced Security, and Cost Optimization.",
        "For the security module, we need to cover IAM roles, Encryption at rest, and VPC networking.",
        "My overarching mental model is to always design for failure. If you assume everything will break, you build resilient systems."
    ]
    
    print("--- SIMULATION STARTED ---")
    print("1. Intaking expert...")
    intake_res = await domain.intake(expert_id)
    
    print("2. Generating Script...")
    script_data = await domain.generate_script(expert_id)
    
    with open("sim_script.json", "w") as f:
        json.dump(script_data, f, indent=2)
    print("Saved script to sim_script.json")

    # 3. Simulate live turns
    print("3. Simulating Live Turns...")
    # Get active block name from script if possible
    active_block = "General Topic"
    try:
        mod = script_data.get("module_backlog", [])[0]
        active_block = f"{mod['module_title']} - {mod['topics'][0]['topic_title']}"
    except:
        pass

    for i, answer in enumerate(dummy_answers):
        print(f"Turn {i+1}...")
        turn_res = await domain.live_turn(session_id, answer)
        print(f"AI Next Question: {turn_res.get('question')}")
        
    # 4. End Session (Synthesis)
    print("4. Synthesizing Session...")
    supabase.table("interview_sessions").update({"status": "completed"}).eq("id", session_id).execute()
    
    synthesis_data = await domain.synthesize(session_id)
    
    with open("sim_synthesis.json", "w") as f:
        json.dump(synthesis_data, f, indent=2)
        
    print("Saved synthesis to sim_synthesis.json")
    print("--- SIMULATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(main())
