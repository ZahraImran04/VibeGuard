let currentScanId;
let currentOriginalCode = '';
let currentFixedCode = '';
let currentVulnerabilities = [];

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Matrix background
    initMatrix();

    // Event Listeners
    const scanBtn = document.getElementById('scan-btn');
    if (scanBtn) scanBtn.addEventListener('click', fetchScan);

    const exampleBtn = document.getElementById('example-btn');
    if (exampleBtn) {
        exampleBtn.addEventListener('click', () => {
            const codeArea = document.getElementById('code-area');
            if (codeArea) {
                codeArea.value = `import sqlite3\n\ndef get_user(user_id):\n    conn = sqlite3.connect("db.sqlite")\n    cursor = conn.cursor()\n    query = f"SELECT * FROM users WHERE id = {user_id}"\n    cursor.execute(query)\n    return cursor.fetchone()\n\nAPI_KEY = "sk-abc123xyz789"\nSECRET_TOKEN = "ghp_abc123def456"\n\n# XSS vulnerability\n# user_input = request.args.get("name")\n# innerHTML = user_input`;
            }
        });
    }

    const generateFixBtn = document.getElementById('generate-fix-btn');
    if (generateFixBtn) generateFixBtn.addEventListener('click', generateFix);

    const simulateBtn = document.getElementById('simulate-btn');
    if (simulateBtn) simulateBtn.addEventListener('click', runSimulation);

    const createPRBtn = document.getElementById('createPRBtn');
    if (createPRBtn) createPRBtn.addEventListener('click', createPR);

    // Check for GitHub token in URL
    const urlParams = new URLSearchParams(window.location.search);
    const githubToken = urlParams.get('github_token');
    if (githubToken) {
        const githubRepoInput = document.getElementById('github-repo-input');
        const githubLoginBtn = document.getElementById('github-login-btn');
        if (githubRepoInput) githubRepoInput.style.display = 'block';
        if (githubLoginBtn) githubLoginBtn.style.display = 'none';
        window.githubSessionId = githubToken;
    }

    // Add history link to navbar
    const navRight = document.querySelector('.nav-right');
    if (navRight) {
        const historyLink = document.createElement('a');
        historyLink.href = '#';
        historyLink.innerText = 'History';
        historyLink.style.marginRight = '20px';
        historyLink.onclick = (e) => {
            e.preventDefault();
            showHistory();
        };
        navRight.prepend(historyLink);
    }
});

async function fetchScan() {
    const repoUrl = document.getElementById('repo-url').value;
    const codeArea = document.getElementById('code-area');
    const code = codeArea ? codeArea.value : '';
    
    if (!repoUrl && !code) {
        alert('Please enter a GitHub repository URL or paste code');
        return;
    }

    currentOriginalCode = code;

    // Show dashboard, hide hero
    const hero = document.getElementById('hero');
    const dashboard = document.getElementById('dashboard');
    if (hero) hero.classList.add('hidden');
    if (dashboard) dashboard.classList.remove('hidden');

    setAllAgentsStatus("running");

    try {
        const response = await fetch('/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_url: repoUrl, code: code })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            alert(data.error || "Scan failed.");
            setAllAgentsStatus("idle");
            return;
        }

        currentScanId = data.scan_id;
        renderResults(data);

        // Fetch explanations
        const explainerStatus = document.getElementById('explainer-status');
        if (explainerStatus) {
            explainerStatus.innerText = 'running';
            explainerStatus.parentElement.className = 'badge badge-running';
        }

        const explainResponse = await fetch('/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vulnerabilities: data.vulnerabilities, code: code })
        });
        
        const explainData = await explainResponse.json();
        if (explainResponse.ok) {
            renderExplanations(explainData.explanations);
            if (explainerStatus) {
                explainerStatus.innerText = 'done';
                explainerStatus.parentElement.className = 'badge badge-done';
            }
        }
    } catch (error) {
        console.error('Error initiating scan:', error);
        alert("Network error initiating scan.");
        setAllAgentsStatus("idle");
    }
}

async function generateFix() {
    if (!currentScanId) return alert('Please scan code first');
    
    const generateFixBtn = document.getElementById('generate-fix-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    generateFixBtn.disabled = true;
    generateFixBtn.textContent = '⏳ Generating fix...';
    if (loadingOverlay) loadingOverlay.style.display = 'flex';

    const fixerStatus = document.getElementById('fixer-status');
    if (fixerStatus) {
        fixerStatus.innerText = 'running';
        fixerStatus.parentElement.className = 'badge badge-running';
    }
    
    try {
        const response = await fetch('/fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                scan_id: currentScanId,
                code: currentOriginalCode,
                vulnerabilities: currentVulnerabilities
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentFixedCode = data.fixed_code;
            displayFixedCode(data);
            if (fixerStatus) {
                fixerStatus.innerText = 'done';
                fixerStatus.parentElement.className = 'badge badge-done';
            }
        } else {
            alert('Error: ' + data.error);
            if (fixerStatus) {
                fixerStatus.innerText = 'idle';
                fixerStatus.parentElement.className = 'badge badge-idle';
            }
        }
    } catch (error) {
        console.error('Fix error:', error);
        alert('Failed to generate fixed code');
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
        generateFixBtn.disabled = false;
        generateFixBtn.textContent = '✨ Generate Fixed Code';
    }
}

async function runSimulation() {
    if (!currentScanId || !currentFixedCode) return alert('Please scan and generate fix first');
    
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    
    const simulationResult = document.getElementById('simulation-result');
    if (simulationResult) simulationResult.innerHTML = '';
    
    try {
        const response = await fetch('/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                scan_id: currentScanId,
                code: currentOriginalCode,
                fixed_code: currentFixedCode,
                vulnerabilities: currentVulnerabilities
            })
        });
        
        const data = await response.json();
        if (response.ok) {
            await runSimulationWithTyping(data.simulation_text);
        } else {
            if (simulationResult) simulationResult.innerHTML = `Error: ${data.error}`;
        }
    } catch (error) {
        console.error('Simulation error:', error);
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }
}

async function createPR() {
    const repoUrl = document.getElementById('repo-url').value;
    const filePath = document.getElementById('file-path').value;
    const githubToken = window.githubSessionId;
    
    if (!repoUrl || !filePath) return alert('Please enter repo URL and file path');
    if (!currentFixedCode) return alert('Please generate fixed code first');
    if (!githubToken) return alert('Please connect GitHub first');

    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    
    try {
        const response = await fetch('/create-pr', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scan_id: currentScanId,
                repo_url: repoUrl,
                file_path: filePath,
                fixed_code: currentFixedCode,
                vulnerabilities: currentVulnerabilities,
                github_token: githubToken
            })
        });
        
        const data = await response.json();
        if (response.ok && data.success) {
            alert(`✅ Pull Request created!\n${data.pr_url}`);
            window.open(data.pr_url, '_blank');
        } else {
            alert('Error: ' + (data.error || 'Failed to create PR.'));
        }
    } catch (error) {
        console.error('PR error:', error);
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }
}

function renderResults(data) {
    if (data.security_score !== undefined) {
        updateSecurityScore(data.security_score);
        const riskLevel = document.getElementById('risk-level');
        if (riskLevel) {
            riskLevel.innerText = data.overall_risk_level || '-';
            riskLevel.style.color = data.security_score > 70 ? 'var(--accent-green)' : (data.security_score > 40 ? 'var(--color-medium)' : 'var(--color-critical)');
        }
    }
    
    if (data.vulnerabilities) {
        currentVulnerabilities = data.vulnerabilities;
        renderVulnerabilities(data.vulnerabilities);
    }
    
    setAllAgentsStatus('done', ['scanner-status']);
}

function renderVulnerabilities(vulns) {
    const list = document.getElementById('vuln-list');
    if (!list) return;
    list.innerHTML = '';
    
    vulns.forEach(v => {
        const li = document.createElement('li');
        li.className = 'vuln-item';
        li.innerHTML = `
            <div class="vuln-header">
                <span class="vuln-badge severity-${(v.severity || 'low').toLowerCase()}">${(v.severity || 'low').toUpperCase()}</span>
                <strong>${v.title}</strong>
            </div>
            <div class="vuln-desc">${v.description}</div>
        `;
        list.appendChild(li);
    });
}

function renderExplanations(explanations) {
    const list = document.getElementById('vuln-list');
    if (!list || !explanations) return;
    list.innerHTML = '';
    explanations.forEach(exp => {
        const li = document.createElement('li');
        li.className = 'vuln-item';
        li.innerHTML = `
            <div class="vuln-header">
                <strong>${exp.title}</strong>
            </div>
            <div class="vuln-desc">
                <p style="margin-bottom: 8px;">${exp.plain_explanation || exp.explanation}</p>
                <p style="color: var(--color-critical); font-size: 0.85rem;">⚠️ <strong>Impact:</strong> ${exp.real_world_impact || exp.impact}</p>
            </div>
        `;
        list.appendChild(li);
    });
}

function displayFixedCode(data) {
    const fixResult = document.getElementById('fix-result');
    if (!fixResult) return;

    const originalLines = currentOriginalCode.split('\n');
    const fixedLines = data.fixed_code.split('\n');
    
    let diffHtml = '<div class="diff-container" style="font-family: monospace; font-size: 13px; background: #000; padding: 15px; border-radius: 8px;">';
    diffHtml += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">';
    diffHtml += '<div><strong style="color: #ff6666;">❌ ORIGINAL</strong></div>';
    diffHtml += '<div><strong style="color: #66ff66;">✅ FIXED</strong></div>';
    
    const maxLines = Math.max(originalLines.length, fixedLines.length);
    for (let i = 0; i < maxLines; i++) {
        const originalLine = originalLines[i] || '';
        const fixedLine = fixedLines[i] || '';
        const isChanged = originalLine !== fixedLine;
        
        diffHtml += `<div style="${isChanged ? 'background: rgba(255, 0, 0, 0.1);' : ''} padding: 2px;">${escapeHtml(originalLine) || '&nbsp;'}</div>`;
        diffHtml += `<div style="${isChanged ? 'background: rgba(0, 255, 0, 0.1);' : ''} padding: 2px;">${escapeHtml(fixedLine) || '&nbsp;'}</div>`;
    }
    diffHtml += '</div></div>';
    
    fixResult.innerHTML = `<h3>Patched Code</h3>${diffHtml}`;
    setTimeout(addCopyButton, 100);
}

function addCopyButton() {
    const containers = document.querySelectorAll('.diff-container');
    containers.forEach(container => {
        if (container.querySelector('.copy-btn')) return;
        const btn = document.createElement('button');
        btn.innerText = '📋 Copy Fixed Code';
        btn.className = 'copy-btn';
        btn.onclick = () => {
            navigator.clipboard.writeText(currentFixedCode);
            btn.innerText = '✅ Copied!';
            setTimeout(() => btn.innerText = '📋 Copy Fixed Code', 2000);
        };
        container.style.position = 'relative';
        container.appendChild(btn);
    });
}

async function runSimulationWithTyping(text) {
    const el = document.getElementById('simulation-result');
    if (!el) return;
    el.innerHTML = '';
    const lines = text.split('\n');
    for (let line of lines) {
        const lineEl = document.createElement('div');
        el.appendChild(lineEl);
        for (let char of line) {
            lineEl.textContent += char;
            await new Promise(r => setTimeout(r, 10));
        }
        lineEl.textContent += '\n';
        el.scrollTop = el.scrollHeight;
    }
}

function setAllAgentsStatus(status, specificIds = null) {
    const ids = specificIds || ['scanner-status', 'explainer-status', 'fixer-status'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerText = status;
            el.parentElement.className = `badge badge-${status}`;
        }
    });
}

function updateSecurityScore(score) {
    const circle = document.getElementById('score-circle');
    const text = document.getElementById('score-text');
    if (!text || !circle) return;
    text.innerText = score;
    circle.setAttribute('stroke-dasharray', `${score}, 100`);
    circle.style.stroke = score > 70 ? '#00ff88' : (score > 40 ? '#ffcc00' : '#ff3300');
}

async function showHistory() {
    try {
        const res = await fetch('/history');
        const data = await res.json();
        if (!data.scans || data.scans.length === 0) return alert('No history found');
        
        let html = '<table class="history-table"><tr><th>Date</th><th>Score</th><th>Risk</th></tr>';
        data.scans.forEach(s => {
            html += `<tr style="cursor:pointer"><td>${new Date(s.created_at).toLocaleDateString()}</td><td>${s.security_score}</td><td>${s.overall_risk_level}</td></tr>`;
        });
        html += '</table>';
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `<div class="modal-content"><span class="modal-close">&times;</span>${html}</div>`;
        document.body.appendChild(modal);
        modal.style.display = 'block';
        modal.querySelector('.modal-close').onclick = () => modal.remove();
    } catch (e) { console.error(e); }
}

function initMatrix() {
    const canvas = document.getElementById('matrix-bg');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const letters = '01';
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    const drops = Array(Math.floor(columns)).fill(1);
    setInterval(() => {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#0f0';
        ctx.font = fontSize + 'px monospace';
        drops.forEach((y, i) => {
            const text = letters[Math.floor(Math.random() * letters.length)];
            ctx.fillText(text, i * fontSize, y * fontSize);
            if (y * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
            drops[i]++;
        });
    }, 33);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
