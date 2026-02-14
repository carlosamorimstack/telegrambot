import os
import json
import logging
import urllib.parse
import io
from datetime import datetime
from PIL import Image
import imagehash
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
MEU_ID = 8542481045
DB_FILE = "db.json"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ---------- BANCO ----------
def carregar_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

# ---------- HASH ----------
def gerar_hash_da_foto(foto_bytes):
    try:
        img = Image.open(io.BytesIO(foto_bytes))
        return imagehash.phash(img)
    except:
        return None

def encontrar_similar(novo_hash, db, limite=5):
    for hash_str in db:
        hash_banco = imagehash.hex_to_hash(hash_str)
        if (novo_hash - hash_banco) <= limite:
            return hash_str
    return None

# ---------- BOTÕES ----------
def criar_botoes_investigacao(url_foto):
    foto_enc = urllib.parse.quote_plus(url_foto)

    yandex_link = f"https://yandex.com/images/search?rpt=imageview&url={foto_enc}"
    google_link = f"https://lens.google.com/uploadbyurl?url={foto_enc}"

    keyboard = [
        [InlineKeyboardButton("🔗 PERFIL (Yandex)", url=yandex_link)],
        [InlineKeyboardButton("🔎 GOOGLE LENS", url=google_link)]
    ]

    return InlineKeyboardMarkup(keyboard)

# ---------- HISTÓRICO ----------
async def historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MEU_ID:
        return

    db = carregar_db()

    if not db:
        await update.message.reply_text("Sem histórico ainda.")
        return

    texto = "📊 Histórico:\n\n"

    for h, dados in list(db.items())[-10:]:
        texto += f"Foto: {dados['contagem']} vezes\n"
        texto += f"Última vez: {dados['data']}\n\n"

    await update.message.reply_text(texto)

# ---------- FOTO ----------
async def analisar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MEU_ID:
        return

    msg_status = await update.message.reply_text("🔍 Buscando...")

    try:
        foto = update.message.photo[-1]
        arquivo = await foto.get_file()
        foto_bytes = await arquivo.download_as_bytearray()
        url_publica = arquivo.file_path

        hash_atual = gerar_hash_da_foto(foto_bytes)
        db = carregar_db()

        hash_str = str(hash_atual)
        hash_existente = encontrar_similar(hash_atual, db)

        agora = datetime.now().strftime("%d/%m %H:%M")

        if hash_existente:
            db[hash_existente]["contagem"] += 1
            db[hash_existente]["data"] = agora
            status_txt = f"⚠️ FOTO REPETIDA\nDetectada {db[hash_existente]['contagem']} vezes."
        else:
            db[hash_str] = {
                "contagem": 1,
                "data": agora
            }
            status_txt = "✅ FOTO NOVA"

        salvar_db(db)

        await msg_status.delete()

        await update.message.reply_text(
            f"{status_txt}\n\nResultados:",
            reply_markup=criar_botoes_investigacao(url_publica)
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Erro ao processar imagem.")

# ---------- MAIN ----------
if __name__ == "__main__":
    if not TOKEN:
        print("Configure TELEGRAM_TOKEN!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()

        app.add_handler(MessageHandler(filters.PHOTO, analisar_foto))
        app.add_handler(CommandHandler("historico", historico))

        print("🚀 Bot rodando...")
        app.run_polling()
