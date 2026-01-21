from bedrock_agentcore_starter_toolkit import Evaluation, Observability
import os
import json
from boto3.session import Session
from IPython.display import Markdown, display


boto_session = Session()
region = boto_session.region_name
print(region)

agent_id="ac_eval_strands2-bGkU1WENqY" 

eval_client = Evaluation(region=region)

response = eval_client.create_online_config(
    agent_id=agent_id,
    config_name="strands_agent_eval2",
    sampling_rate=100,
    evaluator_list=[
        "Builtin.GoalSuccessRate", "Builtin.Correctness", 
        "Builtin.ToolParameterAccuracy", "Builtin.ToolSelectionAccuracy"
    ],
    config_description="Strands agent online evaluation test",
    auto_create_execution_role=True
)

print("Online Evaluation Configuration Id:", response['onlineEvaluationConfigId'])
