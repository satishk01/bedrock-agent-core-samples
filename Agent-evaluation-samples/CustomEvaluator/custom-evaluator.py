import os
import json
from bedrock_agentcore_starter_toolkit import Evaluation

# Create Evaluation client using AgentCore SDK
# This automatically handles region detection and boto3 client creation
print("Creating Evaluation client...")
eval_client = Evaluation()
print("? Evaluation client created successfully\n")

available_evaluators = eval_client.list_evaluators()
available_evaluators

##print("available_evaluators .....")
##print(available_evaluators)

# Read custom evaluator configuration
print("Reading custom metric configuration from metric.json...")
with open("metric.json") as f:
    evaluator_config = json.load(f)

print(f"? Configuration loaded successfully")
print(f"\nConfig preview:\n{json.dumps(evaluator_config, indent=2)}\n")

# Create custom evaluator
print("Creating custom evaluator...")
try:
    custom_evaluator = eval_client.create_evaluator(
        name="response_quality_for_scope",
        level="TRACE",
        description="Response quality evaluator",
        config=evaluator_config
    )
    
    evaluator_id = custom_evaluator['evaluatorId']
    print(f"\n? Evaluator created successfully!")
    print(f"  Evaluator ID: {evaluator_id}")
    print(f"  Evaluator ARN: {custom_evaluator.get('evaluatorArn', 'N/A')}")
    print(f"  Status: {custom_evaluator.get('status', 'N/A')}")
    print(f"\nFull response:\n{json.dumps(custom_evaluator, indent=2, default=str)}")
    
except ImportError as e:
    print(f"\n? Import Error: {str(e)}")
    print("\nThe 'Evaluation' class is not available in your version.")
    print("\nPlease upgrade bedrock-agentcore-starter-toolkit:")
    print("  pip install --upgrade bedrock-agentcore-starter-toolkit")
    print("\nOr check your current version:")
    print("  pip show bedrock-agentcore-starter-toolkit")
    raise
    
except Exception as e:
    print(f"\n? Error creating evaluator: {str(e)}")
    print(f"\nError type: {type(e).__name__}")
    raise

