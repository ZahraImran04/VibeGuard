import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def fix_code(original_code, vulnerabilities, language="auto"):
    """
    Generate fixed version of code with all vulnerabilities patched.
    Returns: fixed_code, list of changes made
    """
    
    vulns_text = "\n".join([
        f"- Line {v.get('line_hint', '?')}: {v.get('title')} - {v.get('description')}"
        for v in vulnerabilities
    ])
    
    prompt = f"""You are a security expert. Fix ALL vulnerabilities in this {language} code.

ORIGINAL CODE:
{original_code}

VULNERABILITIES TO FIX:
{vulns_text}

REQUIREMENTS:
1. Fix EVERY vulnerability listed above
2. Add inline comments explaining EACH security fix (start with "SECURITY FIX:")
3. Keep the original functionality working
4. Use security best practices

Return ONLY valid JSON with this structure:
{{
  "fixed_code": "the complete fixed code as a string",
  "changes": [
    "Changed SQL query to use parameterized statements",
    "Moved API key to environment variable",
    "Added input sanitization for XSS"
  ]
}}

FIX PATTERNS TO USE:
- SQL Injection: Use parameterized queries (?, %s placeholders) or ORM
- Hardcoded Secrets: Replace with os.getenv('VAR_NAME')
- XSS: Use textContent instead of innerHTML, or escape HTML entities
- Command Injection: Use subprocess.run with array arguments, avoid shell=True
- Path Traversal: Use os.path.basename() to sanitize
- Broken Auth: Add token validation checks

Return ONLY valid JSON. No markdown. No other text."""

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
            "fixed_code": result.get("fixed_code", original_code),
            "changes": result.get("changes", ["Fixed security vulnerabilities"])
        }
        
    except Exception as e:
        print(f"Fixer error: {e}")
        # Return original code with error note
        return {
            "fixed_code": f"# ERROR: Could not generate fix\n# {str(e)}\n\n{original_code}",
            "changes": [f"Fix generation failed: {str(e)}"]
        }

def generate_diff(original_code, fixed_code):
    """
    Generate a simple diff between original and fixed code.
    Returns HTML/markdown formatted diff
    """
    original_lines = original_code.split('\n')
    fixed_lines = fixed_code.split('\n')
    
    diff_lines = []
    
    # Simple line-by-line diff
    for i, line in enumerate(original_lines):
        if i < len(fixed_lines):
            if line.strip() != fixed_lines[i].strip():
                diff_lines.append(f"- {line}")
                diff_lines.append(f"+ {fixed_lines[i]}")
        else:
            diff_lines.append(f"- {line}")
    
    # Add any extra lines in fixed code
    for i in range(len(original_lines), len(fixed_lines)):
        diff_lines.append(f"+ {fixed_lines[i]}")
    
    return '\n'.join(diff_lines)
