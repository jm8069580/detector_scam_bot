import logging
import os
import psycopg
from datetime import datetime
from flask import Flask, jsonify
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# BASE DE DATOS PostgreSQL
# ==========================================

def get_conn():
    """
    Retorna una conexión a PostgreSQL.
    Render provee la variable DATABASE_URL automáticamente
    cuando enlazas la base de datos al servicio.
    """
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("❌ No se encontró DATABASE_URL")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return psycopg.connect(DATABASE_URL)

def init_db():
    """Crea la tabla detecciones si no existe."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS detecciones (
                    id          SERIAL PRIMARY KEY,
                    fecha       TIMESTAMP NOT NULL DEFAULT NOW(),
                    usuario     TEXT,
                    user_id     BIGINT,
                    chat_id     BIGINT,
                    chat_nombre TEXT,
                    tipo_alerta TEXT,
                    mensaje     TEXT
                )
            """)
            # Índices útiles para consultas frecuentes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_detecciones_usuario
                ON detecciones (usuario)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_detecciones_fecha
                ON detecciones (fecha DESC)
            """)
        conn.commit()
        print("✅ Tabla 'detecciones' lista en PostgreSQL.")
    finally:
        conn.close()

def registrar_deteccion(usuario, user_id, chat_id, chat_nombre, tipo_alerta, mensaje):
    """Inserta un nuevo registro en la base de datos."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO detecciones
                    (usuario, user_id, chat_id, chat_nombre, tipo_alerta, mensaje)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                usuario,
                user_id,
                chat_id,
                chat_nombre,
                tipo_alerta,
                mensaje[:500]
            ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"[DB] Error al registrar: {e}")
    finally:
        conn.close()

def obtener_detecciones(limite=50):
    """Devuelve las últimas N detecciones como lista de dicts."""
    conn = get_conn()
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("""
                SELECT id, fecha, usuario, user_id, chat_id, chat_nombre, tipo_alerta, mensaje
                FROM detecciones
                ORDER BY fecha DESC
                LIMIT %s
            """, (limite,))
            rows = cur.fetchall()
            # Convertir fecha a string para JSON
            result = []
            for row in rows:
                r = dict(row)
                r["fecha"] = r["fecha"].strftime("%Y-%m-%d %H:%M:%S") if r["fecha"] else None
                result.append(r)
            return result
    finally:
        conn.close()

def obtener_estadisticas():
    """Devuelve totales agrupados por tipo de alerta."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT tipo_alerta, COUNT(*) AS total
                FROM detecciones
                GROUP BY tipo_alerta
                ORDER BY total DESC
            """)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def obtener_usuarios_frecuentes(limite=10):
    """Devuelve los usuarios con más detecciones."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT usuario, COUNT(*) AS total
                FROM detecciones
                GROUP BY usuario
                ORDER BY total DESC
                LIMIT %s
            """, (limite,))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# ==========================================
# SERVIDOR WEB FLASK
# ==========================================

server = Flask('')

@server.route('/')
def home():
    return "🛡️ Bot Detector is running!"

@server.route('/detecciones')
def ver_detecciones():
    """Últimas 50 detecciones en JSON."""
    try:
        datos = obtener_detecciones(50)
        return jsonify({"total": len(datos), "detecciones": datos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/estadisticas')
def ver_estadisticas():
    """Totales por tipo de alerta + usuarios más frecuentes."""
    try:
        stats = obtener_estadisticas()
        top_usuarios = obtener_usuarios_frecuentes(10)
        total_general = sum(s["total"] for s in stats)
        return jsonify({
            "total_general": total_general,
            "por_tipo": stats,
            "top_usuarios": top_usuarios
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run():
    port = int(os.environ.get('PORT', 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ==========================================
# LÓGICA DEL BOT DE TELEGRAM
# ==========================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ALERTAS_KEYWORDS = [
    "verifica tu cuenta", "has ganado", "premio", "soporte",
    "recuperar cuenta", "wallet", "crypto", "binance",
    "envía dinero", "apk", "descarga ahora", "inicia sesión"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ *Bot Detector activado!*\n"
        "Estoy vigilando este chat en busca de enlaces sospechosos y estafas conocidas.\n\n"
        "📊 Usa `/registros` para ver las últimas detecciones.",
        parse_mode="Markdown"
    )

async def registros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /registros — muestra las últimas 5 detecciones en el chat."""
    try:
        datos = obtener_detecciones(5)
        stats = obtener_estadisticas()
    except Exception as e:
        await update.message.reply_text(f"❌ Error al consultar la base de datos: {e}")
        return

    if not datos:
        await update.message.reply_text("📭 No hay detecciones registradas aún.")
        return

    total = sum(s["total"] for s in stats)
    texto = f"📊 *Últimas detecciones* (total acumulado: {total})\n\n"

    for d in datos:
        msg_preview = d['mensaje'][:80] + "..." if len(d['mensaje']) > 80 else d['mensaje']
        texto += (
            f"🗓 `{d['fecha']}`\n"
            f"👤 @{d['usuario']} — `{d['tipo_alerta']}`\n"
            f"💬 _{msg_preview}_\n"
            f"──────────────\n"
        )

    await update.message.reply_text(texto, parse_mode="Markdown")

async def detector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.from_user.is_bot:
        return

    texto = update.message.text.lower()
    texto_original = update.message.text
    usuario = update.message.from_user.username or update.message.from_user.first_name
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_nombre = update.message.chat.title or update.message.chat.username or str(chat_id)

    tipo_alerta = None

    # 1. Detección por palabras clave
    if any(palabra in texto for palabra in ALERTAS_KEYWORDS):
        tipo_alerta = "keywords_sospechosas"
        await update.message.reply_text(
            f"⚠️ *ALERTA DE SCAM*\n"
            f"Usuario: @{usuario}\n"
            f"El mensaje contiene frases sospechosas.",
            parse_mode="Markdown"
        )

    # 2. Detección de enlaces
    elif "http" in texto or "t.me/" in texto:
        tipo_alerta = "link_sospechoso"
        await update.message.reply_text(
            f"🔗 *Link sospechoso* detectado de @{usuario}.\n"
            f"¡No abras enlaces desconocidos!",
            parse_mode="Markdown"
        )

    # Guardar en PostgreSQL si hubo detección
    if tipo_alerta:
        registrar_deteccion(
            usuario=usuario,
            user_id=user_id,
            chat_id=chat_id,
            chat_nombre=chat_nombre,
            tipo_alerta=tipo_alerta,
            mensaje=texto_original
        )
        logging.info(f"[DB] Registrado: {tipo_alerta} | @{usuario} | chat: {chat_nombre}")

def main():
    TOKEN = os.environ.get('TELEGRAM_TOKEN')

    if not TOKEN:
        print("❌ ERROR: No se encontró la variable TELEGRAM_TOKEN")
        return

    # Inicializar base de datos (crea tabla si no existe)
    init_db()

    # Iniciar servidor Flask
    keep_alive()

    # Configurar bot
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registros", registros))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detector))

    print("🤖 Bot iniciado y servidor web escuchando...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()