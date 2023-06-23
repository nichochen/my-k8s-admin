import sys
import llm
import config
import os
from termcolor import colored

class K8SAdmin:
    
    llm = llm.LLM()
    shell_intput_history = []
    shell_output_history = []
    history_counter = 0
    current_mode =  0
    modes = ['chat','action']
    mode_ids = {}
    mode_ids['action'] = colored('(action)==>> ','blue')
    mode_ids['chat'] = colored('(_chat_)-->> ','cyan')
    command_prompt_prefix = colored('k8s-admin ', 'green')
    command_prompt = command_prompt_prefix + mode_ids[modes[current_mode]]
    command_prompt = f"{history_counter}|{command_prompt}"
   

    def __init__(self):
        pass

    def shell(self):
        print(colored(config.text_banner, "yellow"))
        print(f"Version: {config.version}|By Nicholas Chen")
        print(colored('Hi, I am your k8s admin! Enter "help" to learn more.', 'yellow'))

        while True:
            self.history_counter += 1
            self.command_prompt = self.command_prompt_prefix + self.mode_ids[self.modes[self.current_mode]]
            self.command_prompt = f"{self.history_counter}|{self.command_prompt}"
            line = input(self.command_prompt)

            self.shell_intput_history.append(line)

            if line == 'exit':
                break
            elif line == 'clear':
                if os.name == 'nt':
                    os.system('cls')
                else:
                    os.system('clear') 
                continue
            elif line == '':
                self.current_mode = (self.current_mode + 1) % len(self.modes)
                continue
            elif line == 'help':
                self.shell_help()
                continue
            elif line == 'history' or line == 'his':
                self.history()
            else:
                if self.current_mode == 1:
                    if line.lower().startswith('apply @'):
                        num = -1
                        items = line.split('apply @')
                        if len(items) > 0:
                            if items[1] == '':
                                pass
                            else:
                                n = items[1]
                                try:
                                    num = int(n) -1          
                                except:
                                    print(f"Invalid history number {n}.")
                                    pass
                        self.action_apply(num)
                        continue
                    
                    print(self.action(line))
                elif self.current_mode == 0:
                    print(colored(self.chat(line), 'white'))
                continue

    def action_apply(self, history_number):
        if history_number >= len(self.shell_output_history):
            print(f"Invalid history number {history_number}.")
            return

        definition = self.shell_output_history[history_number].replace('```yaml','')
        items=definition.split("```")

        if len(items) < 3:
            return 'No definition found!'
        else:
            definition = items[1]

        print(colored('Are you sure your want to apply following definition?', 'yellow'))
        print(f'{definition}')
        print(colored('yes/no: ', 'yellow'), end='')

        answer = input()
        if answer.lower() == 'yes':
            print('\rApplying the change...') 
            temp_file='/tmp/k8s-admin-temp.yaml'
            file = open(temp_file,'w')
            file.write(definition)
            file.close()
            
            self.llm.k8s_command_executor(f'kubectl apply -f {temp_file}', confirm=False, show_command=False)  
            return 'Done!'


    def action(self, input):
        return self.llm.action(input)
    
    def chat(self, input_text):
        response = self.llm.chat(input_text)
        _response = response
        if '```' in response:
            _response = response[:response.rindex('```') + 3]

        self.shell_output_history.append(_response)
        return _response

    def qa(self, input):
        pass

    def code(self, input):
        pass

    def history(self):
        for i in range(len(self.shell_output_history)):
            print(f"  {i}\t|{self.shell_output_history[i]}")

    def run(self, input):
        self.action(input)

    def shell_help(self):
        help_text=f'''--- My K8S Admin {config.version}---
Hello! I am your personal k8s admin!
Hit 'Enter' to switch between modes.
> Chat mode: chat with me.
> Action mode: let me know what you want to do.

Here are some tips for speeding up your work:
> Type 'history' or 'his' to see model output history.
> Type 'apply @<history number>' to apply a previous definition.
> Type 'apply @' to apply the last definition.
> Add '+' at the end of your command to skip confirmation.
> Type 'help' to see this help text again.

Options:
-s，run interactive shell
-a，run non-interactive action mode
-h，help

You can also type 'exit' to exit. Have a good day!
'''
        print(help_text)

def app_help():
    help_text=f'''--- My K8S Admin {config.version}---
Hello! I am your personal k8s admin!
Options:
-s，run interactive shell
-a，run non-interactive action mode, e.g. k8s-admin -a "list all pods"
-h，help

When you are in the interactive shell, you can:
Hit 'Enter' to switch between modes.
> Chat mode: chat with me.
> Action mode: let me know what you want to do.

> Type 'history' or 'his' to see model output history.
> Type 'apply @<history number>' to apply a previous definition.
> Type 'apply @' to apply the last definition.
> Add '+' at the end of your command to skip confirmation.
> Type 'help' to see this help text again.

You can also type 'exit' to exit.
'''
    print(help_text)
# the start of the program
if __name__ == '__main__':
    # create a k8s admin
    k8s_admin = K8SAdmin()

    # if -s run shell
    if len(sys.argv) < 2:
        k8s_admin.shell()
    elif '-s' == sys.argv[1]:
        k8s_admin.shell()
    elif '-a' == sys.argv[1]:
        if len(sys.argv) < 3:
            print('Please tell me what you want')
            exit(1)
        k8s_admin.run(' '.join(sys.argv[2:]))
    elif '-h' == sys.argv[1]:
        app_help()
    else:
        app_help()
