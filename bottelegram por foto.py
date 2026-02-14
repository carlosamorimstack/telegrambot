import os
import json
import logging
import urllib.parse
import io
from PIL import Image
import imagehash
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# --- CONFIGURAÇÕES ---
# No Hugging Face, você colocará o token nas "Variables" para segurança
TOKEN = os.getenv("TELEGRAM_TOKEN")
MEU_ID = 8542481045  

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Banco de dados em memória para evitar OSError no servidor
if 'db_memoria' not in globals():
    db_memoria = {}

# --- FUNÇÕES DE APOIO ---
def carregar_db():
    return db_memoria

def salvar_db(db):
    global db_memoria
    db_memoria = db

def gerar_hash_da_foto(foto_bytes):
    try:
        img = Image.open(io.BytesIO(foto_bytes))
        return imagehash.phash(img)
    except:
        return None

def encontrar_similar(novo_hash, db, limite=5):
    if not db: return None
    for hash_str in db:
        hash_banco = imagehash.hex_to_hash(hash_str)
        if (novo_hash - hash_banco) <= limite: return hash_str
    return None

def criar_botoes_investigacao(url_foto):
    foto_enc = urllib.parse.quote_plus(url_foto)
    yandex_link = f"https://yandex.com/images/search?rpt=imageview&url={foto_enc}"
    google_link = f"https://lens.google.com/uploadbyurl?url={foto_enc}"
    
    keyboard = [
        [InlineKeyboardButton("🔗 ENCONTRAR PERFIL (Yandex)", url=yandex_link)],
        [InlineKeyboardButton("🔎 VERIFICAR NO GOOGLE", url=google_link)]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLER PRINCIPAL ---
async def analisar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MEU_ID: return
    
    msg_status = await update.message.reply_text("🕵️ **Buscando perfis vinculados...**", parse_mode="Markdown")

    try:
        # Pegamos a foto e baixamos para a MEMÓRIA (sem salvar arquivo no disco)
        foto = update.message.photo[-1]
        arquivo = await foto.get_file()
        foto_bytes = await arquivo.download_as_bytearray()
        
        # Link que o Telegram já gera para nós
        url_publica = arquivo.file_path 

        hash_atual = gerar_hash_da_foto(foto_bytes)
        db = carregar_db()
        hash_str = str(hash_atual)
        hash_existente = encontrar_similar(hash_atual, db)

        if hash_existente:
            db[hash_existente]["contagem"] += 1
            status_txt = f"⚠️ **FOTO REPETIDA!**\nDetectada **{db[hash_existente]['contagem']}** vezes."
        else:
            db[hash_str] = {"contagem": 1}
            status_txt = "✅ **FOTO NOVA**\nNenhum rastro anterior."

        salvar_db(db)
        
        await msg_status.delete()
        await update.message.reply_text(
            f"{status_txt}\n\n**Resultados encontrados:**",
            reply_markup=criar_botoes_investigacao(url_publica),
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Erro: {e}")
        await update.message.reply_text("❌ Erro ao processar. O link da foto pode ter expirado.")

if __name__ == "__main__":
    if not TOKEN:
        print("ERRO: TELEGRAM_TOKEN não configurado!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.PHOTO, analisar_foto))
        print("🚀 Bot Iniciado na Nuvem!")
        app.run_polling()