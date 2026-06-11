# 🛡️ Bot Detector de Scams para Telegram
 
Un bot de seguridad diseñado para detectar frases comunes de estafas, intentos de phishing y enlaces sospechosos en grupos o chats privados de Telegram. Registra cada detección en una base de datos PostgreSQL y corre 24/7 en **Render.com**.
 
---
 
## 🚀 Características
 
- **Detección de palabras clave:** Identifica frases como "has ganado un premio", "verifica tu cuenta", "wallet", "crypto", entre otras.
- **Filtro de enlaces:** Detecta URLs externas y links de Telegram (`t.me`) para prevenir phishing.
- **Base de datos PostgreSQL:** Registra cada detección con usuario, mensaje, tipo de alerta, chat y fecha.
- **Endpoints REST:** Consulta las detecciones y estadísticas desde el navegador.
- **Comando `/registros`:** Muestra las últimas detecciones directamente en Telegram.
- **Servidor web Flask:** Mantiene el servicio activo en el plan gratuito de Render.
- **Seguridad:** Token y credenciales de base de datos configurados como variables de entorno.
---
 
## 🛠️ Instalación y configuración
 
### 1. Clonar el repositorio
 
```bash
git clone https://github.com/tu-usuario/nombre-de-tu-repo.git
cd nombre-de-tu-repo
```
 
### 2. Instalar dependencias
 
```bash
pip install -r requirements.txt
```
 
`requirements.txt`:
```
python-telegram-bot
flask
psycopg2-binary
```
 
### 3. Variables de entorno
 
| Variable | Descripción |
|---|---|
| `TELEGRAM_TOKEN` | Token del bot obtenido desde [@BotFather](https://t.me/BotFather) |
| `DATABASE_URL` | URL de conexión a PostgreSQL (interna de Render) |
 
---
 
## ☁️ Deploy en Render.com
 
### Requisitos
- Python **3.12** (definido en `.python-version`)
- PostgreSQL en Render (plan Free)
### Pasos
 
1. Crear un nuevo **Web Service** conectado a este repositorio.
2. Crear una nueva **PostgreSQL** database en Render.
3. En el Web Service → **Environment** → agregar las variables `TELEGRAM_TOKEN` y `DATABASE_URL` (Internal URL de la base de datos).
4. Render ejecuta automáticamente `pip install -r requirements.txt` y luego `python bot.py`.
5. Al iniciar, el bot crea la tabla `detecciones` si no existe.
---
 
## 📊 Endpoints disponibles
 
| Ruta | Descripción |
|---|---|
| `/` | Estado del servicio |
| `/detecciones` | Últimas 50 detecciones en JSON |
| `/estadisticas` | Totales por tipo de alerta y top usuarios |
 
---
 
## 💬 Comandos del bot
 
| Comando | Descripción |
|---|---|
| `/start` | Activa el bot y muestra información |
| `/registros` | Muestra las últimas 5 detecciones en el chat |
 
---
 
## 🗄️ Estructura de la base de datos
 
Tabla `detecciones`:
 
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL | ID autoincremental |
| `fecha` | TIMESTAMP | Fecha y hora de la detección |
| `usuario` | TEXT | Username o nombre del usuario |
| `user_id` | BIGINT | ID numérico de Telegram |
| `chat_id` | BIGINT | ID del chat donde ocurrió |
| `chat_nombre` | TEXT | Nombre del grupo o chat |
| `tipo_alerta` | TEXT | `keywords_sospechosas` o `link_sospechoso` |
| `mensaje` | TEXT | Contenido del mensaje (máx. 500 caracteres) |