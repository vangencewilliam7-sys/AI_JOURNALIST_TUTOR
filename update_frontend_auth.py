import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w') as f:
        f.write(content)

# 1. LandingPage.tsx
replace_in_file('d:/AI_JOURNALIST_TUTOR/frontend/src/pages/LandingPage.tsx', [
    ("import { useNavigate } from 'react-router-dom';", "import { useNavigate } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';"),
    ("const navigate = useNavigate();", "const navigate = useNavigate();\n  const { session } = useAuth();"),
    ("headers: { 'Content-Type': 'application/json' },", "headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session?.access_token}` },")
])

# 2. ScriptPage.tsx
replace_in_file('d:/AI_JOURNALIST_TUTOR/frontend/src/pages/ScriptPage.tsx', [
    ("import { useNavigate } from 'react-router-dom';", "import { useNavigate } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';"),
    ("const navigate = useNavigate();", "const navigate = useNavigate();\n  const { session } = useAuth();"),
    ("fetch(`http://localhost:9120/generate-script/${expertId}`, {", "fetch(`http://localhost:9120/generate-script`, { headers: { 'Authorization': `Bearer ${session?.access_token}` },"),
    ("fetch('http://localhost:9120/generate-script', {", "fetch('http://localhost:9120/generate-script', { headers: { 'Authorization': `Bearer ${session?.access_token}` },")
])

# 3. InterviewPage.tsx
replace_in_file('d:/AI_JOURNALIST_TUTOR/frontend/src/pages/InterviewPage.tsx', [
    ("import { useNavigate } from 'react-router-dom';", "import { useNavigate } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';"),
    ("const navigate = useNavigate();", "const navigate = useNavigate();\n  const { session } = useAuth();"),
    ("fetch(`http://localhost:9120/session/${sessionId}`)", "fetch(`http://localhost:9120/session/${sessionId}`, { headers: { 'Authorization': `Bearer ${session?.access_token}` } })"),
    ("headers: { 'Content-Type': 'application/json' },", "headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session?.access_token}` },"),
    ("fetch(`http://localhost:9120/end-session/${sessionId}`, { method: 'POST' });", "fetch(`http://localhost:9120/end-session/${sessionId}`, { method: 'POST', headers: { 'Authorization': `Bearer ${session?.access_token}` } });")
])

# 4. HomeworkPage.tsx
replace_in_file('d:/AI_JOURNALIST_TUTOR/frontend/src/pages/HomeworkPage.tsx', [
    ("import { useNavigate } from 'react-router-dom';", "import { useNavigate } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';"),
    ("const navigate = useNavigate();", "const navigate = useNavigate();\n  const { session } = useAuth();"),
    ("fetch(`${API_BASE_URL}/homework/${expertId}`)", "fetch(`${API_BASE_URL}/homework`, { headers: { 'Authorization': `Bearer ${session?.access_token}` } })"),
    ("headers: { 'Content-Type': 'application/json' },", "headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session?.access_token}` },"),
    ("fetch(`${API_BASE_URL}/start-session/${expertId}`, { method: 'POST' })", "fetch(`${API_BASE_URL}/start-session`, { method: 'POST', headers: { 'Authorization': `Bearer ${session?.access_token}` } })")
])

print("Replacements complete!")
