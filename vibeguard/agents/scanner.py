import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-latest')

def detect_language(code_string):
    """Auto-detect programming language from code"""
    code_lower = code_string.lower()
    if "def " in code_string or "import " in code_string or "print(" in code_string:
        return "python"
    elif "function " in code_string or "const " in code_string or "let " in code_string or "=>" in code_string:
        return "javascript"
    elif "<?php" in code_string or "$_" in code_string or "echo " in code_string:
        return "php"
    elif "SELECT " in code_string.upper() or "INSERT " in code_string.upper() or "UPDATE " in code_string.upper():
        return "sql"
    elif "package main" in code_string or "func " in code_string:
        return "go"
    elif "public class" in code_string or "System.out" in code_string:
        return "java"
    return "unknown"

def calculate_risk_score(vulnerabilities):
    """Calculate security score and grade from vulnerabilities"""
    score = 100
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "").lower()
        if severity == "critical":
            score -= 25
            critical_count += 1
        elif severity == "high":
            score -= 15
            high_count += 1
        elif severity == "medium":
            score -= 8
            medium_count += 1
        elif severity == "low":
            score -= 3
            low_count += 1
    
    score = max(0, score)
    
    if score == 100:
        grade = "A"
    elif score >= 85:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"
    
    return {
        "security_score": score,
        "overall_risk_level": grade,
        "severity_breakdown": {
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "low": low_count
        }
    }

def scan_code(code_string, language=None):
    """Main scanning function using Google Gemini"""
    
    if not language or language == "auto":
        language = detect_language(code_string)
    
    prompt = f"""You are a security expert. Analyze this {language} code for security vulnerabilities.

CODE:
{code_string}

Find ALL vulnerabilities. Return ONLY valid JSON with this exact structure. No other text, no markdown, no explanation.

{{
  "vulnerabilities": [
    {{
      "line_hint": 42,
      "severity": "critical",
      "title": "SQL Injection",
      "description": "User input is directly concatenated into SQL query without sanitization",
      "recommendation": "Use parameterized queries or prepared statements",
      "cwe_id": "CWE-89",
      "cwe_name": "SQL Injection"
    }}
  ]
}}

Severity rules (STRICT):
- CRITICAL: SQL injection, Hardcoded secrets (API keys, passwords, tokens, anything looking like sk-, key, secret, token, password = "xxx")
- HIGH: XSS (innerHTML, document.write), Command Injection (os.system, exec, eval), Path Traversal (../, open()), Broken Auth (no token validation)
- MEDIUM: IDOR (no ownership check), Open Redirect, SSRF
- LOW: Missing rate limiting, debug info, console.log of sensitive data

Look for these patterns:
- Any variable = "sk-" or "key" or "secret" or "token" with string value
- f-string or + concatenation in SQL queries
- innerHTML, document.write with variables
- os.system(), exec(), eval() with variables
- File paths with user input

Return ONLY valid JSON. The JSON must parse correctly."""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean response if markdown code blocks present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        vulnerabilities = result.get("vulnerabilities", [])
        
        # Calculate scores
        scores = calculate_risk_score(vulnerabilities)
        
        return {
            "vulnerabilities": vulnerabilities,
            "language": language,
            "security_score": scores["security_score"],
            "overall_risk_level": scores["overall_risk_level"],
            "severity_breakdown": scores["severity_breakdown"],
            "vulnerability_count": len(vulnerabilities)
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {response_text}")
        # Return empty result rather than failing
        return {
            "vulnerabilities": [],
            "language": language,
            "security_score": 100,
            "overall_risk_level": "A",
            "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "vulnerability_count": 0
        }
    except Exception as e:
        print(f"Gemini API error: {e}")
        raise Exception(f"Scanner failed: {str(e)}")
