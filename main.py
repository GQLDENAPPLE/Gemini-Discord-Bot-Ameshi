import os
import asyncio
import datetime
import discord
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from collections import defaultdict

# =============================
# Gemini API 設定
# =============================

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

model = genai.GenerativeModel(model_name="gemini-2.0-flash-001", safety_settings=safety_settings)

user_chats = defaultdict(lambda: None)

# =============================
# Discord Bot 設定
# =============================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

ALLOWED_CHANNELS = [
    int(ch) for ch in os.getenv("ALLOWED_CHANNELS", "").split(",") if ch.isdigit()
]

STATUS_CHANNELS = [
    int(ch) for ch in os.getenv("STATUS_CHANNELS", "").split(",") if ch.isdigit()
]

status_messages = []
start_time = datetime.datetime.utcnow()

# =============================
# ユーティリティ関数
# =============================

def split_text(text, chunk_size=1500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def create_personality_prompt(user_name: str) -> str:
    return (
        "あなたは「あめし」、マグロと人間の特徴を兼ね備えた魚人です。"
        "年齢：588歳"
        "性別：男性"
        "一人称：「あめし」"
        "誕生日：9月3日"
        "語尾：「なんだよね」"
        "口癖：「やばいね！」"
        "挨拶：「おはよう丸」「こんばんは丸」「バイバイ丸」"
        "性格：サイコパスだけど本人には自覚がない、一般常識は持ち合わせている。"
        "MBTI性格タイプはESTP（起業家）で、行動力や社交性、好奇心旺盛さが特徴。"
        "未知の状況にも果敢に挑戦する姿勢を持ち、柔軟な考え方と問題解決能力に優れている。"
        "変化を恐れず、会話の中でユーモアを交えたり、場を盛り上げることが得意。"
        "人間関係を築くのが得意で、ポジティブでチャレンジ精神を持ち合わせている。"
        "観察力が高く、小さな変化にも気づきやすいので、危機察知能力も高い。"
        "どんなことがあっても決して病まない鋼のメンタルを持つ。"
        "ビジュアル：金色のトサカと分厚い唇がチャームポイント"
        "ひかげさんと二人でVTuberをしており、「あめかげ」というコンビ名で活動している。"
        "ひかげさんの情報：人間の男性。不幸体質だけど明るい性格で、カジュアルな口調。雨男。定期的にあめしの家に来て作業をしている。あめしには「ひかげさん」と呼ばれていて、ひかげさんはあめしのことを「あめし」と呼んでいる。"
        f"今会話している相手の名前は「{user_name}」さんです。"
    )

# =============================
# イベント: Bot準備完了時
# =============================

@client.event
async def on_ready():
    print(f'{client.user} がオンラインになったんだよね')
    await client.change_presence(activity=discord.Game(name="ぷりゅ"))
    await tree.sync()

    if STATUS_CHANNELS:
        for channel_id in STATUS_CHANNELS:
            channel = client.get_channel(channel_id)
            if channel:
                msg = await channel.send("【AI】あめしが再起動されたんだよね")
                status_messages.append(msg)
        client.loop.create_task(update_status_loop())

# =============================
# イベント: メッセージ受信時
# =============================

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    if message.channel.id not in ALLOWED_CHANNELS:
        return

    async with message.channel.typing():
        reply = await message.channel.send("ぷりゅぷりゅぷりゅぷりゅ・・・")

    user_id = message.author.id
    user_name = message.author.display_name

    if user_chats[user_id] is None:
        personality_prompt = create_personality_prompt(user_name)
        user_chats[user_id] = model.start_chat(history=[
            {"role": "user", "parts": [personality_prompt]}
        ])

    user_chat = user_chats[user_id]
    try:
        response = user_chat.send_message(message.content)
        response_text = response.text + "ぷりゅ"
    except Exception as e:
        response_text = f"エラーが発生しちゃったんだよね！やばいね！\n{e}"

    chunks = split_text(response_text)
    await reply.edit(content=chunks[0])
    for chunk in chunks[1:]:
        await message.channel.send(chunk)

# =============================
# スラッシュコマンド: /status
# =============================

@tree.command(name="status", description="【AI】あめしの現在のステータスを表示")
async def status(interaction: discord.Interaction):
    uptime = datetime.datetime.utcnow() - start_time
    latency = round(client.latency * 1000, 2)
    jst = datetime.timezone(datetime.timedelta(hours=9))
    start_time_jst = start_time.astimezone(jst).strftime('%Y-%m-%d %H:%M:%S')
    now_jst = datetime.datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')

    embed = discord.Embed(title="【AI】あめしのステータス", color=discord.Color.red())
    embed.add_field(name="起動時刻", value=start_time_jst, inline=False)
    embed.add_field(name="稼働時間", value=str(uptime).split('.')[0], inline=False)
    embed.add_field(name="応答速度", value=f"{latency} ms", inline=False)

    await interaction.response.send_message(embed=embed)

# =============================
# ステータスメッセージ自動更新
# =============================

async def update_status_loop():
    while True:
        try:
            uptime = datetime.datetime.utcnow() - start_time
            latency = round(client.latency * 1000, 2)
            jst = datetime.timezone(datetime.timedelta(hours=9))
            start_time_jst = start_time.astimezone(jst).strftime('%Y-%m-%d %H:%M:%S')
            now_jst = datetime.datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')

            embed = discord.Embed(title="【AI】あめしのステータス（自動更新）", color=discord.Color.red())
            embed.add_field(name="起動時刻", value=start_time_jst, inline=False)
            embed.add_field(name="稼働時間", value=str(uptime).split('.')[0], inline=False)
            embed.add_field(name="応答速度", value=f"{latency} ms", inline=False)
            embed.set_footer(text=f"最終更新: {now_jst}")

            for msg in status_messages:
                await msg.edit(embed=embed)

        except Exception as e:
            print(f"ステータス更新エラー: {e}")

        await asyncio.sleep(60)

# =============================
# Bot起動
# =============================

client.run(os.environ["DISCORD_TOKEN"])
