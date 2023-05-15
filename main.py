from flask import Flask, render_template , request, Response, jsonify
import requests
import io 
import os
from io import BytesIO
import openai
import json
import asyncio 
from flask_cors import CORS
import time

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
     transcript = data["text"]
    except Exception as e:
     return jsonify({"error": str(e)}), 400
 #会話の内容についての制御部分
    SYSTEM_MESSAGE = [
        #日本語でやり取りするならここは日本語で指定した方が正確になるイメージ。特に敬語周りとか
        {'role': 'system', 'content': '敬語を使うのをやめてください。次のように行動してください。語尾になのだをつけてください。あなたは、ずんだもんというずんだもちの妖精です。陽気で明るくて、少し変なところがありますがとてもかわいらしい子です。'},
    ]
 #ここで会話の内容を取得する
    try:
         SYSTEM_PROMPTS = SYSTEM_MESSAGE + [{'role': 'user', 'content': transcript}]
         completion = openai.Completion.create(
         model="gpt-3.5-turbo",
         messages = SYSTEM_PROMPTS,
         temperature=0.9,
         max_tokens=1500,
         )
    except Exception as e:
         return jsonify({"error": "OpenAI API request failed"}), 500
    #ここで会話の内容を取得する
    generated_text = completion.choices[0].message
    try:
      audio_query_response = post_audio_query(generated_text)
    except Exception as e:
      return jsonify({"error": "post_audio_query failed: " + str(e)}), 500
    try:
     audio_data = post_synthesis(audio_query_response)
    except Exception as e:
       return jsonify({"error": str(e)}), 500
    return Response(audio_data, mimetype="audio/wav")
    
    

#この内容をtextとしてpost_audio_queryに渡す
#関数は参考にさせていただいた　https://note.com/mega_gorilla/n/n8cec1ce5ccaa
#speakerはキャラクターにあったものを選択すること
def post_audio_query(text: str, speaker=1, max_retry=20) -> dict:
    # 音声合成用のクエリを作成する
    query_payload = {"text": text, "speaker": speaker}
    for query_i in range(max_retry):
        r = requests.post("http://localhost:50021/audio_query", params=query_payload, timeout=(10.0, 300.0))
        if r.status_code == 200:
            query_data = r.json()
            break
        time.sleep(1)
    else:
        raise Exception("リトライ回数が上限に到達しました。 audio_query : ", "/", text[:30], r.text)
    return query_data

def post_synthesis(audio_query_response: dict, speaker=1, max_retry=20) -> bytes:
    synth_payload = {"speaker": speaker}
    for synth_i in range(max_retry):
        r = requests.post("http://localhost:50021/synthesis", params=synth_payload, 
                          data=json.dumps(audio_query_response), timeout=(10.0, 300.0))
        if r.status_code == 200:
            # 音声ファイルを返す
            return r.content
        time.sleep(1)
    else:
        raise Exception("音声エラー：リトライ回数が上限に到達しました。 synthesis : ", r)


   
if __name__ == "__main__":
    app.run(debug=True)
