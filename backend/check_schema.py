import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase = create_client(url, key)

tables = ["interview_sessions", "homework_ledger", "expert_profile", "tacit_knowledge_reports", "curriculum_blueprints", "experts"]
for t in tables:
    try:
        res = supabase.table(t).select('*').limit(1).execute()
        if res.data:
            print(f"{t}: {len(res.data[0].keys())} columns")
        else:
            # Insert a dummy row and rollback or just look at error
            pass
    except Exception as e:
        print(f"{t}: {e}")
