"""
Dashboard Generator for AgentCore Evaluations

This module automatically generates an HTML dashboard with embedded evaluation data.
Import and call generate_dashboard() after your evaluation runs.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def generate_dashboard(evaluation_data, output_dir="."):
    """
    Generate an HTML dashboard with embedded evaluation data.
    
    Args:
        evaluation_data: List of evaluation session dictionaries or single session dict
        output_dir: Directory to save the dashboard (default: current directory)
    
    Returns:
        Path to the generated dashboard file
    """
    # Ensure evaluation_data is a list
    if not isinstance(evaluation_data, list):
        evaluation_data = [evaluation_data]
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dashboard_file = output_path / f"evaluation_dashboard_{timestamp}.html"
    
    # Convert evaluation data to JSON string
    data_json = json.dumps(evaluation_data, indent=2, default=str)
    
    # HTML template with embedded data
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgentCore Evaluation Dashboard - {timestamp}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
:root {{
--primary-color: #6366f1;
--success-color: #10b981;
--warning-color: #f59e0b;
--danger-color: #ef4444;
--bg-color: #fafafa;
--card-bg: #ffffff;
--border-color: #e5e5e5;
--text-primary: #171717;
--text-secondary: #737373;
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
--shadow-md: 0 4px 8px 0 rgba(0, 0, 0, 0.05);
}}
body {{
font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
background: var(--bg-color);
color: var(--text-primary);
line-height: 1.6;
}}
.header {{
background: white;
border-bottom: 1px solid var(--border-color);
padding: 1rem 0;
position: sticky;
top: 0;
z-index: 100;
box-shadow: var(--shadow-sm);
}}
.header-content {{
max-width: 1400px;
margin: 0 auto;
padding: 0 1.5rem;
}}
.header h1 {{
font-size: 1.5rem;
font-weight: 700;
margin-bottom: 0.25rem;
}}
.header p {{
font-size: 0.875rem;
color: var(--text-secondary);
}}
.container {{
max-width: 1400px;
margin: 0 auto;
padding: 2rem 1.5rem;
}}
.stats-grid {{
display: grid;
grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
gap: 1rem;
margin-bottom: 2rem;
}}
.stat-card {{
background: var(--card-bg);
padding: 1.5rem;
border-radius: 12px;
box-shadow: var(--shadow-sm);
border: 1px solid var(--border-color);
transition: transform 0.2s;
}}
.stat-card:hover {{
transform: translateY(-2px);
box-shadow: var(--shadow-md);
}}
.stat-label {{
font-size: 0.75rem;
color: var(--text-secondary);
text-transform: uppercase;
letter-spacing: 0.05em;
margin-bottom: 0.5rem;
font-weight: 600;
}}
.stat-value {{
font-size: 2rem;
font-weight: 700;
color: var(--text-primary);
}}
.stat-subtitle {{
font-size: 0.75rem;
color: var(--text-secondary);
margin-top: 0.5rem;
}}
.card {{
background: var(--card-bg);
border-radius: 12px;
padding: 1.5rem;
margin-bottom: 2rem;
box-shadow: var(--shadow-sm);
border: 1px solid var(--border-color);
}}
.card-title {{
font-size: 1.125rem;
font-weight: 700;
margin-bottom: 1rem;
}}
.chart-container {{
position: relative;
height: 300px;
margin: 1rem 0;
}}
table {{
width: 100%;
border-collapse: collapse;
}}
th {{
padding: 0.75rem 1rem;
text-align: left;
font-weight: 700;
background: #f5f5f5;
border-bottom: 1px solid var(--border-color);
font-size: 0.75rem;
text-transform: uppercase;
}}
td {{
padding: 0.75rem 1rem;
border-bottom: 1px solid #f5f5f5;
font-size: 0.875rem;
}}
tr:hover {{
background: #fafafa;
}}
.badge {{
display: inline-block;
padding: 0.25rem 0.75rem;
border-radius: 6px;
font-size: 0.75rem;
font-weight: 600;
}}
.score-high {{ background: #d1fae5; color: #047857; }}
.score-medium {{ background: #fef3c7; color: #b45309; }}
.score-low {{ background: #fee2e2; color: #dc2626; }}
.btn {{
padding: 0.5rem 1rem;
background: var(--primary-color);
color: white;
border: none;
border-radius: 8px;
cursor: pointer;
font-weight: 600;
font-size: 0.875rem;
}}
.btn:hover {{
opacity: 0.9;
}}
.btn-secondary {{
background: white;
color: var(--text-primary);
border: 1px solid var(--border-color);
}}
.btn-group {{
display: flex;
gap: 0.75rem;
margin-bottom: 1rem;
}}
.tabs {{
display: flex;
gap: 0.5rem;
margin-bottom: 1.5rem;
border-bottom: 1px solid var(--border-color);
}}
.tab {{
padding: 0.75rem 1.5rem;
background: transparent;
border: none;
cursor: pointer;
font-size: 0.9375rem;
color: var(--text-secondary);
border-bottom: 2px solid transparent;
font-weight: 500;
}}
.tab:hover {{
color: var(--text-primary);
}}
.tab.active {{
color: var(--primary-color);
border-bottom-color: var(--primary-color);
font-weight: 700;
}}
.tab-content {{
display: none;
}}
.tab-content.active {{
display: block;
}}
.detail-row {{
cursor: pointer;
}}
.detail-row:hover {{
background: #eff6ff !important;
}}
.modal {{
display: none;
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background: rgba(0, 0, 0, 0.5);
z-index: 1000;
}}
.modal.active {{
display: flex;
align-items: center;
justify-content: center;
padding: 2rem;
}}
.modal-content {{
background: white;
border-radius: 12px;
padding: 2rem;
max-width: 900px;
width: 100%;
max-height: 90vh;
overflow-y: auto;
}}
.modal-close {{
float: right;
font-size: 1.5rem;
cursor: pointer;
color: var(--text-secondary);
}}
.modal-close:hover {{
color: var(--danger-color);
}}
</style>
</head>
<body>
<div class="header">
<div class="header-content">
<h1>🎯 AgentCore Evaluation Dashboard</h1>
<p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</div>
</div>

<div class="container">
<div class="tabs">
<button class="tab active" onclick="switchTab('overview')">Overview</button>
<button class="tab" onclick="switchTab('sessions')">Sessions</button>
<button class="tab" onclick="switchTab('evaluators')">Evaluators</button>
</div>

<!-- Overview Tab -->
<div id="overview" class="tab-content active">
<div class="stats-grid">
<div class="stat-card">
<div class="stat-label">Total Sessions</div>
<div class="stat-value" id="totalSessions">0</div>
</div>
<div class="stat-card">
<div class="stat-label">Total Evaluations</div>
<div class="stat-value" id="totalEvaluations">0</div>
</div>
<div class="stat-card">
<div class="stat-label">Average Score</div>
<div class="stat-value" id="avgScore">0.00</div>
</div>
<div class="stat-card">
<div class="stat-label">Total Tokens</div>
<div class="stat-value" id="totalTokens">0</div>
<div class="stat-subtitle" id="tokenBreakdown"></div>
</div>
</div>

<div class="card">
<div class="card-title">Score Distribution</div>
<div class="chart-container">
<canvas id="scoreChart"></canvas>
</div>
</div>

<div class="card">
<div class="card-title">Evaluator Performance</div>
<div class="chart-container" style="height: 400px;">
<canvas id="evaluatorChart"></canvas>
</div>
</div>
</div>

<!-- Sessions Tab -->
<div id="sessions" class="tab-content">
<div class="card">
<div class="card-title">Session Details</div>
<div class="btn-group">
<button class="btn btn-secondary" onclick="exportToCSV()">Export CSV</button>
<button class="btn btn-secondary" onclick="exportToJSON()">Export JSON</button>
</div>
<div id="sessionsTable"></div>
</div>
</div>

<!-- Evaluators Tab -->
<div id="evaluators" class="tab-content">
<div class="card">
<div class="card-title">Evaluator Statistics</div>
<div id="evaluatorsTable"></div>
</div>
</div>
</div>

<!-- Modal -->
<div id="modal" class="modal">
<div class="modal-content">
<span class="modal-close" onclick="closeModal()">&times;</span>
<div id="modalBody"></div>
</div>
</div>

<script>
// Embedded evaluation data
const EVALUATION_DATA = {data_json};

let charts = {{}};

function initializeDashboard() {{
renderOverview();
renderSessions();
renderEvaluators();
}}

function renderOverview() {{
const allResults = [];
EVALUATION_DATA.forEach(session => {{
if (session.results) {{
allResults.push(...session.results);
}}
}});

// Update stats
document.getElementById('totalSessions').textContent = EVALUATION_DATA.length;
document.getElementById('totalEvaluations').textContent = allResults.length;

const validScores = allResults.filter(r => r.value != null);
const avgScore = validScores.length > 0
? (validScores.reduce((sum, r) => sum + r.value, 0) / validScores.length).toFixed(2)
: '0.00';
document.getElementById('avgScore').textContent = avgScore;

const inputTokens = allResults.reduce((sum, r) => sum + (r.token_usage?.inputTokens || 0), 0);
const outputTokens = allResults.reduce((sum, r) => sum + (r.token_usage?.outputTokens || 0), 0);
const totalTokens = allResults.reduce((sum, r) => sum + (r.token_usage?.totalTokens || 0), 0);

document.getElementById('totalTokens').textContent = totalTokens.toLocaleString();
document.getElementById('tokenBreakdown').textContent = 
`Input: ${{inputTokens.toLocaleString()}} | Output: ${{outputTokens.toLocaleString()}}`;

renderScoreChart(validScores);
renderEvaluatorChart(allResults);
}}

function renderScoreChart(scores) {{
const canvas = document.getElementById('scoreChart');
const ctx = canvas.getContext('2d');

const bins = Array(10).fill(0);
scores.forEach(r => {{
const binIndex = Math.min(Math.floor(r.value * 10), 9);
bins[binIndex]++;
}});

if (charts.score) charts.score.destroy();
charts.score = new Chart(ctx, {{
type: 'bar',
data: {{
labels: bins.map((_, i) => `${{(i * 0.1).toFixed(1)}}-${{((i + 1) * 0.1).toFixed(1)}}`),
datasets: [{{
label: 'Evaluations',
data: bins,
backgroundColor: bins.map((_, i) => {{
const score = (i + 0.5) / 10;
return score >= 0.8 ? '#10b981' : score >= 0.5 ? '#f59e0b' : '#ef4444';
}}),
borderRadius: 6
}}]
}},
options: {{
responsive: true,
maintainAspectRatio: false,
plugins: {{ legend: {{ display: false }} }}
}}
}});
}}

function renderEvaluatorChart(results) {{
const canvas = document.getElementById('evaluatorChart');
const ctx = canvas.getContext('2d');

const evaluatorMap = {{}};
results.forEach(r => {{
if (r.value != null) {{
if (!evaluatorMap[r.evaluator_id]) {{
evaluatorMap[r.evaluator_id] = {{ sum: 0, count: 0 }};
}}
evaluatorMap[r.evaluator_id].sum += r.value;
evaluatorMap[r.evaluator_id].count++;
}}
}});

const evaluators = Object.entries(evaluatorMap)
.map(([id, data]) => ({{
id: id.replace('Builtin.', ''),
avg: data.sum / data.count,
count: data.count
}}))
.sort((a, b) => b.avg - a.avg);

if (charts.evaluator) charts.evaluator.destroy();
charts.evaluator = new Chart(ctx, {{
type: 'bar',
data: {{
labels: evaluators.map(e => e.id),
datasets: [{{
label: 'Average Score',
data: evaluators.map(e => e.avg),
backgroundColor: evaluators.map(e =>
e.avg >= 0.8 ? '#10b981' : e.avg >= 0.5 ? '#f59e0b' : '#ef4444'
),
borderRadius: 6
}}]
}},
options: {{
indexAxis: 'y',
responsive: true,
maintainAspectRatio: false,
plugins: {{ 
legend: {{ display: false }},
tooltip: {{
callbacks: {{
label: (context) => {{
const evaluator = evaluators[context.dataIndex];
return [
`Average: ${{context.parsed.x.toFixed(3)}}`,
`Count: ${{evaluator.count}}`
];
}}
}}
}}
}},
scales: {{ x: {{ beginAtZero: true, max: 1 }} }}
}}
}});
}}

function renderSessions() {{
const container = document.getElementById('sessionsTable');
let html = '<table><thead><tr>';
html += '<th>Session ID</th><th>Evaluations</th><th>Avg Score</th><th>Tokens</th><th>Actions</th>';
html += '</tr></thead><tbody>';

EVALUATION_DATA.forEach((session, idx) => {{
const results = session.results || [];
const validScores = results.filter(r => r.value != null);
const avgScore = validScores.length > 0
? validScores.reduce((sum, r) => sum + r.value, 0) / validScores.length
: 0;

const totalTokens = results.reduce((sum, r) => sum + (r.token_usage?.totalTokens || 0), 0);

const scoreClass = avgScore >= 0.8 ? 'badge score-high' 
: avgScore >= 0.5 ? 'badge score-medium' 
: 'badge score-low';

html += '<tr class="detail-row">';
html += `<td><code>${{session.session_id.substring(0, 16)}}...</code></td>`;
html += `<td>${{results.length}}</td>`;
html += `<td><span class="${{scoreClass}}">${{avgScore.toFixed(2)}}</span></td>`;
html += `<td>${{totalTokens.toLocaleString()}}</td>`;
html += `<td><button class="btn btn-secondary" onclick="showSessionDetails(${{idx}})">View</button></td>`;
html += '</tr>';
}});

html += '</tbody></table>';
container.innerHTML = html;
}}

function renderEvaluators() {{
const container = document.getElementById('evaluatorsTable');
const evaluatorMap = {{}};

EVALUATION_DATA.forEach(session => {{
(session.results || []).forEach(r => {{
if (!evaluatorMap[r.evaluator_id]) {{
evaluatorMap[r.evaluator_id] = {{
scores: [],
tokens: 0,
count: 0
}};
}}
if (r.value != null) {{
evaluatorMap[r.evaluator_id].scores.push(r.value);
}}
evaluatorMap[r.evaluator_id].tokens += r.token_usage?.totalTokens || 0;
evaluatorMap[r.evaluator_id].count++;
}});
}});

let html = '<table><thead><tr>';
html += '<th>Evaluator</th><th>Count</th><th>Avg Score</th><th>Min</th><th>Max</th><th>Total Tokens</th>';
html += '</tr></thead><tbody>';

Object.entries(evaluatorMap)
.sort(([a], [b]) => a.localeCompare(b))
.forEach(([id, data]) => {{
const avg = data.scores.length > 0 
? data.scores.reduce((a, b) => a + b, 0) / data.scores.length 
: 0;
const min = data.scores.length > 0 ? Math.min(...data.scores) : 0;
const max = data.scores.length > 0 ? Math.max(...data.scores) : 0;

const scoreClass = avg >= 0.8 ? 'badge score-high' 
: avg >= 0.5 ? 'badge score-medium' 
: 'badge score-low';

html += '<tr>';
html += `<td><strong>${{id.replace('Builtin.', '')}}</strong></td>`;
html += `<td>${{data.count}}</td>`;
html += `<td><span class="${{scoreClass}}">${{avg.toFixed(3)}}</span></td>`;
html += `<td>${{min.toFixed(2)}}</td>`;
html += `<td>${{max.toFixed(2)}}</td>`;
html += `<td>${{data.tokens.toLocaleString()}}</td>`;
html += '</tr>';
}});

html += '</tbody></table>';
container.innerHTML = html;
}}

function showSessionDetails(idx) {{
const session = EVALUATION_DATA[idx];
let html = '<h2>Session Details</h2>';
html += `<p><strong>Session ID:</strong> <code>${{session.session_id}}</code></p>`;
html += `<p><strong>Evaluations:</strong> ${{session.results?.length || 0}}</p>`;

if (session.metadata) {{
html += '<h3>Metadata</h3><ul>';
Object.entries(session.metadata).forEach(([k, v]) => {{
html += `<li><strong>${{k}}:</strong> ${{v}}</li>`;
}});
html += '</ul>';
}}

html += '<h3>Evaluation Results</h3><table><thead><tr>';
html += '<th>Evaluator</th><th>Score</th><th>Label</th><th>Tokens</th>';
html += '</tr></thead><tbody>';

(session.results || []).forEach(r => {{
const scoreClass = r.value >= 0.8 ? 'badge score-high' 
: r.value >= 0.5 ? 'badge score-medium' 
: 'badge score-low';

html += '<tr>';
html += `<td>${{r.evaluator_id.replace('Builtin.', '')}}</td>`;
html += `<td><span class="${{scoreClass}}">${{r.value?.toFixed(2) || 'N/A'}}</span></td>`;
html += `<td>${{r.label || 'N/A'}}</td>`;
html += `<td>${{r.token_usage?.totalTokens || 0}}</td>`;
html += '</tr>';
}});

html += '</tbody></table>';
showModal(html);
}}

function switchTab(tabName) {{
document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
event.target.classList.add('active');
document.getElementById(tabName).classList.add('active');
}}

function showModal(html) {{
document.getElementById('modalBody').innerHTML = html;
document.getElementById('modal').classList.add('active');
}}

function closeModal() {{
document.getElementById('modal').classList.remove('active');
}}

function exportToCSV() {{
let csv = 'Session ID,Evaluator,Score,Label,Tokens\\n';
EVALUATION_DATA.forEach(session => {{
(session.results || []).forEach(r => {{
csv += `"${{session.session_id}}","${{r.evaluator_id}}",${{r.value || ''}},"${{r.label || ''}}",${{r.token_usage?.totalTokens || 0}}\\n`;
}});
}});
downloadFile(csv, 'evaluation_results.csv', 'text/csv');
}}

function exportToJSON() {{
const json = JSON.stringify(EVALUATION_DATA, null, 2);
downloadFile(json, 'evaluation_results.json', 'application/json');
}}

function downloadFile(content, filename, type) {{
const blob = new Blob([content], {{ type }});
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = filename;
a.click();
URL.revokeObjectURL(url);
}}

// Initialize on load
initializeDashboard();
</script>
</body>
</html>"""
    
    # Write the HTML file
    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✓ Dashboard generated: {dashboard_file}")
    print(f"  Open in browser: file://{dashboard_file.absolute()}")
    
    return str(dashboard_file)


if __name__ == "__main__":
    # Example usage
    sample_data = [{
        "session_id": "test-session-123",
        "metadata": {"experiment": "test"},
        "results": [
            {
                "evaluator_id": "Builtin.Helpfulness",
                "value": 0.85,
                "label": "Very Helpful",
                "token_usage": {"totalTokens": 150}
            }
        ]
    }]
    
    generate_dashboard(sample_data)
