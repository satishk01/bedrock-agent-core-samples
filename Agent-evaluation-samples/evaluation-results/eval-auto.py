


"""
Automated Evaluation Analysis Script for EC2

This script:
1. Loads evaluation results from JSON files
2. Analyzes low-scoring evaluations
3. Identifies patterns and problems
4. Generates actionable recommendations
5. Creates an updated system prompt

Usage:
    python3 eval-auto.py

Requirements:
    - Evaluation JSON files in eval_data/ folder
    - system-prompt.txt with your agent's prompt
    - strands package installed
"""

# Configuration
EVAL_FOLDER = "eval_data/"
BATCH_SIZE = 10
SCORE_THRESHOLD = 0.7
SYSTEM_PROMPT_FILE = "system-prompt.txt"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
AWS_REGION = "us-east-1"

# Load system prompt
from pathlib import Path
import sys

prompt_path = Path(SYSTEM_PROMPT_FILE)
if not prompt_path.exists():
    print(f"ERROR: {SYSTEM_PROMPT_FILE} not found!")
    print(f"Please create {SYSTEM_PROMPT_FILE} with your agent's system prompt.")
    sys.exit(1)

if prompt_path.stat().st_size < 100:
    print(f"WARNING: {SYSTEM_PROMPT_FILE} seems too short (< 100 chars)")
    print(f"Please add your actual agent system prompt to this file.")
    sys.exit(1)

with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
    AGENT_SYSTEM_PROMPT = f.read()

# Strip comment header if present
lines = AGENT_SYSTEM_PROMPT.split('\n')
content_lines = []
in_header = True
for line in lines:
    if in_header and line.strip().startswith('#'):
        continue
    in_header = False
    content_lines.append(line)
AGENT_SYSTEM_PROMPT = '\n'.join(content_lines).strip()

print(f"✓ System prompt loaded ({len(AGENT_SYSTEM_PROMPT)} chars)")

##setup

import json
import time
from typing import List, Dict, Any, Optional
from statistics import mean, stdev
from collections import defaultdict

# Check if running in Jupyter
try:
    from IPython.display import display, Markdown
    USE_IPYTHON = True
except ImportError:
    USE_IPYTHON = False
    print("Note: Running in terminal mode (not Jupyter)")

from strands import Agent, tool
from strands.models import BedrockModel

def extract_evaluations(data: Any, parent_metadata: Optional[Dict] = None) -> List[Dict]:
    """Recursively extract evaluations from any JSON structure."""
    evaluations = []
    parent_metadata = parent_metadata or {}
    
    if isinstance(data, list):
        for item in data:
            evaluations.extend(extract_evaluations(item, parent_metadata))
    elif isinstance(data, dict):
        score_key = 'score' if 'score' in data else ('value' if 'value' in data else None)
        
        if score_key and 'explanation' in data:
            eval_entry = {
                'score': data[score_key],
                'explanation': data['explanation'],
                'metadata': {**parent_metadata}
            }
            for key, val in data.items():
                if key not in ['score', 'value', 'explanation']:
                    if isinstance(val, (str, int, float, bool)):
                        eval_entry['metadata'][key] = val
            evaluations.append(eval_entry)
        else:
            nested_metadata = {**parent_metadata}
            for key in ['session_id', 'trace_id', 'evaluator_name', 'evaluator_id']:
                if key in data:
                    nested_metadata[key] = data[key]
            for key in ['results', 'evaluations', 'data', 'items']:
                if key in data:
                    evaluations.extend(extract_evaluations(data[key], nested_metadata))
    
    return evaluations

def load_evaluations(folder_path: str) -> List[Dict]:
    """Load all JSON files from a folder and extract evaluations."""
    evaluations = []
    folder = Path(folder_path)
    
    for json_file in sorted(folder.glob("*.json")):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            evals = extract_evaluations(data, {'source_file': json_file.name})
            evaluations.extend(evals)
            print(f"  {json_file.name}: {len(evals)} evaluations")
        except Exception as e:
            print(f"  {json_file.name}: Error - {e}")
    
    return evaluations

def compute_statistics(evaluations: List[Dict], threshold: float) -> Dict:
    """Compute statistics from evaluations."""
    if not evaluations:
        return {'total': 0, 'error': 'No evaluations found'}
    
    scores = [e['score'] for e in evaluations if e['score'] is not None]
    
    by_evaluator = defaultdict(list)
    for e in evaluations:
        evaluator = e['metadata'].get('evaluator_name', e['metadata'].get('label', 'unknown'))
        if e['score'] is not None:
            by_evaluator[evaluator].append(e['score'])
    
    evaluator_stats = {}
    for evaluator, eval_scores in by_evaluator.items():
        evaluator_stats[evaluator] = {
            'count': len(eval_scores),
            'mean': round(mean(eval_scores), 3),
            'min': round(min(eval_scores), 3),
            'max': round(max(eval_scores), 3),
        }
        if len(eval_scores) > 1:
            evaluator_stats[evaluator]['stdev'] = round(stdev(eval_scores), 3)
    
    low_scoring = [e for e in evaluations if e['score'] is not None and e['score'] < threshold]
    
    return {
        'total': len(evaluations),
        'valid_scores': len(scores),
        'mean_score': round(mean(scores), 3) if scores else None,
        'min_score': round(min(scores), 3) if scores else None,
        'max_score': round(max(scores), 3) if scores else None,
        'stdev': round(stdev(scores), 3) if len(scores) > 1 else None,
        'low_scoring_count': len(low_scoring),
        'low_scoring_pct': round(len(low_scoring) / len(scores) * 100, 1) if scores else 0,
        'by_evaluator': evaluator_stats,
        'threshold': threshold
    }

def batch_evaluations(evaluations: List[Dict], batch_size: int) -> List[List[Dict]]:
    """Split evaluations into batches."""
    return [evaluations[i:i+batch_size] for i in range(0, len(evaluations), batch_size)]
    
    
# Validate configuration
if not AGENT_SYSTEM_PROMPT.strip():
    print(f"ERROR: System prompt is empty!")
    print(f"Please add your agent's system prompt to {SYSTEM_PROMPT_FILE}")
    sys.exit(1)

print(f"✓ System prompt validated")

eval_path = Path(EVAL_FOLDER)
if not eval_path.exists():
    print(f"ERROR: Evaluation folder not found: {EVAL_FOLDER}")
    print(f"Please create the folder and add evaluation JSON files.")
    sys.exit(1)

json_files = list(eval_path.glob("*.json"))
if not json_files:
    print(f"ERROR: No JSON files found in {EVAL_FOLDER}")
    print(f"Please run evaluations first to generate JSON files.")
    sys.exit(1)

print(f"✓ Found {len(json_files)} JSON files in {EVAL_FOLDER}")

print(f"\nLoading evaluations from {EVAL_FOLDER}:")
evaluations = load_evaluations(EVAL_FOLDER)
print(f"\n✓ Total: {len(evaluations)} evaluations loaded")

if len(evaluations) == 0:
    print(f"ERROR: No evaluations found in JSON files!")
    print(f"Please check that your JSON files contain evaluation results.")
    sys.exit(1)

stats = compute_statistics(evaluations, SCORE_THRESHOLD)

print(f"\n{'='*80}")
print(f"EVALUATION STATISTICS")
print(f"{'='*80}")
print(f"Mean score: {stats['mean_score']} (range: {stats['min_score']} - {stats['max_score']})")
print(f"Low scoring (<{SCORE_THRESHOLD}): {stats['low_scoring_count']} ({stats['low_scoring_pct']}%)")

print(f"\nBy evaluator:")
for evaluator, eval_stats in stats['by_evaluator'].items():
    print(f"  • {evaluator}: mean={eval_stats['mean']}, count={eval_stats['count']}")

low_scoring = [e for e in evaluations if e['score'] is not None and e['score'] < SCORE_THRESHOLD]

if len(low_scoring) == 0:
    print(f"\n{'='*80}")
    print(f"✓ EXCELLENT! No low-scoring evaluations found.")
    print(f"{'='*80}")
    print(f"\nYour agent is performing well across all metrics.")
    print(f"No analysis needed at this time.")
    sys.exit(0)

print(f"\n{'='*80}")
print(f"ANALYSIS STARTING")
print(f"{'='*80}")
print(f"{len(low_scoring)} low-scoring evaluations will be analyzed")
print(f"This may take a few minutes...")
print(f"{'='*80}\n")


###Define Analysis Agents

# ============================================
# AGENT PROMPTS
# ============================================

BATCH_ANALYZER_PROMPT = """
You analyze low-scoring evaluations to identify systematic failure patterns.

## Input
A batch of evaluations, each with:
- score: numeric 0-1 (scores < 0.7 indicate problems)
- explanation: detailed text from the LLM judge explaining why the score was given
- metadata: context including evaluator_name, trace_id/session_id

## Your Task
1. Read each explanation carefully - these contain the LLM judge's reasoning
2. Identify SYSTEMATIC PATTERNS (not isolated incidents) in why scores are low
3. Group similar failures together
4. Extract 2-3 specific quotes as evidence per pattern
5. Note which evaluator metrics are affected

## Output (JSON)
Return ONLY valid JSON with this structure:
{
  "patterns": [
    {
      "name": "short descriptive name",
      "description": "what the agent did wrong and why it's problematic",
      "count": N,
      "evaluators_affected": ["Faithfulness", "Correctness"],
      "evidence": ["direct quote from explanation 1", "direct quote from explanation 2"],
      "root_cause": "what's missing or unclear in the system prompt"
    }
  ]
}

CONSTRAINTS:
- Maximum 5 patterns per batch
- Only include patterns that appear 2+ times (systematic, not isolated)
- Evidence quotes should be verbatim from explanations
- Root cause should identify what prompt guidance would fix this
"""

ORCHESTRATOR_PROMPT = """
You synthesize evaluation analysis into actionable recommendations with system prompt improvements.

## Your Task
1. Use the analyze_batch tool to analyze low-scoring evaluations in batches
2. Collect patterns from all batches
3. Identify the TOP 3 most impactful problems based on:
   - **Frequency**: Appears across multiple evaluations (the more, the worse)
   - **Severity**: Lower scores indicate more severe problems
   - **Fixability**: Can be addressed by clarifying the system prompt
4. Generate specific, minimal prompt changes to fix each problem

## Required Output Format

# Evaluation Analysis Report

## Summary
[2-3 sentences on overall health of the agent based on the statistics and patterns found]

## Top 3 Problems

### Problem 1: [Specific Descriptive Name]

**Evidence from evaluations:**
- "[Direct quote from LLM judge explanation]"
- "[Another direct quote showing this pattern]"

**Frequency & Impact:**
- Appears in X out of Y low-scoring evaluations
- Affects metrics: [list evaluator names]
- Average score when this occurs: X.XX

**Root Cause:**
[What's missing or unclear in the current system prompt that causes this behavior]

**Proposed Fix:**
[Specific text to add/modify in the prompt and why it will work]

---

### Problem 2: [Specific Descriptive Name]

**Evidence from evaluations:**
- "[Direct quote]"
- "[Another quote]"
- "[TraceID and SessionID]"

**Frequency & Impact:**
- Appears in X out of Y low-scoring evaluations
- Affects metrics: [list]
- Average score when this occurs: X.XX

**Root Cause:**
[What's missing in the prompt]

**Proposed Fix:**
[Specific change and rationale]

---

### Problem 3: [Specific Descriptive Name]

**Evidence from evaluations:**
- "[Direct quote]"
- "[Another quote]"

**Frequency & Impact:**
- Appears in X out of Y low-scoring evaluations
- Affects metrics: [list]
- Average score when this occurs: X.XX

**Root Cause:**
[What's missing in the prompt]

**Proposed Fix:**
[Specific change and rationale]

---

## Suggested System Prompt Changes

### Changes Summary
| # | What Changed | Original Text | New Text | Fixes |
|---|--------------|---------------|----------|-------|
| 1 | [brief description] | [exact original snippet] | [exact new snippet] | Problem 1 |
| 2 | [brief description] | [exact original snippet] | [exact new snippet] | Problem 2 |
| 3 | [brief description] | [exact original snippet] | [exact new snippet] | Problem 3 |

### Complete Updated System Prompt
```
[FULL UPDATED PROMPT - COPY-PASTE READY]
```

## CONSTRAINTS
- Only 3 problems, ranked by impact (frequency � severity)
- Evidence must be actual quotes from the evaluation explanations with traceID and sessionID
- Make minimal, surgical prompt changes (not a complete rewrite)
- Preserve everything in the original prompt that works well
- The Complete Updated System Prompt must be the FULL prompt, ready to use
- No implementation roadmaps, KPIs, timelines, or risk assessments
"""

model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION)

batch_analyzer_agent = Agent(model=model, system_prompt=BATCH_ANALYZER_PROMPT)

@tool
def analyze_batch(batch_json: str) -> str:
    """Analyze a batch of low-scoring evaluations to identify failure patterns."""
    result = batch_analyzer_agent(f"Analyze these evaluations and return JSON patterns:\n{batch_json}")
    return str(result)

orchestrator = Agent(model=model, system_prompt=ORCHESTRATOR_PROMPT, tools=[analyze_batch])

print(f"Analyzing {len(low_scoring)} evaluations in {len(batch_evaluations(low_scoring, BATCH_SIZE))} batches...")

# Start timing
start_time = time.time()

batches = batch_evaluations(low_scoring, BATCH_SIZE)
batches_json = [json.dumps(batch, indent=2) for batch in batches]

analysis_prompt = f"""
Analyze these evaluation results and provide a comprehensive report.

## Statistics
- Total evaluations: {stats['total']}
- Mean score: {stats['mean_score']}
- Low scoring (<{SCORE_THRESHOLD}): {stats['low_scoring_count']} ({stats['low_scoring_pct']}%)
- Score range: {stats['min_score']} - {stats['max_score']}

## Evaluator Breakdown
{json.dumps(stats['by_evaluator'], indent=2)}

## Current Agent System Prompt (to be improved)
{AGENT_SYSTEM_PROMPT}

## Low-Scoring Evaluations
There are {len(batches)} batches of evaluations to analyze.
Use the analyze_batch tool for each batch:

"""

for i, batch_json in enumerate(batches_json):
    analysis_prompt += f"\nBatch {i+1}:\n{batch_json}\n"

# Run the analysis
result_text = str(orchestrator(analysis_prompt))

# Calculate elapsed time
elapsed_time = round(time.time() - start_time, 1)

print(f"\n{'='*80}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*80}")
print(f"Processing time: {elapsed_time}s")
print(f"{'='*80}\n")

### View and save results

# ============================================
# DISPLAY AND SAVE RESULTS
# ============================================

# Display in terminal or Jupyter
if USE_IPYTHON:
    display(Markdown(result_text))
else:
    print(result_text)

from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"analysis_report_{timestamp}.md"

report_content = f"""# Evaluation Analysis Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Evaluations Analyzed:** {len(low_scoring)} low-scoring out of {stats['total']} total
**Processing Time:** {elapsed_time}s
**Score Threshold:** {SCORE_THRESHOLD}

---

## Statistics Summary

- **Total Evaluations:** {stats['total']}
- **Mean Score:** {stats['mean_score']}
- **Score Range:** {stats['min_score']} - {stats['max_score']}
- **Low Scoring Count:** {stats['low_scoring_count']} ({stats['low_scoring_pct']}%)

### By Evaluator

{chr(10).join([f"- **{evaluator}**: mean={eval_stats['mean']}, count={eval_stats['count']}" for evaluator, eval_stats in stats['by_evaluator'].items()])}

---

{result_text}

---

## Next Steps

1. Review the analysis above
2. Copy the "Complete Updated System Prompt" section
3. Update your system-prompt.txt file
4. Re-run evaluations to verify improvements
5. Repeat this process until scores are satisfactory

## Files Generated

- Analysis Report: {output_file}
- Original Prompt: {SYSTEM_PROMPT_FILE}

"""

with open(output_file, "w", encoding='utf-8') as f:
    f.write(report_content)

print(f"\n{'='*80}")
print(f"✓ Report saved to: {output_file}")
print(f"{'='*80}")
print(f"\nNext steps:")
print(f"1. Review the analysis in {output_file}")
print(f"2. Update {SYSTEM_PROMPT_FILE} with the suggested changes")
print(f"3. Re-run your evaluations to verify improvements")
print(f"\n{'='*80}\n")

