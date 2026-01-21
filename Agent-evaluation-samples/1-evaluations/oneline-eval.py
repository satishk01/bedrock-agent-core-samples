import boto3
import json

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
    print("Note: Running in terminal mode (not Jupyter), using print for output\n")

# Get region from boto3 session
region = boto3.Session().region_name
print(f"Region: {region}\n")

agentcore_client = boto3.client(
    'bedrock-agentcore',
    region_name=region
)

agent_arn = "arn:aws:bedrock-agentcore:us-east-1:319645399632:runtime/ac_eval_strands2-bGkU1WENqY"


def invoke_agent_runtime(agent_arn, prompt):
    """Invoke the agent runtime and display the response."""
    print(f"{'='*80}")
    print(f"Prompt: {prompt}")
    print(f"{'='*80}")
    
    boto3_response = agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        qualifier="DEFAULT",
        payload=json.dumps({"prompt": prompt})
    )
    
    if "text/event-stream" in boto3_response.get("contentType", ""):
        content = []
        for line in boto3_response["response"].iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    print(line)
                    content.append(line)
        
        response_text = "\n".join(content)
        if USE_IPYTHON:
            display(Markdown(response_text))
        else:
            print(f"\nAgent Response:\n{response_text}\n")
    else:
        try:
            events = []
            for event in boto3_response.get("response", []):
                events.append(event)
            
            if events:
                response_data = json.loads(events[0].decode("utf-8"))
                if USE_IPYTHON:
                    display(Markdown(json.dumps(response_data, indent=2)))
                else:
                    print(f"\nAgent Response:\n{json.dumps(response_data, indent=2)}\n")
        except Exception as e:
            print(f"Error reading EventStream: {e}")
    
    return boto3_response

print("\n" + "="*80)
print("INVOKING AGENT WITH MULTIPLE PROMPTS")
print("="*80 + "\n")

response = invoke_agent_runtime(
    agent_arn,
    "How much is 7+9+10*2?"
)

response = invoke_agent_runtime(
    agent_arn,
    "Is it raining?"
)

response = invoke_agent_runtime(
    agent_arn,
    "how much is 20% of 300?"
)

response = invoke_agent_runtime(
    agent_arn,
    "What can you do?"
)

response = invoke_agent_runtime(
    agent_arn,
    "What is the capital of NY State?"
)

print("\n" + "="*80)
print("ALL INVOCATIONS COMPLETE")
print("="*80)

