import discord
import os
import google.generativeai as genai
import datetime

# Gemini APIの設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')
chat = model.start_chat(history=[])

# Discordの設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# 許可されたチャンネルIDのリストを環境変数から取得
allowed_channels_str = os.getenv("ALLOWED_CHANNELS", "")
ALLOWED_CHANNELS = [int(ch) for ch in allowed_channels_str.split(",") if ch.isdigit()]

# Botの起動時間を記録
start_time = datetime.datetime.utcnow()

def split_text(text, chunk_size=1500):
    """長いテキストを分割する関数"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

@client.event
async def on_ready():
    print(f'{client.user} がオンラインになったんだよね')
    await client.change_presence(activity=discord.Game(name="ぷりゅ"))
    await tree.sync()  # スラッシュコマンドを同期

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    # 許可されたチャンネル以外では無視
    if message.channel.id not in ALLOWED_CHANNELS:
        return

    # 生成中のメッセージを送信
    reply = await message.channel.send("ぷりゅぷりゅぷりゅぷりゅ・・・")

    # あめしの特徴を反映させる性格のプロンプト
    personality_prompt = (
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
        "ひかげさんの情報：人間の男性、不幸体質だけど明るい性格、雨男、定期的にあめしの家に来て作業をしている。あめしには「ひかげさん」と呼ばれている。"
    )

    # 性格を反映させるためにプロンプトを追加
    full_input = personality_prompt + " " + message.content

    # Gemini AIにメッセージを送信
    response = chat.send_message(full_input)

    # 返答に口癖「ぷりゅ」を追加
    response_with_phrase = response.text + "ぷりゅ"

    # 回答を分割し、最初の部分だけ編集、残りは追加送信
    splitted_text = split_text(response_with_phrase)
    await reply.edit(content=splitted_text[0])  # 最初のメッセージを編集
    for chunk in splitted_text[1:]:
        await message.channel.send(chunk)

@tree.command(name="status", description="Botの現在のステータスを表示")
async def status(interaction: discord.Interaction):
    """Botのステータスを表示するスラッシュコマンド"""
    uptime = datetime.datetime.utcnow() - start_time
    latency = round(client.latency * 1000, 2)  # 秒単位なのでミリ秒に変換

    embed = discord.Embed(title="ステータス", color=discord.Color.green())
    embed.add_field(name="オンライン時間", value=str(uptime).split('.')[0], inline=False)
    embed.add_field(name="応答速度", value=f"{latency} ms", inline=False)

    await interaction.response.send_message(embed=embed)

client.run(os.environ['DISCORD_TOKEN'])