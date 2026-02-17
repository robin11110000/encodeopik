import os
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
import json
from pathlib import Path
from dotenv import load_dotenv
from src.service.summary_service.summarizer_prompt import *



class Summarizer:

    def __init__(self, model_name="amazon.nova-pro-v1:0"):
        load_dotenv()
        access_key = os.getenv("AWS_ACCESS_KEY")
        secret_key  = os.getenv("AWS_SECRET_KEY")
        self.llm = ChatBedrock(model=model_name,
                               region="us-east-1",   
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key)
    
    def load_json(self, file_path):
        '''
        input: json file path
        output: text
        Reads a JSON file and returns a pretty string for model input. 
        '''

        with open(Path(file_path), "r") as f:
            json_text = json.load(f)
        return json.dumps(json_text, indent=2)
    
    def summarize_json(self, file_path, system_prompt, human_prompt):
        ''' 
        input: json_file: file where the information has been extracted in json format
        llm: LLM instance
        summarizer_prompt: For what do we need to summarize the file. 
            Options: 
            {(BANK_STATEMENT_SUMMARIZER_SYSTEM_PROMPT, BANK_STATEMENT_SUMMARIZER_HUMAN_PROMPT),
            (CREDIT_REPORT_SUMMARIZER_SYSTEM_PROMPT, CREDIT_REPORT_SUMMARIZER_HUMAN_PROMPT),
            (IDENTITY_REPORT_SUMMARIZER_SYSTEM_PROMPT, IDENTITY_REPORT_SUMMARIZER_HUMAN_PROMPT),
            (INCOME_PROOF_REPORT_SUMMARIZER_SYSTEM_PROMPT, INCOME_PROOF_REPORT_SUMMARIZER_HUMAN_PROMPT),
            (TAX_STATEMENT_REPORT_SUMMARIZER_SYSTEM_PROMPT, TAX_STATEMENT_REPORT_SUMMARIZER_HUMAN_PROMPT),
            (UTILITY_BILLS_REPORT_SUMMARIZER_SYSTEM_PROMPT, UTILITY_BILL_REPORT_SUMMARIZER_HUMAN_PROMPT)
            }
        '''
        #load json file
        json_text = self.load_json(file_path)
        # Create message templates
        # System role: define assistant behavior
        system_template = SystemMessagePromptTemplate.from_template(system_prompt)

        # Human message: provide data
        human_template = HumanMessagePromptTemplate.from_template(human_prompt)
        

        chat_prompt = ChatPromptTemplate.from_messages([system_template, human_template])
        formatted_messages = chat_prompt.format_messages(json_text=json_text)
        response = self.llm.invoke(formatted_messages)
        print(response.content)
        return response.content
    
    def save_summary(self, file_path, system_prompt, human_prompt, output_path,document_type):
         sumamry = self.summarize_json(file_path, system_prompt, human_prompt)
         save_path = f"{output_path}/{document_type}_summary.txt"
         with open(save_path, "w") as f:
             f.write(sumamry)


             