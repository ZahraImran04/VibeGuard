from supabase import create_client, Client
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_client() -> Client:
    """Initialize and return Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def save_scan(scan_id, repo_url, repo_name, repo_owner, language, stars, security_score, files_scanned, overall_risk_level):
    """Insert a new scan record"""
    client = get_client()
    data = {
        "id": scan_id,
        "repo_url": repo_url,
        "repo_name": repo_name,
        "repo_owner": repo_owner,
        "language": language,
        "stars": stars or 0,
        "security_score": security_score,
        "files_scanned": files_scanned,
        "overall_risk_level": overall_risk_level,
        "status": "complete"
    }
    return client.table("scans").insert(data).execute()

def save_vulnerabilities(scan_id, vulnerabilities_list):
    """Bulk insert vulnerabilities for a scan"""
    client = get_client()
    records = []
    for vuln in vulnerabilities_list:
        records.append({
            "scan_id": scan_id,
            "file_path": vuln.get("file_path", "unknown"),
            "title": vuln.get("title"),
            "description": vuln.get("description"),
            "severity": vuln.get("severity"),
            "line_hint": vuln.get("line_hint"),
            "recommendation": vuln.get("recommendation", ""),
            "plain_explanation": vuln.get("plain_explanation", ""),
            "real_world_impact": vuln.get("real_world_impact", ""),
            "cwe_id": vuln.get("cwe_id"),
            "cwe_name": vuln.get("cwe_name")
        })
    if records:
        return client.table("vulnerabilities").insert(records).execute()
    return None

def save_fix(scan_id, file_path, vulnerable_code, fixed_code, fix_explanation, effort):
    """Save fix results to database"""
    client = get_client()
    data = {
        "scan_id": scan_id,
        "file_path": file_path,
        "vulnerable_code": vulnerable_code,
        "fixed_code": fixed_code,
        "fix_explanation": fix_explanation,
        "effort": effort
    }
    return client.table("fixes").insert(data).execute()

def save_hacker_report(scan_id, attack_narrative, most_critical_vulnerability, estimated_breach_time, attack_steps, overall_risk_level):
    """Save hacker simulation report to database"""
    client = get_client()
    data = {
        "scan_id": scan_id,
        "attack_narrative": attack_narrative,
        "most_critical_vulnerability": most_critical_vulnerability,
        "estimated_breach_time": estimated_breach_time,
        "attack_steps": json.dumps(attack_steps) if isinstance(attack_steps, list) else attack_steps,
        "overall_risk_level": overall_risk_level
    }
    return client.table("hacker_reports").insert(data).execute()

def get_scan(scan_id):
    """Retrieve scan by ID"""
    client = get_client()
    return client.table("scans").select("*").eq("id", scan_id).execute()

def get_vulnerabilities(scan_id):
    """Retrieve all vulnerabilities for a scan"""
    client = get_client()
    return client.table("vulnerabilities").select("*").eq("scan_id", scan_id).execute()

def get_fixes(scan_id):
    """Retrieve fixes for a scan"""
    client = get_client()
    return client.table("fixes").select("*").eq("scan_id", scan_id).execute()

def get_hacker_reports(scan_id):
    """Retrieve hacker reports for a scan"""
    client = get_client()
    return client.table("hacker_reports").select("*").eq("scan_id", scan_id).execute()
