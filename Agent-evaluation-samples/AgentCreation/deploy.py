from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import uuid
import time

boto_session = Session()
region = "us-east-1"
print(f"Using region: {region}")

agentcore_runtime = Runtime()

agent_name = "ac_eval_strands2"
response = agentcore_runtime.configure(
    entrypoint="eval_agent_strands.py",
    auto_create_execution_role=True,
    auto_create_ecr=True,
    requirements_file="requirements.txt",
    region=region,
    agent_name=agent_name,
    idle_timeout=120
)
launch_result_strands = agentcore_runtime.launch()
print(f"Strands agent deployment started: {launch_result_strands}")

