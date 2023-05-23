# 🤖 BotiBotDiscord - Gestión de Promociones en Discord

![image](https://github.com/CositortoL/BotiBotDiscord/assets/134352245/e75e2e9b-43b1-4600-ba19-94da6df9c11a)


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
5. Si quieres conectarte a mongo Db con certificado debes colocar el certificado en el mismo lugar que el .py y modificar la linea 91 colcandole el nombre del certificado:
```
client = MongoClient(uri, tls=True, tlsCertificateKeyFile='{NOMBRE DEL CERTIFICADO}.pem')
```
En caso que quieras Usuario y Password debes borrar la linea 91 y adaptarlo a esto:
```
Caso contrario debes colcoar el MongoClient con usuario como la documentacion de mongo lo indica:

# Obtén las credenciales de las variables de entorno
mongo_user = os.getenv('MONGO_USER')
mongo_password = os.getenv('MONGO_PASSWORD')

# Crea la cadena de conexión utilizando las credenciales
mongo_uri = f"mongodb+srv://{mongo_user}:{mongo_password}@cluster0.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

# Crea el cliente de MongoDB
client = MongoClient(mongo_uri)
``` 
  
## 🎮 Uso

El bot soporta los siguientes comandos:

- `/promocion`: Este comando permite a los usuarios agregar una nueva promoción al sistema. Cuando un usuario escribe /promocion, el bot enviará un mensaje privado al usuario solicitando los detalles de la promoción. El usuario debe responder a estos mensajes privados con la información solicitada.

Para que este comando funcione correctamente, el usuario debe tener habilitada la opción de recibir mensajes privados de servidores en sus ajustes de privacidad de Discord.

- `/ver_promociones`: Muestra todas las promociones actuales en el servidor.

- `/eliminar_registro`: Este comando permite a los administradores eliminar un registro de promoción existente. Cuando un administrador escribe /eliminar_registro, el bot solicitará el UUID del registro que se desea eliminar.

- `/ver_logs`: Muestra todos los registros de logs. Este comando sólo puede ser utilizado por usuarios con los roles 'ADMIN'.

- `/editar_registro`: Este comando permite a los administradores editar un registro de promoción existente. Cuando un administrador escribe /editar_registro, el bot solicitará el UUID del registro que se desea editar y luego solicitará la nueva información para ese registro.

- `/replica`: Este comando permite a los administradores sincronizar los datos entre Google Sheets y MongoDB. Cuando un administrador escribe /replica, el bot comparará los datos en Google Sheets y MongoDB y realizará las actualizaciones necesarias.


##👾Tareas Automáticas👾
`
El bot tiene una tarea automática que se ejecuta cada 7 días para verificar las promociones vencidas. Esta tarea busca todas las promociones que hayan vencido y las marca como vencidas en la base de datos. También envía un mensaje al canal de Discord especificado para informar sobre las promociones vencidas.
`
##🚨Errores y Excepciones🚨`
El bot está diseñado para manejar varios tipos de errores y excepciones. Aquí hay algunos ejemplos:
Si un usuario intenta usar un comando para el cual no tiene permisos, el bot enviará un mensaje indicando que el usuario no tiene permisos para usar ese comando.
Si un usuario proporciona información incorrecta o incompleta al agregar o editar una promoción, el bot enviará un mensaje indicando el error y solicitando la información correcta.
Si ocurre un error al intentar sincronizar los datos entre Google Sheets y MongoDB con el comando /replica, el bot enviará un mensaje con detalles sobre el error.
Si un usuario no responde a los mensajes privados del bot dentro de un cierto tiempo al agregar una nueva promoción, el bot cancelará el proceso y enviará un mensaje indicando que se ha agotado el tiempo.
Si ocurre un error al intentar eliminar o editar un registro que no existe, el bot enviará un mensaje indicando que el registro no se encontró.

Por favor, ten en cuenta que estos son solo algunos ejemplos y el bot puede manejar muchos otros tipos de errores y excepciones. Siempre que ocurra un error, el bot intentará proporcionar información útil para ayudar a resolver el problema.
`

## 👥 Contribución

Las solicitudes de pull son bienvenidas. Para cambios importantes, por favor abre un issue primero para discutir lo que te gustaría cambiar.

## 📄 Licencia

[MIT](https://choosealicense.com/licenses/mit/)
