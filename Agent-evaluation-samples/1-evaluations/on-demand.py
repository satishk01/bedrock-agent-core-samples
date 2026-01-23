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
    # Check if we're actually in a Jupyter/IPython interactive environment
    ipython = get_ipython()
    USE_IPYTHON = ipython is not None and 'IPKernelApp' in ipython.config
except (ImportError, AttributeError):
    USE_IPYTHON = False

if not USE_IPYTHON:
    print("Note: Running in terminal mode (not Jupyter), using print for output")

boto_session = Session()
region = boto_session.region_name
print(f"Region: {region}")
agent_arn='arn:aws:bedrock-agentcore:us-east-1:319645399632:runtime/ac_eval_strands2-9tl3F0FgeM'
agent_id='ac_eval_strands2-9tl3F0FgeM'

# Create clients
eval_client = Evaluation(region=region)
client = boto3.client('bedrock-agentcore', region_name=region)

# Prepare payload
payload = json.dumps({"prompt": "How much is 2+2?"})
session_id_strands = str(uuid.uuid4())

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
print("? Waiting for CloudWatch logs to populate (this takes 2-5 minutes)...")
print("   CloudWatch needs time to ingest the observability data from the agent invocation.")

WAIT_TIME = 180  # 3 minutes (180 seconds)
for remaining in range(WAIT_TIME, 0, -30):
    print(f"   Waiting... {remaining} seconds remaining")
    time.sleep(30)

print("? Wait complete. Attempting evaluation...\n")

# Try evaluation with retry logic
max_retries = 3
retry_delay = 60  # 1 minute between retries

goal_sucess_results = None
correctness_results = None
parameter_results = None

for attempt in range(1, max_retries + 1):
    try:
        print(f"Evaluation attempt {attempt}/{max_retries}...")
        
        # Run all evaluations
        goal_sucess_results = eval_client.run(
            agent_id=agent_id,
            session_id=session_id_strands, 
            evaluators=["Builtin.GoalSuccessRate"]
        )
        
        correctness_results = eval_client.run(
            agent_id=agent_id,
            session_id=session_id_strands, 
            evaluators=["Builtin.Correctness"]
        )
        
        parameter_results = eval_client.run(
            agent_id=agent_id,
            session_id=session_id_strands, 
            evaluators=["Builtin.ToolParameterAccuracy", "Builtin.ToolSelectionAccuracy"]
        )
        
        print("? Evaluation successful!\n")
        break  # Success, exit retry loop
    except RuntimeError as e:
        if "No spans found" in str(e):
            if attempt < max_retries:
                print(f"? No spans found yet. Waiting {retry_delay} more seconds before retry {attempt + 1}...")
                time.sleep(retry_delay)
            else:
                print(f"\n? Error: Still no spans found after {max_retries} attempts.")
                print("\nPossible causes:")
                print("  1. Observability is not enabled for this agent")
                print("  2. CloudWatch logs are taking longer than expected to populate")
                print("  3. The session didn't generate any traces")
                print("\nTroubleshooting:")
                print(f"  - Check CloudWatch Logs for session: {session_id_strands}")
                print("  - Verify observability is enabled in agent configuration")
                print("  - Try running evaluation again in a few minutes")
                raise
        else:
            raise

# Display results
print("=" * 80)
print("EVALUATION RESULTS")
print("=" * 80)

# Display Goal Success Results
if goal_sucess_results:
    print("\n" + "=" * 80)
    print("GOAL SUCCESS RATE RESULTS")
    print("=" * 80)
    for i, result in enumerate(goal_sucess_results.results, 1):
        information = f"""
Result #{i}:
-----------
Goal Success: {result.label} ({result.value})

Explanation:
{result.explanation}

Token Usage: {result.token_usage}

Context: {result.context}
"""
        if USE_IPYTHON:
            display(Markdown(information))
        else:
            print(information)
            print("-" * 80)

# Display Correctness Results
if correctness_results:
    print("\n" + "=" * 80)
    print("CORRECTNESS RESULTS")
    print("=" * 80)
    for i, result in enumerate(correctness_results.results, 1):
        information = f"""
Result #{i}:
-----------
Correctness: {result.label} ({result.value})

Explanation:
{result.explanation}

Token Usage: {result.token_usage}

Context: {result.context}
"""
        if USE_IPYTHON:
            display(Markdown(information))
        else:
            print(information)
            print("-" * 80)

# Display Tool Parameter/Selection Results
if parameter_results:
    print("\n" + "=" * 80)
    print("TOOL ACCURACY RESULTS")
    print("=" * 80)
    for i, result in enumerate(parameter_results.results, 1):
        information = f"""
Result #{i}:
-----------
Metric: {result.evaluator_name}
Value: {result.label} ({result.value})

Explanation:
{result.explanation}

Token Usage: {result.token_usage}

Context: {result.context}
"""
        if USE_IPYTHON:
            display(Markdown(information))
        else:
            print(information)
            print("-" * 80)

print("\n? All evaluations complete!")    

