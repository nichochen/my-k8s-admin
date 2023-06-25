import vertexai
import config
from vertexai.language_models import TextGenerationModel
from vertexai.preview.language_models import CodeGenerationModel
import subprocess
import os
from google.cloud.bigquery.client import Client
from vertexai.preview.language_models import ChatModel, InputOutputTextPair
import config
from termcolor import colored
import json

# for development only
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.gcp_service_account_key
#if os.getenv('MY_K8S_ADMIN_GCP_PROJECT') is not None:
#    gcp_project = os.getenv('MY_K8S_ADMIN_GCP_PROJECT')

class LLM:
    #init

    chat_session=None

    text_llm_parameters = {
    "temperature": 0,
    "max_output_tokens": 512,
    "top_p": 0.4,
    "top_k": 20
    }

    chat_llm_parameters = {
        "temperature": 0,
        "max_output_tokens": 256,
        "top_p": 0.3,
        "top_k": 40
    }

    code_llm_parameters = {
    "temperature": 0,
    "max_output_tokens": 256
    }

    prompt_evaluation_template = """
You are an input evaluator. 
You will screen the input.

The input MUST meet ALL following requirements. Otherwise you should issue a warning and provide reasons:
1. The input should be in a positive tone.
2. The input must be an instruction.
3. The input should not be a question or a statement.
4. The input should be related to Kubernetes technical subjects.
5. If the user say thank you, you reject the request, but response to it with a positive tone.
5. If the user say hi or hello, you reject the request, but response to it with a positive tone.

Your response should be in json format, following is the schema:
valid: 1 if the input is valid, 0 if the input is invalid
message: if the input is inappropriate, please issue an warning and provide suggestions. If the prompt is valid,
type: return the type of the input: create, update, delete or list. Leave it blank when valid is 0

Do not use markdown in the output

input: {input}
output:
    """

    generate_deployment_command_template = """
You are a kubectl command generator.
Your output will be valid a kubectl command.

kubectl command example:
kubctl get pods

Additional kubectl commands:
{additional_kubectl_examples}

Do not use markdown in the output

Now let's generate a kubectl command:
input: {input}
output:
"""

    deployment_command_validator_template = """
kubectl command syntax example:
kubectl get pods

You are a kubectl command validator.
1. You will check the input is valid kubectl command or not.
2. The input must contains only 1 line
3. The input must be a kubectl command
4. deny kubectl delete node

Your response will be in json format and follow following schema:
valid: 1 if the input is valid, 0 if the input is invalid
Message: if the input is invalid, please issue an warning and provide reasons.

Check carefully against the kubectl syntax documentation
Think step by step

Do not use markdown in the output

input: {input}
output:
"""

    chat_model_context='''
You are a kubernetes technical support.
Your name is 'My K8S Admin'.
You will chat with the user with a friendly and positive tone.
Your responses will always be concise.
You will never provide information other than Kubernetes technical support. 
When provide kubernetes object definitions, make the output clean and concise.
My K8S Admin is created by Nicholas Chen, a Generative AI ambassador at Google.
If the user want you to deploy/create/change something, please ask the user to hit Enter to enter the action mode.

You will be very honest. If you don't know or not sure, do not make things up, just say you don't know.
    '''

    additional_kubectl_examples='''kubectl create token admin --duration 10h'''
    text_model = TextGenerationModel.from_pretrained(config.gcp_text_llm)
    chat_model = ChatModel.from_pretrained(config.gcp_chat_llm)
    code_model = CodeGenerationModel.from_pretrained(config.gcp_code_llm)

    def evaluate_prompt(self, input):
        prompt = self.prompt_evaluation_template.format(input=input)
        response = self.text_model.predict(prompt,**self.text_llm_parameters)
        return to_json(response.text.replace("```", ''))

    def generate_deployment_command(self, input):
        prompt = self.generate_deployment_command_template.format(additional_kubectl_examples=self.additional_kubectl_examples,input=input)
        response = self.code_model.predict(prompt,**self.code_llm_parameters)
        return response.text.replace("```", '')
    
    def deployment_command_validation(self, input):
        prompt = self.deployment_command_validator_template.format(input=input)
        response = self.code_model.predict(prompt,**self.code_llm_parameters)
        return to_json(response.text.replace("```", ''))

    def __init__(self):
        # todo: implement lazy init
        vertexai.init(project=config.gcp_project, location=config.gcp_region)
        self.chat_session = self.chat_model.start_chat(context=self.chat_model_context,)

    def dummy_k8s_command_executor(self, command, confirm=True, show_command=True):
        print(colored(f">> Executing command: {command}", 'light_grey'))
        print(colored(">> Done!", 'light_grey'))
        return ''

    def k8s_command_executor(self, command, confirm=True, show_command=True):

        if show_command:
            print(colored(f">> Executing command: {command}", 'light_grey'))

        if confirm:
            print(colored('Do you want to continue? yes/no: ', 'yellow'), end='')
            answer = input()
            if answer.lower() != 'yes':
                return ''

        stdoutdata = subprocess.getoutput(command)
        self.chat_session.send_message(stdoutdata, **self.chat_llm_parameters)
        print(colored(stdoutdata, 'white'))
        print(colored(">> Done!", 'light_grey'))
        return ''

    def chat(self, input):
        response = self.chat_session.send_message(input, **self.chat_llm_parameters)
        return response.text

    def action(self, input, executor=None, debug=False):
        _input = input
        confirm = True
        if input.endswith('+'):
            _input = input[:-1]
            confirm = False

        output = self.evaluate_prompt(_input)
        print(colored("I got it...", 'dark_grey'))
        print(colored("[1/4]Evaluating your input...", 'dark_grey'))
        if debug: print_output("DEBUG", _input, output)

        if output['valid']:
            is_list = output['type'] == 'list'
            if  is_list: confirm = False
            print(colored("[2/4]Generating the deployment command..", 'dark_grey'))
            command = self.generate_deployment_command(_input)
            if debug: print_output("DEBUG", _input, command)

            print(colored("[3/4]Validating the deployment command..", 'dark_grey'))
            validation = self.deployment_command_validation(command)
            if debug: print_output("DEBUG", command, validation)

            if validation['valid']:
                print(colored("[4/4]Start running your deployment..", 'dark_grey'))
                if executor == None:
                    executor = self.k8s_command_executor
                return executor(command, confirm=confirm)

            else:
                print(colored("OMG: Not able to generate the deployment command, please check your input", 'red'))
                return ''

        else:
            print(colored(output['message'], 'yellow'))
            return ''
            
# helper functions
# todo: move to a helper class
def to_json(input):
  res =  {}
  try:
    res = json.loads(input)
  except:
    print(f"Error:invalid JSON string:{input}")
  return res

def print_output(action, input, output):
  prefix = ">> "
  print(f"{prefix}Action: {action}")
  print(f"{prefix}INPUT: {input}")
  print(f"{prefix}OUTPUT: {output}")


