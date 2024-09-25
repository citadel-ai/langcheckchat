import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


class RAG:

    def __init__(self):
        # Initialize LLM and embedding model depending on the API type
        self.llm = AzureOpenAI(  # type: ignore
            api_key=os.environ['AZURE_OPENAI_KEY'],
            azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
            api_version=os.environ['OPENAI_API_VERSION'],
        )

    def query(self, user_message, system_prompt):
        '''Given a query, retrieve relevant sources and generates a response
        using the sources as context.
        '''
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        response = self.llm.chat.completions.create(
            model=os.environ['AZURE_OPENAI_API_MODEL'],
            messages=messages,  # type: ignore
            temperature=0.0
        )

        response_text = response.choices[0].message.content

        return response_text
