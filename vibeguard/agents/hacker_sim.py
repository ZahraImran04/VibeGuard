import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def simulate_attack(original_code, fixed_code, vulnerabilities, language="auto"):
    """
    Generate dramatic hacker simulation for vulnerable vs fixed code.
    Returns terminal-style simulation text
    """
    
    vulns_text = "\n".join([
        f"- {v.get('title')} at line {v.get('line_hint', '?')}"
        for v in vulnerabilities[:3]  # Top 3 most critical
    ])
    
    prompt = f"""You are creating a dramatic hacker terminal simulation for a cybersecurity demo.

LANGUAGE: {language}

VULNERABILITIES IN ORIGINAL CODE:
{vulns_text}

Create a realistic terminal simulation showing:
1. Hacker attacking the VULNERABLE code (attack succeeds)
2. Hacker attacking the FIXED code (attack fails with "ACCESS DENIED")

Style requirements:
- Use green text on black background style
- Start each line with "$ " for commands
- Use dramatic hacker language but keep it realistic
- Show actual attack steps (enumeration, exploitation, payload)
- For vulnerable code: Show SUCCESS and data breach
- For fixed code: Show "ACCESS DENIED" or "BLOCKED"

Example format:
$ nmap -p 80,443 target.com
$ sqlmap -u "https://target.com/user?id=1" --dbs
[VULNERABLE] Database found: customer_db
$ python exploit.py --payload "'; DROP TABLE users; --"
[SUCCESS] 15,234 user records extracted! Including passwords!

--- ATTACKING PATCHED CODE ---
$ python exploit.py --payload "'; DROP TABLE users; --"
[BLOCKED] Access denied. Parameterized query detected.
$ exit

Make it exciting but believable. Keep under 30 lines total."""
    
    try:
        response = model.generate_content(prompt)
        simulation_text = response.text.strip()
        
        # Add formatting
        full_simulation = f"""
┌─────────────────────────────────────────────────────────────┐
│                    🔴 HACKER SIMULATION 🔴                    │
│              Testing your code against real attacks           │
└─────────────────────────────────────────────────────────────┘

{simulation_text}

┌─────────────────────────────────────────────────────────────┐
│                      SIMULATION RESULT                       │
├─────────────────────────────────────────────────────────────┤
│  ORIGINAL CODE: 🔴 VULNERABLE - Would be hacked              │
│  FIXED CODE:   🟢 SECURE - Attack blocked                    │
└─────────────────────────────────────────────────────────────┘
"""
        return full_simulation
        
    except Exception as e:
        print(f"Hacker sim error: {e}")
        return f"""
┌─────────────────────────────────────────────────────────────┐
│                    🔴 HACKER SIMULATION 🔴                    │
└─────────────────────────────────────────────────────────────┘

$ whoami
hacker

$ # Attempting to exploit vulnerabilities...
$ sqlmap -u "http://target.com/user?id=1" --dbs

[VULNERABLE CODE - ATTACK SUCCEEDS]
[+] Database found! Extracting user data...
[+] SUCCESS! 1,234 user records compromised.

[FIXED CODE - ATTACK FAILS]
[-] Parameterized query detected. Attack blocked.
[-] ACCESS DENIED - Your code is secure.

┌─────────────────────────────────────────────────────────────┐
│  ORIGINAL CODE: 🔴 VULNERABLE                                │
│  FIXED CODE:   🟢 SECURE                                     │
└─────────────────────────────────────────────────────────────┘
"""
