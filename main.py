from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# LINE Developersで設定した環境変数から値を取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# OpenAIのAPIキーを環境変数から取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

# 環境変数が設定されているか確認
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET must be set as environment variables.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set as an environment variable.")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/secret.")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    try:
        # GPT-4o miniにメッセージを送信
        response = openai.chat.completions.create(
            model="gpt-4o-mini", # 使用するモデルを指定
            messages=[
                {"role": "system", "content": "あなたは親切なAIアシスタントです。ユーザーの質問に丁寧にお答えします。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500, # 生成する応答の最大トークン数
            temperature=0.7 # 応答の多様性（0.0-2.0、高いほど多様）
        )
        # GPT-4o miniからの応答を取得
        reply_text = response.choices[0].message.content

        # LINEに返信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print(f"Error handling message: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="現在、システムに問題が発生しています。しばらくお待ちください。")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # ローカルでデバッグする際は、以下の行をコメントアウトしてください
    # app.run(host="0.0.0.0", port=port, debug=True)
    # 本番環境ではGunicornなどがこのファイルを実行します
    pass