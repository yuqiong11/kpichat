import openai
import requests
import json
import os
# from dotenv import load_dotenv

# load_dotenv()

# api_url = 'https://api.openai.com/v1/edits'
# headers = {'Authorization': 'Bearer ' + API_KEY}
# body = {    
#     "model": "text-davinci-edit-001",
#     "input": "Berlin had 300 chargepoints in July 2022.",
#     "instruction": "Rephrase the text"
#     }

# response = requests.post(api_url, data=json.dumps(body), headers=headers)

# print(response.json())
with open("./backend/.env") as env:
  for line in env:
    key, value = line.strip().split("=")
    os.environ[key] = value

openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.Model.list()

# models = openai.Model.list()
# for model in models["data"]:
#   print(model["id"])

# response = openai.Edit.create(
#   model="text-davinci-edit-001",
#   instruction="Rephrase the text after colon in a way that the meaning should not be changed: Berlin had 300 chargepoints in July 2022."
# )

# print(response)

def rephrase_text(input):

    response =openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Rephrase the text after colon in a way that the meaning should not be changed: {input}"},
        ]
    )

    return response['choices'][0]['message']['content']

# print(response)


def generate_answer(question, info):
   
    response =openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer the question using the following information. Please don't mention the word information or data in your reply. The information that is given to you always corresponds to the time the question asks."},
            {"role": "user", "content": f"Question: {question}   Information: {info}"},
        ]
    )

    return response['choices'][0]['message']['content']

# print(generate_answer((['Belrin', 1000])))