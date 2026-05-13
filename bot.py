import logging
import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# CONFIGURACIÓN DE SERVER WEB (PARA RENDER)
# ==========================================
server = Flask('')

@server.route('/')
def home():
    return "🛡️ Bot Detector is running!"

def run():
    # Render asigna un puerto automáticamente en la variable de entorno PORT
    port = int(os.environ.get('PORT', 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ==========================================
# LÓGICA DEL BOT DE TELEGRAM
# ==========================================

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ **Bot Detector activado!**\n"
        "Estoy vigilando este chat en busca de enlaces sospechosos y estafas conocidas."
    )

async def detector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignorar mensajes vacíos o de otros bots
    if not update.message or not update.message.text or update.message.from_user.is_bot:
        return
        
    texto = update.message.text.lower()
    usuario = update.message.from_user.username or update.message.from_user.first_name

    # Lista de palabras clave sospechosas
    alertas = [
        "verifica tu cuenta", "has ganado", "premio", "soporte", 
        "recuperar cuenta", "wallet", "crypto", "binance", 
        "envía dinero", "apk", "descarga ahora", "inicia sesión"
    ]

    # 1. Detección por palabras clave
    if any(palabra in texto for palabra in alertas):
        await update.message.reply_text(f"⚠️ **ALERTA DE SCAM**\nUsuario: @{usuario}\nEl mensaje contiene frases sospechosas.")

    # 2. Detección de enlaces (links)
    elif "http" in texto or "t.me/" in texto:
        await update.message.reply_text(f"🔗 **Link sospechoso** detectado de @{usuario}. ¡No abras enlaces desconocidos!")

def main():
    # Se recomienda configurar el token en Render como Variable de Entorno
    TOKEN = os.environ.get('TELEGRAM_TOKEN')
    
    if not TOKEN:
        print("❌ ERROR: No se encontró la variable TELEGRAM_TOKEN")
        return

    # Iniciar el servidor web de Flask en un hilo separado
    keep_alive()

    # Configurar el bot
    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detector))

    print("🤖 Bot iniciado y servidor web escuchando...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()