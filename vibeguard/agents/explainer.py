import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def explain_vulnerability(vulnerability, code_context=""):
    """Convert technical vulnerability into plain English."""
    
    prompt = f"""You are a security translator for non-technical founders. Convert this technical vulnerability into plain English.

VULNERABILITY:
Title: {vulnerability.get('title')}
Description: {vulnerability.get('description')}
Code context: {code_context[:200] if code_context else 'No code provided'}

Return ONLY valid JSON with this structure:
{{
  "plain_explanation": "One sentence explaining what's wrong, like you're talking to a 10-year-old. No technical terms.",
  "real_world_impact": "One sentence explaining what a hacker can ACTUALLY do. Use scary but truthful examples."
}}

Rules:
- NO CVE codes
- NO jargon (no 'sanitization', 'parameterization', 'XSS')
- Be direct and honest

Examples:
For SQL Injection: 
plain_explanation: "Your app is blindly trusting whatever users type into search boxes."
real_world_impact: "A hacker could type a single line of code and delete your entire customer database."

For Hardcoded Secret:
plain_explanation: "You left your house key under the doormat, and wrote the address on it."
real_world_impact: "Anyone who sees your code can pretend to be you and access your bank account."
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        return {
            "plain_explanation": result.get("plain_explanation", "Security issue found."),
            "real_world_impact": result.get("real_world_impact", "Hackers could exploit this.")
        }
        
    except Exception as e:
        print(f"Explainer error: {e}")
        return {
            "plain_explanation": f"Security issue: {vulnerability.get('title')}",
            "real_world_impact": "This vulnerability could be exploited by attackers."
        }

def explain_all_vulnerabilities(vulnerabilities, code=""):
    """Explain multiple vulnerabilities and return enriched list"""
    enriched_vulnerabilities = []
    for i, vuln in enumerate(vulnerabilities):
        explanation = explain_vulnerability(vuln, code)
        enriched_vuln = vuln.copy()
        enriched_vuln["plain_explanation"] = explanation["plain_explanation"]
        enriched_vuln["real_world_impact"] = explanation["real_world_impact"]
        enriched_vulnerabilities.append(enriched_vuln)
    
    return enriched_vulnerabilities
