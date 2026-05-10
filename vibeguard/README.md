# 🛡️ VibeGuard - Security for Vibe Coders

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3.3-red.svg)](https://flask.palletsprojects.com/)

## 🎯 The Problem

Vibe coders are shipping vulnerable code every day. Non-technical founders building with AI assistants don't know what SQL injection is, yet they're pushing to production. Hackers are exploiting these MVPs within days.

## 💡 The Solution

VibeGuard is a one-click security scanner that:
- **Scans** code for vulnerabilities using Gemini AI
- **Explains** issues in plain English (no jargon)
- **Fixes** code automatically with one click
- **Simulates** hacker attacks to prove the fix works
- **Creates** GitHub PRs with all fixes

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Supabase account (free)
- Google Gemini API key (free tier)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/vibeguard.git
cd vibeguard

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your keys

# Run the app
python app.py
```

## 🌐 Environment Variables
```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
FLASK_SECRET_KEY=your_secret_key
```

## 🎮 Usage
1. **Paste code** - Python, JavaScript, PHP, or SQL
2. **Click Scan** - AI finds all vulnerabilities
3. **Read explanations** - Plain English impact statements
4. **Generate fix** - One click patched code with diff view
5. **Run simulation** - Watch hacker attack succeed then fail
6. **Create PR** - Push fixes to GitHub automatically

## 🏗️ Architecture
```text
┌─────────────────────────────────────────────────────────┐
│                    VibeGuard UI                         │
│         (Monaco Editor + Risk Dashboard)                │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   Flask Backend                         │
├───────────────┬───────────────┬───────────────────────┤
│  Scanner      │  Explainer    │  Fixer    │ Hacker Sim │
│  (Gemini AI)  │  (Gemini AI)  │ (Gemini AI)│ (Gemini AI)│
└───────────────┴───────────────┴───────────┴───────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    Supabase                             │
│     (Scans, Vulnerabilities, Fixes, Reports)           │
└─────────────────────────────────────────────────────────┘
```

## 📊 Risk Scoring
| Grade | Score | Action |
|-------|-------|--------|
| A | 100 | Safe to ship |
| B | 85-99 | Minor fixes |
| C | 70-84 | Fix before prod |
| D | 60-69 | Fix immediately |
| F | 0-59 | DO NOT SHIP |

## 🔍 Detected Vulnerabilities
- SQL Injection (Critical)
- Hardcoded Secrets (Critical)
- Cross-Site Scripting (High)
- Command Injection (High)
- Path Traversal (High)
- Broken Authentication (High)
- IDOR (Medium)
- Open Redirect (Medium)
- SSRF (Medium)
- Missing Rate Limiting (Low)
