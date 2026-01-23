"""
Pipeline-Based Agent Evaluation Script

This script runs a pipeline of evaluations across multiple prompts:
1. Invokes the agent with multiple test prompts
2. Waits for CloudWatch logs to populate
3. Evaluates each session with selected evaluators
4. Collects and displays comprehensive results

Features:
- Multiple prompts with metadata tracking
- Multi-turn conversations (same session ID)
- Batch evaluation across all prompts
- Detailed results summary

Expected runtime: ~5-10 minutes depending on number of prompts
"""

from bedrock_agentcore_starter_toolkit import Evaluation, Observability
import os
import json
import uuid
import boto3
import time
from boto3.session import Session

# Try to import IPython display and check if we're in a Jupyter environment
try:
    from IPython.display import Markdown, display
    from IPython import get_ipython
    ipython = get_ipython()
    USE_IPYTHON = ipython is not None and 'IPKernelApp' in ipython.config
except (ImportError, AttributeError):
    USE_IPYTHON = False

if not USE_IPYTHON:
    print("Note: Running in terminal mode (not Jupyter), using print for output\n")

# Configuration - UPDATE THESE VALUES
region = "us-east-1"
agent_id = "ac_eval_strands2-kbwmZfG9EB"  # UPDATE: Your agent ID
agent_arn = "arn:aws:bedrock-agentcore:us-east-1:319645399632:runtime/ac_eval_strands2-kbwmZfG9EB"  # UPDATE: Your agent ARN

print(f"Region: {region}")
print(f"Agent ID: {agent_id}\n")

# Create clients
eval_client = Evaluation(region=region)
client = boto3.client('bedrock-agentcore', region_name=region)

# Experiment configuration
EXPERIMENT_NAME = "comprehensive_evaluation_v1"
EXPERIMENT_DELAY = 180  # Wait time in seconds (3 minutes)

# Create a planned session for multi-turn conversation
planned_session = str(uuid.uuid4())

# Define test prompts with metadata
EXPERIMENT_PROMPTS = [
    {"prompt": "What is 2 + 2?", "session_id": "", "metadata": {"category": "math", "turn": 1}},
    {"prompt": "What is the capital of France?", "session_id": "", "metadata": {"category": "geography", "turn": 1}},
    {"prompt": "Tell me about quantum physics", "session_id": "", "metadata": {"category": "science", "turn": 1}},
    {"prompt": "Hello, can you help me with math?", "session_id": planned_session, "metadata": {"category": "math", "turn": 1}},
    {"prompt": "What is 15 * 23?", "session_id": planned_session, "metadata": {"category": "math", "turn": 2}},
]

# Evaluators to run (you can customize this list)
EXPERIMENT_EVALUATORS = [
    "Builtin.Helpfulness",
    "Builtin.Correctness",
    "Builtin.GoalSuccessRate"
]

print(f"Experiment: {EXPERIMENT_NAME}")
print(f"Prompts: {len(EXPERIMENT_PROMPTS)}")
print(f"Evaluators: {len(EXPERIMENT_EVALUATORS)}")
print(f"Evaluators: {', '.join(EXPERIMENT_EVALUATORS)}\n")

# ============================================================================
# STEP 1: Invoke agent with all prompts
# ============================================================================
print("="*80)
print("STEP 1: INVOKING AGENT WITH ALL PROMPTS")
print("="*80 + "\n")

invocation_results = []

for i, config in enumerate(EXPERIMENT_PROMPTS, 1):
    prompt_text = config["prompt"]
    session_id = config.get("session_id", "")
    metadata = config.get("metadata", {})
    
    # Generate new session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    print(f"[{i}/{len(EXPERIMENT_PROMPTS)}] Prompt: {prompt_text}")
    print(f"         Session ID: {session_id}")
    print(f"         Metadata: {metadata}")
    
    try:
        # Invoke agent
        payload = json.dumps({"prompt": prompt_text})
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            runtimeSessionId=session_id,
            payload=payload,
        )
        
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        print(f"         Response: {response_data}\n")
        
        invocation_results.append({
            "session_id": session_id,
            "prompt": prompt_text,
            "response": response_data,
            "metadata": metadata
        })
        
    except Exception as e:
        print(f"         âœ— Error: {e}\n")
        invocation_results.append({
            "session_id": session_id,
            "prompt": prompt_text,
            "error": str(e),
            "metadata": metadata
        })

print(f"âœ“ Completed {len(invocation_results)} agent invocations\n")

# ============================================================================
# STEP 2: Wait for CloudWatch logs
# ============================================================================
print("="*80)
print("STEP 2: WAITING FOR CLOUDWATCH LOGS")
print("="*80)
print("â³ Waiting for CloudWatch logs to populate (this takes 2-5 minutes)...")
print("   CloudWatch needs time to ingest the observability data.\n")

for remaining in range(EXPERIMENT_DELAY, 0, -30):
    print(f"   Waiting... {remaining} seconds remaining")
    time.sleep(30)

print("âœ“ Wait complete. Starting evaluations...\n")

# ============================================================================
# STEP 3: Run evaluations for each session
# ============================================================================
print("="*80)
print("STEP 3: RUNNING EVALUATIONS")
print("="*80 + "\n")

batch_results = []
max_retries = 2
retry_delay = 60

for i, inv_result in enumerate(invocation_results, 1):
    if "error" in inv_result:
        print(f"[{i}/{len(invocation_results)}] Skipping (invocation failed): {inv_result['prompt']}\n")
        batch_results.append(inv_result)
        continue
    
    session_id = inv_result["session_id"]
    prompt = inv_result["prompt"]
    metadata = inv_result["metadata"]
    
    print(f"[{i}/{len(invocation_results)}] Evaluating: {prompt}")
    print(f"         Session ID: {session_id}")
    
    eval_results = []
    
    for attempt in range(1, max_retries + 1):
        try:
            # Run each evaluator
            for evaluator in EXPERIMENT_EVALUATORS:
                print(f"         Running {evaluator}...", end=" ")
                results = eval_client.run(
                    agent_id=agent_id,
                    session_id=session_id,
                    evaluators=[evaluator]
                )
                
                for r in results.results:
                    print(f"âœ“ {r.value} ({r.label})")
                    eval_results.append({
                        "evaluator": r.evaluator_name,
                        "value": r.value,
                        "label": r.label,
                        "explanation": r.explanation
                    })
            
            break  # Success, exit retry loop
            
        except RuntimeError as e:
            if "No spans found" in str(e) and attempt < max_retries:
                print(f"âš  No spans found. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"âœ— Error: {e}")
                break
        except Exception as e:
            print(f"âœ— Error: {e}")
            break
    
    batch_results.append({
        "session_id": session_id,
        "prompt": prompt,
        "response": inv_result["response"],
        "metadata": metadata,
        "evaluations": eval_results
    })
    print()

# ============================================================================
# STEP 4: Display summary
# ============================================================================
print("="*80)
print("EVALUATION SUMMARY")
print("="*80)
print(f"Experiment: {EXPERIMENT_NAME}")
print(f"Total prompts: {len(EXPERIMENT_PROMPTS)}")
print(f"Successful evaluations: {sum(1 for r in batch_results if 'evaluations' in r and r['evaluations'])}")
print(f"Failed: {sum(1 for r in batch_results if 'error' in r or ('evaluations' in r and not r['evaluations']))}\n")

for i, result in enumerate(batch_results, 1):
    print(f"\n[{i}] Prompt: {result['prompt']}")
    print(f"    Session: {result['session_id']}")
    print(f"    Metadata: {result.get('metadata', {})}")
    
    if 'error' in result:
        print(f"    Status: âœ— Error - {result['error']}")
    elif 'evaluations' in result and result['evaluations']:
        print(f"    Status: âœ“ Success")
        print(f"    Evaluations:")
        for ev in result['evaluations']:
            print(f"      â€¢ {ev['evaluator']}: {ev['value']} ({ev['label']})")
    else:
        print(f"    Status: âš  No evaluation results")

print("\n" + "="*80)
print("âœ“ Pipeline evaluation complete!")
print("="*80)

# Generate dashboard automatically
try:
    from dashboard_generator import generate_dashboard
    
    # Prepare data for dashboard (convert batch_results to proper format)
    dashboard_data = []
    for result in batch_results:
        if 'evaluations' in result and result['evaluations']:
            dashboard_data.append({
                'session_id': result['session_id'],
                'metadata': result.get('metadata', {}),
                'results': result['evaluations']
            })
    
    if dashboard_data:
        dashboard_file = generate_dashboard(dashboard_data)
        print(f"\nðŸ“Š Dashboard available at: {dashboard_file}")
except ImportError:
    print("\nâš  dashboard_generator.py not found - skipping dashboard generation")
except Exception as e:
    print(f"\nâš  Error generating dashboard: {e}")

