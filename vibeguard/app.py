from flask import Flask, request, jsonify, redirect, render_template
from flask_cors import CORS
import uuid
from datetime import datetime
from dotenv import load_dotenv
import os

from agents.scanner import scan_code
from agents.explainer import explain_all_vulnerabilities
from agents.fixer import fix_code
from agents.hacker_sim import simulate_attack
from services.supabase_client import save_scan, save_vulnerabilities, get_scan, get_vulnerabilities, save_fix, save_hacker_report, get_fixes, get_hacker_reports
from services.github import exchange_code_for_token, create_pull_request

load_dotenv()

app = Flask(__name__)
CORS(app)

# Store temporary GitHub tokens (in production use session/DB)
github_tokens = {}

@app.route('/', methods=['GET'])
def index():
    """Serve the frontend UI"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "VibeGuard API running",
        "message": "All agents ready - Scanner, Explainer, Fixer, Hacker Sim",
        "version": "1.0.0",
        "ai_model": "gemini-1.5-flash"
    })

@app.route('/scan', methods=['POST'])
def scan():
    """Main scan endpoint - analyzes code for vulnerabilities"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({"error": "Missing 'code' field"}), 400
        
        code = data['code']
        language = data.get('language', 'auto')
        repo_url = data.get('repo_url', 'paste')
        repo_name = data.get('repo_name', 'manual')
        repo_owner = data.get('repo_owner', 'user')
        
        if not code or len(code.strip()) == 0:
            return jsonify({"error": "Code cannot be empty"}), 400
        
        # Run the scanner
        scan_result = scan_code(code, language)
        
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Save to Supabase
        try:
            save_scan(
                scan_id=scan_id,
                repo_url=repo_url,
                repo_name=repo_name,
                repo_owner=repo_owner,
                language=scan_result['language'],
                stars=0,
                security_score=scan_result['security_score'],
                files_scanned=1,
                overall_risk_level=scan_result['overall_risk_level']
            )
            
            # Save vulnerabilities
            if scan_result['vulnerabilities']:
                save_vulnerabilities(scan_id, scan_result['vulnerabilities'])
            
            print(f"Saved scan {scan_id} to Supabase")
            
        except Exception as db_error:
            print(f"Supabase error (non-fatal): {db_error}")
        
        return jsonify({
            "scan_id": scan_id,
            "security_score": scan_result['security_score'],
            "overall_risk_level": scan_result['overall_risk_level'],
            "language": scan_result['language'],
            "vulnerabilities": scan_result['vulnerabilities'],
            "vulnerability_count": scan_result['vulnerability_count'],
            "severity_breakdown": scan_result['severity_breakdown']
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/explain', methods=['POST'])
def explain():
    """Get plain English explanations for vulnerabilities"""
    try:
        data = request.get_json()
        vulnerabilities = data.get('vulnerabilities', [])
        code = data.get('code', '')
        
        explanations = explain_all_vulnerabilities(vulnerabilities, code)
        
        return jsonify({
            "explanations": explanations
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/fix', methods=['POST'])
def fix():
    """Generate fixed code and save to database"""
    try:
        data = request.get_json()
        scan_id = data.get('scan_id')
        code = data.get('code', '')
        vulnerabilities = data.get('vulnerabilities', [])
        language = data.get('language', 'auto')
        file_path = data.get('file_path', 'unknown')
        
        if not code:
            return jsonify({"error": "No code provided"}), 400
        
        result = fix_code(code, vulnerabilities, language)
        
        # Save to database if scan_id provided
        if scan_id:
            try:
                save_fix(
                    scan_id=scan_id,
                    file_path=file_path,
                    vulnerable_code=code,
                    fixed_code=result['fixed_code'],
                    fix_explanation="; ".join(result['changes']),
                    effort="auto"
                )
                print(f"Saved fix for scan {scan_id} to database")
            except Exception as db_error:
                print(f"Failed to save fix: {db_error}")
        
        return jsonify({
            "fixed_code": result['fixed_code'],
            "changes": result['changes']
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/simulate', methods=['POST'])
def simulate():
    """Run hacker simulation and save report to database"""
    try:
        data = request.get_json()
        scan_id = data.get('scan_id')
        original_code = data.get('code', '')
        fixed_code = data.get('fixed_code', '')
        vulnerabilities = data.get('vulnerabilities', [])
        language = data.get('language', 'auto')
        
        if not original_code:
            return jsonify({"error": "No code provided"}), 400
        
        simulation_text = simulate_attack(original_code, fixed_code, vulnerabilities, language)
        
        # Save to database if scan_id provided
        if scan_id and vulnerabilities:
            try:
                # Find most critical vulnerability
                severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
                most_critical = max(vulnerabilities, key=lambda v: severity_order.get(v.get('severity', 'low'), 0))
                
                # Estimate breach time based on severity
                severity = most_critical.get('severity', 'medium')
                breach_times = {
                    "critical": "under 5 minutes",
                    "high": "under 30 minutes", 
                    "medium": "within a few hours",
                    "low": "within a day"
                }
                
                save_hacker_report(
                    scan_id=scan_id,
                    attack_narrative=simulation_text[:1000],  # Truncate for DB
                    most_critical_vulnerability=most_critical.get('title', 'Unknown'),
                    estimated_breach_time=breach_times.get(severity, "unknown"),
                    attack_steps=["Reconnaissance", "Exploitation", "Data exfiltration"],
                    overall_risk_level=severity.upper()
                )
                print(f"Saved hacker report for scan {scan_id}")
            except Exception as db_error:
                print(f"Failed to save hacker report: {db_error}")
        
        return jsonify({
            "simulation_text": simulation_text
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get recent scan history"""
    try:
        from services.supabase_client import get_client
        client = get_client()
        result = client.table("scans").select("*").order("created_at", desc=True).limit(20).execute()
        
        return jsonify({
            "scans": result.data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scan/<scan_id>/full', methods=['GET'])
def get_full_scan(scan_id):
    """Get complete scan with vulnerabilities, fixes, and hacker report"""
    try:
        scan_result = get_scan(scan_id)
        if not scan_result.data:
            return jsonify({"error": "Scan not found"}), 404
        
        vulnerabilities = get_vulnerabilities(scan_id)
        fixes = get_fixes(scan_id)
        hacker_reports = get_hacker_reports(scan_id)
        
        return jsonify({
            "scan": scan_result.data[0],
            "vulnerabilities": vulnerabilities.data,
            "fixes": fixes.data,
            "hacker_report": hacker_reports.data[0] if hacker_reports.data else None
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/github/login', methods=['GET'])
def github_login():
    """Redirect to GitHub OAuth"""
    client_id = os.getenv("GITHUB_CLIENT_ID")
    redirect_uri = "http://localhost:5000/github/callback"
    return redirect(f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=repo")

@app.route('/github/callback', methods=['GET'])
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    token = exchange_code_for_token(code)
    
    if token:
        # Store token (in production use session)
        session_id = str(uuid.uuid4())
        github_tokens[session_id] = token
        return redirect(f"/?github_token={session_id}")
    else:
        return redirect("/?github_error=true")

@app.route('/create-pr', methods=['POST'])
def create_pr():
    """Create GitHub pull request with fixed code"""
    try:
        data = request.get_json()
        scan_id = data.get('scan_id')
        repo_url = data.get('repo_url')
        file_path = data.get('file_path')
        fixed_code = data.get('fixed_code')
        vulnerabilities = data.get('vulnerabilities', [])
        github_token = data.get('github_token') or github_tokens.get(data.get('session_id', ''))
        
        if not github_token:
            return jsonify({"error": "GitHub not connected. Please login first."}), 401
        
        if not repo_url or not file_path or not fixed_code:
            return jsonify({"error": "Missing required fields"}), 400
        
        result = create_pull_request(
            repo_url=repo_url,
            file_path=file_path,
            fixed_code=fixed_code,
            vulnerabilities=vulnerabilities,
            access_token=github_token,
            scan_id=scan_id
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "pr_url": result['pr_url'],
                "pr_number": result['pr_number'],
                "branch_name": result['branch_name']
            }), 200
        else:
            return jsonify({"error": result['error']}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scan/<scan_id>', methods=['GET'])
def get_scan_results(scan_id):
    """Retrieve previous scan results"""
    try:
        scan_result = get_scan(scan_id)
        vulnerabilities = get_vulnerabilities(scan_id)
        
        if not scan_result.data:
            return jsonify({"error": "Scan not found"}), 404
        
        return jsonify({
            "scan": scan_result.data[0],
            "vulnerabilities": vulnerabilities.data
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
