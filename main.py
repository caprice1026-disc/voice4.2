from flask import Flask, render_template , request, Response, jsonify
import requests
import io 
import os
from io import BytesIO
import openai
import json
import asyncio 
from flask_cors import CORS


#余計なライブラリは後で削ること
#環境変数は後で書きなおすこと
openai.api_key = ""

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_text", methods=["POST"])
def process_text():
    try:
     data = request.get_json()
     transcript = data['text']
    except Exception as e:
     return jsonify({"error": str(e)}), 400
 #会話の内容についての制御部分
    SYSTEM_MESSAGE = [
        #日本語でやり取りするならここは日本語で指定した方が正確になるイメージ。特に敬語周りとか
        {'role': 'system', 'content': '敬語を使うのをやめてください。次のように行動してください。語尾になのだをつけてください。あなたは、ずんだもんというずんだもちの妖精です。陽気で明るくて、少し変なところがありますがとてもかわいらしい子です。'},
    ]
 #ここで会話の内容を取得する
    exit_flag = False
    while not exit_flag:
        try:
         SYSTEM_PROMPTS = SYSTEM_MESSAGE + [{'role': 'user', 'content': transcript}]
         response = openai.Completion.create(
         engine="gpt-3.5-turbo",
         messages = SYSTEM_PROMPTS,
         temperature=0.9,
         max_tokens=1500,
         )
        except Exception as e:
         return jsonify({"error": "OpenAI API request failed"}), 500
    #ここで会話の内容を取得する
    generated_text = response.choices[0].text.strip()
    try:
      audio_query_response = post_audio_query(generated_text)
      audio_data = post_synthesis(audio_query_response)
    except Exception as e:
     return jsonify({"error": "External API request failed"}), 500
    return audio_data

    
    

#この内容をtextとしてpost_audio_queryに渡す

def post_audio_query(generated_text: str) -> dict:
    params = {'text': generated_text , 'speaker': 1}
    res = requests.post('http://localhost:50021/audio_query', params=params)
    return res.json()

def post_synthesis(audio_query_response: dict) -> bytes:
   params = {'speaker': 1}
   headers = {'content-type': 'application/json'}
   audio_query_response_json = json.dumps(audio_query_response)
   res = requests.post(
        'http://localhost:50021/synthesis',
        data=audio_query_response_json,
        params=params,
        headers=headers
    )
   return Response(res.content, mimetype='audio/wav')

   
if __name__ == "__main__":
    app.run(debug=True)
