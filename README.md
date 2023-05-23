# 🤖 BotiBotDiscord - Gestión de Promociones en Discord

![BotiBotDiscord](![image](https://github.com/CositortoL/BotiBotDiscord/assets/134352245/d93f7540-7332-4bdb-a068-fb0b831d9662))

Este bot de Discord está diseñado para gestionar promociones en un servidor. Permite a los usuarios añadir, editar, eliminar y visualizar promociones. También verifica las promociones vencidas y envía notificaciones al servidor. El bot utiliza Google Sheets como base de datos para almacenar las promociones y MongoDB para réplica y respaldo.

## 📚 Índice

- [Instalación](#instalación)
- [Uso](#uso)
- [Contribución](#contribución)
- [Licencia](#licencia)

## 💻 Instalación

1. Clona el repositorio:
    ```
    git clone https://github.com/CositortoL/BotiBotDiscord.git
    ```
2. Instala las dependencias requeridas:
    ```
    pip install -r requirements.txt
    ```
3. Crea un archivo `.env` en el directorio raíz del proyecto y añade las siguientes variables de entorno:
    ```
    DISCORD_TOKEN=tu-token-de-discord
    GOOGLE_SHEETS_API_KEY=tu-clave-api-de-google-sheets
    MONGODB_CONNECTION_STRING=tu-cadena-de-conexión-de-mongodb
    ```
4. Ejecuta el bot:
    ```
    python bot.py
    ```

## 🎮 Uso

El bot soporta los siguientes comandos:

- `/promocion`: Inicia un diálogo con el usuario para añadir una nueva promoción. El usuario debe tener habilitada la opción de recibir mensajes directos de los miembros del servidor.

- `/ver_promociones`: Muestra todas las promociones actuales en el servidor.

- `/eliminar_promocion <UUID>`: Elimina una promoción con el UUID especificado. Este comando sólo puede ser utilizado por usuarios con los roles 'ADMIN', 'TETON LEGENDARIO' o 'TETON GRAN MAESTRO'.

- `/ver_logs`: Muestra todos los registros de logs. Este comando sólo puede ser utilizado por usuarios con los roles 'ADMIN', 'TETON LEGENDARIO' o 'TETON GRAN MAESTRO'.

- `/editar_registro <UUID>`: Inicia un diálogo con el usuario para editar una promoción con el UUID especificado. Este comando sólo puede ser utilizado por usuarios con los roles 'ADMIN', 'TETON LEGENDARIO' o 'TETON GRAN MAESTRO'.

- `/replica`: Comprueba las diferencias entre la base de datos de Google Sheets y la base de datos de MongoDB y actualiza la base de datos de MongoDB en consecuencia. Este comando sólo puede ser utilizado por usuarios con el rol 'ADMIN'.

El bot también realiza una tarea cada 7 días para comprobar las promociones vencidas y envía notificaciones al servidor.

## 👥 Contribución

Las solicitudes de pull son bienvenidas. Para cambios importantes, por favor abre un issue primero para discutir lo que te gustaría cambiar.

## 📄 Licencia

[MIT](https://choosealicense.com/licenses/mit/)
