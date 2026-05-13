# 🛡️ Bot Detector de Scams para Telegram

Un bot de seguridad diseñado para detectar frases comunes de estafas, intentos de phishing y enlaces sospechosos en grupos o chats privados de Telegram. Optimizado para correr 24/7 en plataformas como **Render.com**.

## 🚀 Características
* **Detección de Palabras Clave:** Identifica frases como "has ganado un premio", "verifica tu cuenta", entre otras.
* **Filtro de Enlaces:** Detecta links de Telegram (`t.me`) y URLs externas para prevenir phishing.
* **Servidor Web Integrado:** Incluye un micro-servidor Flask para evitar que el servicio gratuito de Render se detenga.
* **Seguridad:** Configurado para usar variables de entorno para proteger el Token del bot.

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone [https://github.com/tu-usuario/nombre-de-tu-repo.git](https://github.com/tu-usuario/nombre-de-tu-repo.git)
cd nombre-de-tu-repo