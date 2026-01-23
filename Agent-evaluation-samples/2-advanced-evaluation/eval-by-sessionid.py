"""
Comprehensive Agent Evaluation Script

This script evaluates an agent across multiple evaluator types:
- Flexible Evaluators (work at session or trace level)
- Session-Only Evaluators (evaluate entire conversation)
- Span-Only Evaluators (evaluate individual tool calls)

The script:
1. Invokes the agent 3 times with different prompts
2. Waits for CloudWatch logs to populate (3 minutes)
3. Runs all evaluator groups with retry logic
4. Displays comprehensive results

Total evaluators tested: 13
Expected runtime: ~5-6 minutes
"""

from bedrock_agentcore_starter_toolkit import Evaluation, Observability
import os
import json
import uuid
import boto3
import time
from boto3.session import Session

# Configuration - UPDATE THESE VALUES
region = "us-east-1"
agent_id = "ac_eval_strands2-kbwmZfG9EB"  # UPDATE: Your agent ID
agent_arn = "arn:aws:bedrock-agentcore:us-east-1:319645399632:runtime/ac_eval_strands2-kbwmZfG9EB"  # UPDATE: Your agent ARN

# Generate new session ID for this evaluation run
session_id_strands = str(uuid.uuid4())

print(f"Region: {region}")
print(f"Agent ID: {agent_id}")
print(f"Session ID: {session_id_strands}\n")

metadata = {
    "experiment": "evaluation_test",
    "description": "Testing all evaluator scopes"
}

# Create clients
eval_client = Evaluation(region=region)
client = boto3.client('bedrock-agentcore', region_name=region)    


# Evaluator Groups
FLEXIBLE_EVALUATORS = [
    "Builtin.Correctness",
    "Builtin.Faithfulness",
    "Builtin.Helpfulness",
    "Builtin.ResponseRelevance",
    "Builtin.Conciseness",
    "Builtin.Coherence",
    "Builtin.InstructionFollowing",
    "Builtin.Refusal",
    "Builtin.Harmfulness",
    "Builtin.Stereotyping"
]

SESSION_ONLY_EVALUATORS = ["Builtin.GoalSuccessRate"]

SPAN_ONLY_EVALUATORS = [
    "Builtin.ToolSelectionAccuracy",
    "Builtin.ToolParameterAccuracy"
]


test_groups = [
    {
        "name": "Flexible Evaluators (session scope)",
        "evaluators": FLEXIBLE_EVALUATORS,
        "scope": "session"
    },
    {
        "name": "Session-Only Evaluators",
        "evaluators": SESSION_ONLY_EVALUATORS,
        "scope": "session"
    },
    {
        "name": "Span-Only Evaluators",
        "evaluators": SPAN_ONLY_EVALUATORS,
        "scope": "span"
    }
]


# Prepare payload
payload = json.dumps({"prompt": "How much is 2+2?"})

print(f"\nInvoking agent with session ID: {session_id_strands}")

# Invoke agent
response = client.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    runtimeSessionId=session_id_strands,
    payload=payload,
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print(f"Agent Response: {response_data}\n")

# Second invocation - weather question
payload = json.dumps({"prompt": "What is the weather now?"})
response = client.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    runtimeSessionId=session_id_strands,
    payload=payload,
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print(f"Agent Response: {response_data}\n")

# Third invocation - capital question
payload = json.dumps({"prompt": "Can you tell me the capital of the US?"})
response = client.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    runtimeSessionId=session_id_strands,
    payload=payload,
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print(f"Agent Response: {response_data}\n")



# IMPORTANT: Wait for CloudWatch logs to populate
# There is a 2-5 minute delay before observability data becomes available
print("â³ Waiting for CloudWatch logs to populate (this takes 2-5 minutes)...")
print("   CloudWatch needs time to ingest the observability data from the agent invocation.")

WAIT_TIME = 180  # 3 minutes (180 seconds)
for remaining in range(WAIT_TIME, 0, -30):
    print(f"   Waiting... {remaining} seconds remaining")
    time.sleep(30)

print("âœ“ Wait complete. Attempting evaluation...\n")

# Run evaluations with retry logic
max_retries = 3
retry_delay = 60  # 1 minute between retries
all_results = []

for attempt in range(1, max_retries + 1):
    try:
        print(f"Evaluation attempt {attempt}/{max_retries}...\n")
        
        # Run all evaluation groups
        for group in test_groups:
            print(f"{'='*80}")
            print(f"Running: {group['name']}")
            print(f"Evaluators: {', '.join(group['evaluators'])}")
            print(f"{'='*80}")
            
            try:
                # Run each evaluator in the group
                for evaluator in group['evaluators']:
                    print(f"  Running {evaluator}...")
                    results = eval_client.run(
                        agent_id=agent_id,
                        session_id=session_id_strands,
                        evaluators=[evaluator]
                    )
                    
                    # Collect results
                    for r in results.results:
                        print(f"    âœ“ {r.evaluator_name}: {r.value} - {r.label}")
                        all_results.append(r)
                
                print(f"âœ“ Completed group: {group['name']}\n")
                    
            except Exception as e:
                print(f"âœ— Error in group '{group['name']}': {e}\n")
                # Continue with next group even if this one fails
                continue
        
        print("âœ“ All evaluations successful!\n")
        break  # Success, exit retry loop
        
    except RuntimeError as e:
        if "No spans found" in str(e):
            if attempt < max_retries:
                print(f"âš  No spans found yet. Waiting {retry_delay} more seconds before retry {attempt + 1}...")
                time.sleep(retry_delay)
            else:
                print(f"\nâœ— Error: Still no spans found after {max_retries} attempts.")
                print("\nPossible causes:")
                print("  1. Observability is not enabled for this agent")
                print("  2. CloudWatch logs are taking longer than expected to populate")
                print("  3. The session didn't generate any traces")
                print("\nTroubleshooting:")
                print(f"  - Check CloudWatch Logs for session: {session_id_strands}")
                print(f"  - Verify observability is enabled in agent configuration")
                print("  - Try running evaluation again in a few minutes")
                raise
        else:
            raise

# Display summary
print("\n" + "="*80)
print("EVALUATION SUMMARY")
print("="*80)
print(f"Total evaluations completed: {len(all_results)}")
print(f"Session ID: {session_id_strands}")
print(f"Agent ID: {agent_id}")
print("\nResults by evaluator:")
for r in all_results:
    print(f"  â€¢ {r.evaluator_name}: {r.value} ({r.label})")
print("\nâœ“ All evaluations complete!")

