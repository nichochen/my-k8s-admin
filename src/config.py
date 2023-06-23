
import os

text_banner=''' _  _____ ____       _    ____  __  __ 
| |/ ( _ ) ___|     / \  |  _ \|  \/  |
| ' // _ \___ \    / _ \ | | | | |\/| |
| . \ (_) |__) |  / ___ \| |_| | |  | |
|_|\_\___/____/  /_/   \_\____/|_|  |_|
'''
version='alpha 0.0.1'

#----Google Cloud LLM Config----
gcp_project='<your gcp project>'
gcp_region='us-central1'
gcp_service_account_key='/opt/sa.key'

#----Do not change below settings----
gcp_text_llm='text-bison@001'
gcp_chat_llm='chat-bison@001'
gcp_code_llm='code-bison@001'
