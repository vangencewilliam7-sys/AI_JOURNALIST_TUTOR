import re

with open('c:/Users/vardh/OneDrive/Desktop/ai_journalist_tutor/backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Header import
content = content.replace('from fastapi import FastAPI, HTTPException, UploadFile, File', 'from fastapi import FastAPI, HTTPException, UploadFile, File, Header')

# 2. Update Prompts imports
content = content.replace('JOURNALIST_BASE_PERSONA', 'COURSE_ARCHITECT_PERSONA')

# 3. Update hybrid_rag_fetch
content = re.sub(r'def hybrid_rag_fetch\(query: str, top_k: int = 4\) -> dict:', 'def hybrid_rag_fetch(query: str, user_id: str, top_k: int = 4) -> dict:', content)
content = content.replace('"match_threshold": 0.3,\n            "match_count": top_k', '"match_threshold": 0.3,\n            "match_count": top_k,\n            "p_user_id": user_id')
content = content.replace('select("*, knowledge_sources(title, source_type)").ilike("content", f"%{query[:15]}%").limit(top_k).execute()', 'select("*, knowledge_sources(title, source_type)").eq("user_id", user_id).ilike("content", f"%{query[:15]}%").limit(top_k).execute()')

# 4. Update research_scan
content = re.sub(r'async def research_scan\(\) -> dict:', 'async def research_scan(user_id: str) -> dict:', content)
content = content.replace('select("id, title, source_type").execute()', 'select("id, title, source_type").eq("user_id", user_id).execute()')
content = content.replace('select("content, location_marker").eq("source_id", s["id"]).limit(30).execute()', 'select("content, location_marker").eq("source_id", s["id"]).eq("user_id", user_id).limit(30).execute()')

# 5. Update Endpoints to use x_user_id
content = re.sub(r'async def ingest_youtube_endpoint\(request: YoutubeIngestRequest\):', 'async def ingest_youtube_endpoint(request: YoutubeIngestRequest, x_user_id: str = Header(...)):', content)
content = content.replace('"url_or_identifier": request.url', '"url_or_identifier": request.url,\n            "user_id": x_user_id')
content = content.replace('"chunk_index": idx', '"chunk_index": idx,\n                "user_id": x_user_id')

content = re.sub(r'async def ingest_documents_endpoint\(files: List\[UploadFile\] = File\(\.\.\.\)\):', 'async def ingest_documents_endpoint(files: List[UploadFile] = File(...), x_user_id: str = Header(...)):', content)
content = content.replace('"url_or_identifier": f"upload:{file.filename}"', '"url_or_identifier": f"upload:{file.filename}",\n                "user_id": x_user_id')
content = content.replace('"chunk_index": idx', '"chunk_index": idx,\n                    "user_id": x_user_id')

content = re.sub(r'async def list_knowledge_sources\(\):', 'async def list_knowledge_sources(x_user_id: str = Header(...)):', content)
content = content.replace('select("id, title, source_type, url_or_identifier, created_at").order("created_at", desc=True).execute()', 'select("id, title, source_type, url_or_identifier, created_at").eq("user_id", x_user_id).order("created_at", desc=True).execute()')
content = content.replace('select("id", count="exact").eq("source_id", source["id"]).execute()', 'select("id", count="exact").eq("source_id", source["id"]).eq("user_id", x_user_id).execute()')

content = re.sub(r'async def delete_knowledge_source\(source_id: str\):', 'async def delete_knowledge_source(source_id: str, x_user_id: str = Header(...)):', content)
content = content.replace('eq("source_id", source_id).execute()', 'eq("source_id", source_id).eq("user_id", x_user_id).execute()')
content = content.replace('eq("id", source_id).execute()', 'eq("id", source_id).eq("user_id", x_user_id).execute()')

content = re.sub(r'async def delete_all_knowledge_sources\(\):', 'async def delete_all_knowledge_sources(x_user_id: str = Header(...)):', content)
content = content.replace('neq("id", "00000000-0000-0000-0000-000000000000").execute()', 'eq("user_id", x_user_id).execute()')

content = re.sub(r'async def prepare_interview_endpoint\(request: PrepareRequest\):', 'async def prepare_interview_endpoint(request: PrepareRequest, x_user_id: str = Header(...)):', content)
content = content.replace('scan_data = await research_scan()', 'scan_data = await research_scan(x_user_id)')
content = content.replace('"session_id": session_id,', '"session_id": session_id,\n            "user_id": x_user_id,')

content = re.sub(r'async def generate_next_question_endpoint\(request: InterviewRequest\):', 'async def generate_next_question_endpoint(request: InterviewRequest, x_user_id: str = Header(...)):', content)
content = content.replace('formatted_persona = JOURNALIST_BASE_PERSONA.replace("{topic}", topic)', 'formatted_persona = COURSE_ARCHITECT_PERSONA.replace("{topic}", topic)')
content = content.replace('ensure_session(session_id, topic)', 'ensure_session(session_id, topic, x_user_id)')
content = content.replace('rag_data = hybrid_rag_fetch(expert_answer)', 'rag_data = hybrid_rag_fetch(expert_answer, x_user_id)')
content = content.replace('await reactive_generate_question(request, formatted_persona)', 'await reactive_generate_question(request, formatted_persona, x_user_id)')
content = content.replace('supabase.table("interview_scripts").select("*").eq("session_id", session_id).execute()', 'supabase.table("interview_scripts").select("*").eq("session_id", session_id).eq("user_id", x_user_id).execute()')
content = content.replace('supabase.table("interview_scripts").update({"questions_completed": new_completed}).eq("session_id", session_id).execute()', 'supabase.table("interview_scripts").update({"questions_completed": new_completed}).eq("session_id", session_id).eq("user_id", x_user_id).execute()')
content = content.replace('supabase.table("interview_scripts").update({"status": "completed"}).eq("session_id", session_id).execute()', 'supabase.table("interview_scripts").update({"status": "completed"}).eq("session_id", session_id).eq("user_id", x_user_id).execute()')

content = re.sub(r'async def reactive_generate_question\(request, persona\):', 'async def reactive_generate_question(request, persona, user_id):', content)
content = content.replace('hybrid_rag_fetch(request.expert_answer)', 'hybrid_rag_fetch(request.expert_answer, user_id)')

content = re.sub(r'async def end_interview_endpoint\(session_id: str\):', 'async def end_interview_endpoint(session_id: str, x_user_id: str = Header(...)):', content)
content = content.replace('await synthesize_knowledge_endpoint(session_id)', 'await synthesize_knowledge_endpoint(session_id, x_user_id)')
content = content.replace('supabase.table("conversation_sessions").select("id").eq("session_id", session_id).execute()', 'supabase.table("conversation_sessions").select("id").eq("session_id", session_id).eq("user_id", x_user_id).execute()')
content = content.replace('supabase.table("conversation_sessions").update({', 'supabase.table("conversation_sessions").update({') # No need to replace user_id here as we use PK.
content = content.replace('supabase.table("interview_scripts").update({\n            "status": "ended_early"\n        }).eq("session_id", session_id).execute()', 'supabase.table("interview_scripts").update({\n            "status": "ended_early"\n        }).eq("session_id", session_id).eq("user_id", x_user_id).execute()')
content = content.replace('supabase.table("interview_scripts").select("*").eq("session_id", session_id).execute()', 'supabase.table("interview_scripts").select("*").eq("session_id", session_id).eq("user_id", x_user_id).execute()')

content = re.sub(r'async def synthesize_knowledge_endpoint\(session_id: str\):', 'async def synthesize_knowledge_endpoint(session_id: str, x_user_id: str = Header(...)):', content)
content = content.replace('supabase.table("tacit_knowledge_reports")', 'supabase.table("course_blueprints")')
content = content.replace('supabase.table("conversation_sessions").select("id").eq("session_id", session_id).execute()', 'supabase.table("conversation_sessions").select("id").eq("session_id", session_id).eq("user_id", x_user_id).execute()')
content = content.replace('supabase.table("interview_scripts").select("themes, questions_completed, total_questions").eq("session_id", session_id).execute()', 'supabase.table("interview_scripts").select("themes, questions_completed, total_questions").eq("session_id", session_id).eq("user_id", x_user_id).execute()')
content = content.replace('supabase.table("interview_scripts").update({\n                "status": "synthesized"\n            }).eq("session_id", session_id).execute()', 'supabase.table("interview_scripts").update({\n                "status": "synthesized"\n            }).eq("session_id", session_id).eq("user_id", x_user_id).execute()')

content = content.replace('"session_id": session_id,\n                "report_title": report_data.get("report_title", "Knowledge Report"),', '"session_id": session_id,\n                "user_id": x_user_id,\n                "course_title": report_data.get("course_title", "Course Blueprint"),')
content = content.replace('"expert_domain": report_data.get("expert_domain", ""),', '"target_audience": report_data.get("target_audience", ""),')
content = content.replace('"tacit_insights": report_data.get("tacit_insights", []),', '"course_modules": report_data.get("course_modules", []),')
content = content.replace('"mental_models": report_data.get("mental_models", []),', '"marketing_hooks": report_data.get("marketing_hooks", []),')
content = content.replace('"pattern_breaks": report_data.get("pattern_breaks", []),\n                "war_stories": report_data.get("war_stories", []),\n                "actionable_playbooks": report_data.get("actionable_playbooks", []),\n                "knowledge_gaps": report_data.get("knowledge_gaps", []),', '')

content = re.sub(r'async def get_knowledge_report\(session_id: str\):', 'async def get_knowledge_report(session_id: str, x_user_id: str = Header(...)):', content)
content = content.replace('supabase.table("course_blueprints").select("*").eq("session_id", session_id).order("created_at", desc=True).limit(1).execute()', 'supabase.table("course_blueprints").select("*").eq("session_id", session_id).eq("user_id", x_user_id).order("created_at", desc=True).limit(1).execute()')
# Update returned dict keys for get_knowledge_report
content = content.replace('"report_title": record.get("report_title"),', '"course_title": record.get("course_title"),')
content = content.replace('"expert_domain": record.get("expert_domain"),', '"target_audience": record.get("target_audience"),')
content = content.replace('"tacit_insights": record.get("tacit_insights", []),', '"course_modules": record.get("course_modules", []),')
content = content.replace('"mental_models": record.get("mental_models", []),', '"marketing_hooks": record.get("marketing_hooks", []),')
content = content.replace('"pattern_breaks": record.get("pattern_breaks", []),\n            "war_stories": record.get("war_stories", []),\n            "actionable_playbooks": record.get("actionable_playbooks", []),\n            "knowledge_gaps": record.get("knowledge_gaps", [])', '')

content = re.sub(r'def ensure_session\(session_id: str, topic: str\) -> str:', 'def ensure_session(session_id: str, topic: str, user_id: str) -> str:', content)
content = content.replace('supabase.table("conversation_sessions").select("id").eq("session_id", session_id).execute()', 'supabase.table("conversation_sessions").select("id").eq("session_id", session_id).eq("user_id", user_id).execute()')
content = content.replace('"session_id": session_id,', '"session_id": session_id,\n                "user_id": user_id,')

with open('c:/Users/vardh/OneDrive/Desktop/ai_journalist_tutor/backend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('app.py updated successfully.')
