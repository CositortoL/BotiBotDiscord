import discord
import asyncio
import datetime
import gspread
import uuid
import random
import string
import interactions
import logging
import os
from discord.ext import commands
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from interactions import Button, ButtonStyle, InteractionType
from discord.ext.commands import MissingPermissions
from pymongo import MongoClient
from discord import Embed
from discord.ext import tasks
from google.auth.transport.requests import Request
from datetime import datetime, date, timedelta


intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
CANCEL_COMMAND = "/cancelar"
token = os.getenv('DISCORD_TOKEN')
channel_id = int(os.getenv('CHANNELID'))
tktgoogle = os.getenv('GOOGLE_SHEETS_API_KEY')


bot = commands.Bot(command_prefix='/', intents=intents)

promociones = []  # Lista para almacenar las promociones

### BLOQUE DE LOGS ###

#Configura el logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler(f"logs/log_{datetime.now().strftime('%Y%m%d')}.log"),
                              logging.StreamHandler()])

# Luego, puedes usar logging.info() para registrar mensajes en el archivo de log y en la consola
logging.info("Este mensaje se registrará en el archivo de log y en la consola")

# Para eliminar los archivos de log antiguos, puedes usar os.remove()
for filename in os.listdir("logs"):
    if filename.endswith(".log"):
        filepath = os.path.join("logs", filename)
        # Comprueba si el archivo tiene más de 30 días
        if datetime.fromtimestamp(os.path.getmtime(filepath)) < datetime.now() - timedelta(days=30):
            os.remove(filepath)

##### BLOQUE DE LOGS ####

# Función para validar si un string es un número
def is_valid_number(number_str):
    try:
        float(number_str)
        return True
    except ValueError:
        return False

# Función para validar si una URL es válida
def is_valid_url(url_str):
    import re
    url_regex = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return re.match(url_regex, url_str) is not None

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


#Gsheet api Bot:
# Ruta al archivo JSON de las credenciales descargado anteriormente
credentials = Credentials.from_service_account_file('NAME OF CREDENCIAL.json', scopes=['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive'])
# Autenticar con las credenciales
gc = gspread.authorize(credentials)

# ID de tu hoja de cálculo de Google Sheets
sheet_id = tktgoogle

#### MONGO DB CONECTIONS ####
# Crear una conexión con MongoDB
try:
    uri = "URI TUYA DE MONGO DB"
    client = MongoClient(uri, tls=True, tlsCertificateKeyFile='X509-cert-8207758789985649306.pem')

    # Seleccionar la base de datos
    db = client["Base de datos tuya "]

    # Seleccionar la colección
    collection = db["TU collection"]
    print("Conexión exitosa a la base de datos de mongo DB")
except Exception as e:
    print("No se pudo conectar a MongoDB: %s" % e)
#### MONGO DB CONECTIONS ####

# Abrir la hoja de cálculo por su ID
sheet = gc.open_by_key(sheet_id).sheet1
#Generador de ID
def generar_identificador():
    longitud = 6  # Longitud del identificador (puedes ajustarla)
    caracteres = string.ascii_uppercase + string.ascii_lowercase + string.digits
    identificador = ''.join(random.choice(caracteres) for _ in range(longitud))
    return identificador
#Creacion de Log
logs = []  # Lista para almacenar los registros de log

async def obtener_registro_por_uuid(uuid):
    cell = sheet.find(uuid)
    record = sheet.row_values(cell.row)
    return record, cell


@bot.command()
async def promocion(ctx):
  # ID del canal donde se permite el comando
    canal_permitido_id = channel_id  # Reemplaza esto con el ID de tu canal

    # Verificar si el comando se ejecutó en el canal permitido
    if ctx.channel.id != canal_permitido_id:
        canal_permitido = bot.get_channel(canal_permitido_id)
        await ctx.send(f"Este comando solo se puede usar en {canal_permitido.mention}.")
        return
       
    user = ctx.author
    message_content = ctx.message.content
    author_name = ctx.message.author.name
    # Generar referencia interna para la promoción
    referencia_interna = generar_identificador()
    #Inserto Indice de log por datos -  Registrar el log de input
    log = f"[{datetime.now()}] Usuario {user} ingresó un dato: {message_content}"
    logs.append(log)

    try:
        await user.send("¡Hola! Por favor, sigue las instrucciones para enviar una promoción. (escribe '/cancelar' para abortar):")
        
        # Pregunta si el usuario quiere adjuntar una imagen
        await user.send("¿Deseas adjuntar una imagen relacionada con la promoción? Responde con 'si' o 'no'. "
                    "Recuerda que las imágenes deben estar en formato .jpg, .png o .gif y no deben superar los 8 MB:")
        respuesta_imagen = await bot.wait_for("message", check=lambda m: m.author == user, timeout=30)
        if respuesta_imagen.content.lower() == CANCEL_COMMAND:
            await user.send("Operación cancelada.")
            return
        imagen_url = None
 # Lista de posibles formas de "sí"
        afirmaciones = ["sí", "si", "s", "yes", "y", "sí.", "si."]
        if respuesta_imagen.content.lower() in afirmaciones:
            await user.send("Por favor, adjunta la imagen:")
            imagen_msg = await bot.wait_for("message", check=lambda m: m.author == user and m.attachments, timeout=15)
            imagen_url = imagen_msg.attachments[0].url 

 # Validación del nombre del banco/tarjeta/app
        await user.send("Escribe el nombre del banco, tarjeta o aplicación (escribe '/cancelar' para abortar):")
        nombre = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15)

        if nombre.content.lower() == CANCEL_COMMAND:
            await user.send("Operación cancelada.")
            return
        while not nombre.content:  # Comprueba si el nombre está vacío
            await user.send("El nombre no puede estar vacío. Por favor, intenta de nuevo:")
            nombre = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15)
        if nombre.content.lower() == CANCEL_COMMAND:
            await user.send("Operación cancelada.")
            return
   # Solicitar y validar la fecha
        while True:
            await user.send("Escribe la fecha en formato DD/MM/AAAA (escribe '/cancelar' para abortar):")
            fecha_msg = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15)
            if fecha_msg.content.lower() == CANCEL_COMMAND:
                await user.send("Operación cancelada.")
                return
            try:
                fecha = datetime.strptime(fecha_msg.content, "%d/%m/%Y")
                break
            except ValueError:
                await user.send("Formato de fecha inválido. Por favor, intenta de nuevo.")
        
        await user.send("Escribe el rubro de la promoción:")
        rubro = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15)
        
        #Solicitar y validar el descuento
        while True:
            await user.send("Escribe el descuento de la promoción (número o porcentaje) (escribe '/cancelar' para abortar):")
            descuento_msg = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15)
            if descuento_msg.content.lower() == CANCEL_COMMAND:
                await user.send("Operación cancelada.")
                return
            descuento_str = descuento_msg.content.replace('%', '')  # quitar el signo de porcentaje
            try:
                descuento = float(descuento_str)  # ahora esto debería funcionar
                break
            except ValueError:
                await user.send("Descuento inválido. Por favor, intenta de nuevo.")
        
        # Validación del tope
        await user.send("Escribe el tope de la promoción:")
        tope = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15)
        if tope.content.lower() == CANCEL_COMMAND:
            await user.send("Operación cancelada.")
            return
        while not is_valid_number(tope.content):  # Comprueba si el tope es un número válido
            await user.send("Tope no válido. Por favor, escribe un número válido:")
            tope = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15)
        if tope.content.lower() == CANCEL_COMMAND:
            await user.send("Operación cancelada.")
            return
        
         # Validación del enlace
        await user.send("Escribe el enlace a los términos y condiciones:")
        enlace = await bot.wait_for("message", check=lambda m:m.author == user, timeout=15)
        if enlace.content.lower() == CANCEL_COMMAND:
            await user.send("Operación cancelada.")
            return
       
        while not is_valid_url(enlace.content):  # Comprueba si el enlace es una URL válida
            await user.send("Enlace no válido. Por favor, escribe un enlace válido:")
            enlace = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15) 
        if enlace.content.lower() == CANCEL_COMMAND:
            await user.send("Operación cancelada.")

        # Solicitar y validar la fecha de vencimiento
        while True:
            await user.send("Obligatorio - Escribe la fecha de vencimiento en formato DD/MM/AAAA (escribe '/cancelar' para abortar): ")
            vencimiento_msg = await bot.wait_for("message", check=lambda m: m.author == user, timeout=15)
            if vencimiento_msg.content.lower() == CANCEL_COMMAND:
                await user.send("Operación cancelada.")
                return
            try:
                vencimiento = datetime.strptime(vencimiento_msg.content, "%d/%m/%Y")
                break
            except ValueError:
                await user.send("Formato de fecha inválido. Por favor, intenta de nuevo.")



        ###### Bloque falopa para probar el embed ######

         # Crear un embed
        embed = discord.Embed(title=f":tada: ¡Nueva promoción enviada por {user.name}!", color=0x00ff00)
        embed.add_field(name="Banco/Tarjeta/App:", value=nombre.content, inline=False)
        embed.add_field(name=":calendar: Fecha:", value=fecha.strftime("%d/%m/%Y"), inline=False)
        embed.add_field(name=":shopping_cart: Rubro:", value=rubro.content, inline=False)
        embed.add_field(name=":moneybag: Descuento:", value=f"{descuento}%", inline=False)
        embed.add_field(name=":money_with_wings: Tope:", value=tope.content, inline=False)
        embed.add_field(name=":calendar: Fecha de Vencimiento :", value=vencimiento.strftime("%d/%m/%Y"), inline=False)
        embed.add_field(name=":link: Enlace:", value=enlace.content, inline=False)
        embed.add_field(name=":id: UUID:", value=referencia_interna, inline=False)
        if imagen_url:
            embed.set_image(url=imagen_url)  # Agrega la imagen al embed
        ###### MONGO DUPLICATE MODULE ######

        # Crear el documento que quieres insertar
        documento = {
            "Banco/Tarjeta/App:": nombre.content,
            "Fecha": fecha.strftime("%d/%m/%Y"),
            "Rubro": rubro.content,
            "Descuento": descuento,
            "Tope": tope.content,
            "Enlace": enlace.content,
            "Comando": message_content,
            "Usuario": author_name,
            "Vencimiento": vencimiento.strftime("%d/%m/%Y"),
            "URL Imagen": imagen_url,
            "UUID": referencia_interna,
            "Log": log,
            "Puntero": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Imprimir el documento
        print(documento)
        # Insertar el documento en la colección y verificar la inserción
        resultado = collection.insert_one(documento)
        if resultado.inserted_id:
                print(f"Documento insertado correctamente con el ID: {resultado.inserted_id}")
        else:
                print("Hubo un error al insertar el documento.")

        ###### MONGO DUPLICATE MODULE ######


        # Almacenar la promoción en el Google Sheet
        #row_data = [nombre.content, fecha.strftime("%d/%m/%Y"), rubro.content, descuento, tope, enlace.content]
        #sheet.append_row(row_data)
        row_data = [nombre.content, fecha.strftime("%d/%m/%Y"), rubro.content, descuento, tope.content, enlace.content, message_content, author_name, imagen_url, referencia_interna,log, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),vencimiento.strftime("%d/%m/%Y")]
        sheet.append_row(row_data)

    
     #  Publicar promoción en un canal específico = Reemplaza este número por el ID correspondiente al canal donde se publicarán las promociones
        canal_promociones = bot.get_channel(channel_id)
        await canal_promociones.send(embed=embed)
        if imagen_url:
         await canal_promociones.send(imagen_url)  # Publica la imagen si existe

        await ctx.send("¡Promoción recibida y almacenada! Gracias por tu colaboración.") 

    except asyncio.TimeoutError:
         await user.send("Se agotó el tiempo para ingresar la información. Por favor, intenta de nuevo.")


@bot.command()
async def ver_promociones(ctx):
# Mostrar el menú interactivo principal
    menu = discord.Embed(title="Menú de Promociones", description="Elige una opción de búsqueda:")
    menu.add_field(name="👋 Filtrar por período", value="Promociones en un período de tiempo")
    menu.add_field(name="🖖 Buscar por UUID", value="Buscar una promoción por UUID")
    menu.add_field(name="🙌 Filtrar por fecha", value="Filtrar promociones por fecha específica")
    menu.add_field(name="😴 Cancelar", value="Cancelar y salir del menú")

    menu_message = await ctx.send(embed=menu)
    await menu_message.add_reaction("👋")
    await menu_message.add_reaction("🖖")
    await menu_message.add_reaction("🙌")
    await menu_message.add_reaction("😴")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["👋", "🖖", "🙌", "😴"]

    try:
        while True:
            reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == "👋":
                await submenu_periodo(ctx)
            elif str(reaction.emoji) == "🖖":
                await buscar_promocion_uuid(ctx)
            elif str(reaction.emoji) == "🙌":
                await buscar_promocion_fecha(ctx)
            elif str(reaction.emoji) == "😴":
                await ctx.send("Has cancelado el menú.")
                break

            await menu_message.remove_reaction(reaction, user)

    except asyncio.TimeoutError:
        await ctx.send("Se agotó el tiempo de espera. Por favor, intenta nuevamente.")
        await limpiar_mensajes(ctx)

async def submenu_periodo(ctx):

    # Mostrar el menú interactivo
    menu = discord.Embed(title="Menú de Promociones", description="Elige una opción para filtrar las promociones:")
    menu.add_field(name="1️⃣ Busqueda por U. 30 minutos", value="Promociones en los últimos 30 minutos")
    menu.add_field(name="2️⃣ Busqueda por U. Hora", value="Promociones en la última hora")
    menu.add_field(name="3️⃣ Busqueda por U. 24hs", value="Promociones en el último día")
    menu.add_field(name="4️⃣ Busqueda por U. 48hs", value="Promociones en los últimos 2 días")
    menu.add_field(name="5️⃣ Busqueda por U. Semana", value="Promociones en la última semana")
    menu.add_field(name="6️⃣ Busqueda por U. Mes", value="Promociones en el último mes")
    menu.add_field(name="❌ Cancelar", value="Cancelar y salir del menú")

    menu_message = await ctx.send(embed=menu)
    await menu_message.add_reaction("1️⃣")
    await menu_message.add_reaction("2️⃣")
    await menu_message.add_reaction("3️⃣")
    await menu_message.add_reaction("4️⃣")
    await menu_message.add_reaction("5️⃣")
    await menu_message.add_reaction("6️⃣")
    await menu_message.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "❌"]

    try:
        while True:
            reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == "1️⃣":
                await filtrar_promociones_periodo(ctx, 30)
            elif str(reaction.emoji) == "2️⃣":
                await filtrar_promociones_periodo(ctx, 60)
            elif str(reaction.emoji) == "3️⃣":
                await filtrar_promociones_periodo(ctx, 1440)
            elif str(reaction.emoji) == "4️⃣":
                await filtrar_promociones_periodo(ctx, 2880)
            elif str(reaction.emoji) == "5️⃣":
                await filtrar_promociones_periodo(ctx, 10080)
            elif str(reaction.emoji) == "6️⃣":
                await filtrar_promociones_periodo(ctx, 43200)
            elif str(reaction.emoji) == "❌":
                await ctx.send("Has cancelado el menú.")
                break

            await menu_message.remove_reaction(reaction, user)

    except asyncio.TimeoutError:
        await ctx.send("Se agotó el tiempo de espera. Por favor, intenta nuevamente.")
        await limpiar_mensajes(ctx)

async def filtrar_promociones_periodo(ctx, minutos):
    if minutos > 60:
        await ctx.send(f"Buscando promociones en los últimos {int(minutos/1440)} Dias...")

    else:    
        await ctx.send(f"Buscando promociones en los últimos {minutos} minutos...")

    now = datetime.now()
    time_limit = now - timedelta(minutes=minutos)

    try:
        rows = sheet.get_all_records()
        if not rows:
            await ctx.send("No hay promociones almacenadas.")
            return

        promociones_filtradas = []
        for row in rows:
            puntero_str = row['Puntero']
            if puntero_str:
                puntero = datetime.strptime(puntero_str, "%Y-%m-%d %H:%M:%S")
                if puntero >= time_limit:
                    promocion_formateada = f"Banco/Tarjeta/App: {row['Nombre del banco/tarjeta/aplicacion']}\n"
                    promocion_formateada += f"Día: {row['Fecha']}\n"
                    promocion_formateada += f"Rubro: {row['Rubro']}\n"
                    promocion_formateada += f"Descuento: {row['Descuento']}%\n"
                    promocion_formateada += f"Tope: {row['Tope']}\n"
                    promocion_formateada += f"Link TYC: {row['Enlace']}\n"
                    promocion_formateada += f"Imagen URL: {row['URL Imagen']}\n"
                    promocion_formateada += f"ID: {row['UUID']}\n"
                    promociones_filtradas.append(promocion_formateada)

        if not promociones_filtradas:
                
            if minutos > 60:
                await ctx.send(f"No se encontraron promociones en los últimos {int(minutos/1440)} Dias...")
        
            else:
                await ctx.send(f"No se encontraron promociones en los últimos {minutos} minutos.")
        
        else:
            await ctx.send(f"Promociones encontradas en los últimos {minutos} minutos:")
            for promocion in promociones_filtradas:
                await ctx.send(promocion)

    except Exception as e:
        await ctx.send(f"Error al filtrar las promociones: {str(e)}")

    # Solicitar opción de búsqueda adicional\
    # # Mostrar el menú interactivo
    menu = discord.Embed(title="Elige una opción adicional de búsqueda:", description="Elige una opción para filtrar las promociones:")
    menu.add_field(name="👾 Buscar por UUID", value="Busca una opcion por el ID de publicacion")
    menu.add_field(name="🤖 Buscar por fecha concreta", value="Buscar por una fecha concreta ( Expesada en DD/MM/AAAA)")
    menu.add_field(name="🛑 Cancelar", value="Cancelar Busqueda")
    menu.add_field(name="🥵 Volver a buscar", value="Volver a realizar la busqueda")

    
         
    #await ctx.send("Elige una opción adicional de búsqueda:")
    #menu_message2 = await ctx.send("👾 Buscar por UUID\n🤖 Buscar por fecha concreta\n🛑 Cancelar\n🥵 Volver a buscar")

    menu_message2 = await ctx.send(embed=menu)
    await menu_message2.add_reaction("👾")
    await menu_message2.add_reaction("🤖")
    await menu_message2.add_reaction("🥵")
    await menu_message2.add_reaction("🛑")
    

    def check_reaction(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["👾", "🤖", "🥵","🛑"]
   
    try:
      #reaction = await bot.wait_for("reaction_add", check=check_reaction, timeout=30.0)
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
      
        while True:
            reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)

            if str(reaction.emoji) == "👾":
                await buscar_promocion_uuid(ctx)
            elif str(reaction.emoji) == "🤖":
                await buscar_promocion_fecha(ctx)
            elif str(reaction.emoji) == "🥵":
                await submenu_periodo(ctx)
            elif str(reaction.emoji) == "🛑":
                await ctx.send("Has cancelado la búsqueda adicional.")
                break

            await menu_message2.remove_reaction(reaction, user)
       # if str(reaction.emoji) == "👾":
         #   await buscar_promocion_uuid(ctx)
        #elif str(reaction.emoji) == "🤖":
          #  await buscar_promocion_fecha(ctx)
        #elif str(reaction.emoji) == "🥵":
         #   await submenu_periodo(ctx)
        #elif str(reaction.emoji) == "🛑":
         #   await ctx.send("Has cancelado la búsqueda adicional.")
        #else:
         #   await ctx.send("Reacción inválida. Intenta nuevamente.")
    
    except asyncio.TimeoutError:
        await ctx.send("Se agotó el tiempo de espera. Por favor, intenta nuevamente.")
        await limpiar_mensajes(ctx)

async def buscar_promocion_uuid(ctx):
    await ctx.send("Por favor, ingresa el UUID de la promoción que deseas buscar:")

    def check_message(m):
        return m.author == ctx.author

    try:
        message = await bot.wait_for("message", check=check_message, timeout=30.0)
        uuid_input = message.content.strip()

        if not uuid_input:
            await ctx.send("El UUID no puede estar vacío. Por favor, intenta nuevamente.")
            return

        rows = sheet.get_all_records()
        promocion_encontrada = None
        for row in rows:
            if row["UUID"] == uuid_input:
                promocion_encontrada = row
                break

        if promocion_encontrada:
            promocion_formateada = f"Banco/Tarjeta/App: {promocion_encontrada['Nombre del banco/tarjeta/aplicacion']}\n"
            promocion_formateada += f"Día: {promocion_encontrada['Fecha']}\n"
            promocion_formateada += f"Rubro: {promocion_encontrada['Rubro']}\n"
            promocion_formateada += f"Descuento: {promocion_encontrada['Descuento']}%\n"
            promocion_formateada += f"Tope: {promocion_encontrada['Tope']}\n"
            promocion_formateada += f"Link TYC: {promocion_encontrada['Enlace']}\n"
            promocion_formateada += f"Imagen URL: {promocion_encontrada['URL Imagen']}\n"
            promocion_formateada += f"ID: {promocion_encontrada['UUID']}\n"

            await ctx.send("Promoción encontrada:")
            await ctx.send(promocion_formateada)
        else:
            await ctx.send("No se encontró ninguna promoción con el UUID proporcionado.")

    except asyncio.TimeoutError:
        await ctx.send("Se agotó el tiempo de espera. Por favor, intenta nuevamente.")
        await limpiar_mensajes(ctx)

async def buscar_promocion_fecha(ctx):
    await ctx.send("Por favor, ingresa la fecha en formato DD/MM/AAAA para buscar las promociones (ejemplo: 14/05/2023):")

    def check_message(m):
        return m.author == ctx.author

    try:
        message = await bot.wait_for("message", check=check_message, timeout=30.0)
        fecha_input = message.content.strip()

        try:
            fecha = datetime.strptime(fecha_input, "%d/%m/%Y").date()
        except ValueError:
            await ctx.send("Formato de fecha inválido. Por favor, intenta nuevamente.")
            return

        rows = sheet.get_all_records()
        promociones_filtradas = []
        for row in rows:
            fecha_promocion = datetime.strptime(row["Fecha"], "%d/%m/%Y").date()
            if fecha_promocion == fecha:
                promocion_formateada = f"Banco/Tarjeta/App: {row['Nombre del banco/tarjeta/aplicacion']}\n"
                promocion_formateada += f"Día: {row['Fecha']}\n"
                promocion_formateada += f"Rubro: {row['Rubro']}\n"
                promocion_formateada += f"Descuento: {row['Descuento']}%\n"
                promocion_formateada += f"Tope: {row['Tope']}\n"
                promocion_formateada += f"Link TYC: {row['Enlace']}\n"
                promocion_formateada += f"Imagen URL: {row['URL Imagen']}\n"
                promocion_formateada += f"ID: {row['UUID']}\n"
                promociones_filtradas.append(promocion_formateada)

        if not promociones_filtradas:
            await ctx.send(f"No se encontraron promociones para la fecha {fecha_input}.")
        else:
            await ctx.send(f"Promociones encontradas para la fecha {fecha_input}:")
            for promocion in promociones_filtradas:
                await ctx.send(promocion)

    except asyncio.TimeoutError:
        await ctx.send("Se agotó el tiempo de espera. Por favor, intenta nuevamente.")
        await limpiar_mensajes(ctx)

async def limpiar_mensajes(ctx):
    canal = bot.get_channel(channel_id)
    mensajes = []
    # Obtener los últimos 20 mensajes del canal
    async for message in canal.history(limit=20):
        mensajes.append(message)

    # Filtrar y borrar los mensajes del usuario y del bot
    mensajes_para_borrar = [msg for msg in mensajes if msg.author == ctx.author or msg.author == bot.user]
    await canal.delete_messages(mensajes_para_borrar)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('/'):
        await bot.process_commands(message)
        try:
            await message.add_reaction("✅")
        except discord.errors.NotFound:
            # Manejar el error de mensaje no encontrado
            pass

@bot.event
async def on_ready():
    check_expired_promotions.start()


@bot.command()
@commands.has_permissions(administrator=True)
async def purgeDB(ctx):
    # Obtén todos los documentos con "Vencimiento": "EXPIRED"
    expired_docs = collection.find({"Vencimiento": "EXPIRED"})
    
    # Cuenta cuántos documentos hay
    count = collection.count_documents({"Vencimiento": "EXPIRED"})

    # Envía un mensaje pidiendo confirmación
    confirm_message = await ctx.send(f"Se encontraron {count} documentos vencidos. ¿Deseas eliminarlos? Reacciona con 👍 para confirmar o 👎 para cancelar.")
    
    # Agrega las reacciones al mensaje
    await confirm_message.add_reaction("👍")
    await confirm_message.add_reaction("👎")
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["👍", "👎"]
    
    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("Operación cancelada por tiempo de espera.")
    else:
        if str(reaction.emoji) == "👍":
            # El usuario confirmó, así que elimina los documentos
            collection.delete_many({"Vencimiento": "EXPIRED"})
            await ctx.send(f"Se eliminaron {count} documentos vencidos.")
        else:
            # El usuario canceló la operación
            await ctx.send("Operación cancelada.")

@bot.command()
@commands.has_any_role('ADMIN')
async def eliminar_registro(ctx):
    # Solicitar el UUID al usuario
    await ctx.send("Por favor, introduce el UUID del registro que deseas eliminar. Responde con 'cancelar' para cancelar el proceso.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    uuid_msg = await bot.wait_for('message', check=check)
    if uuid_msg.content.lower() == 'cancelar':
        await ctx.send("Proceso cancelado.")
        return

    uuid = uuid_msg.content

    # Buscar el registro por UUID
    log_records = sheet.get_all_records()
    for i, record in enumerate(log_records):
        if record['UUID'] == uuid:
            # Mostrar el registro al usuario
            record_str = f"Nombre del banco/tarjeta/aplicación: {record['Nombre del banco/tarjeta/aplicacion']}\n" \
                         f"Fecha: {record['Fecha']}\n" \
                         f"Rubro: {record['Rubro']}\n" \
                         f"Descuento: {record['Descuento']}\n" \
                         f"Tope: {record['Tope']}\n" \
                         f"Enlace: {record['Enlace']}\n" \
                         f"Comando: {record['Comando']}\n" \
                         f"Usuario: {record['Usuario']}\n" \
                         f"URL Imagen: {record['URL Imagen']}\n" \
                         f"UUID: {record['UUID']}\n" \
                         f"Log: {record['Log']}\n" \
                         f"Puntero: {record['Puntero']}"
            await ctx.send(f"Estás a punto de eliminar el siguiente registro:\n{record_str}")
            # Solicitar confirmación antes de eliminar
            confirm_message = await ctx.send(f"Estás a punto de eliminar el registro {uuid}. ¿Estás seguro? Reacciona con 👍 para confirmar, 👎 para cambiar la eliminación, o 🚫 para cancelar.")
            await confirm_message.add_reaction('👍')
            await confirm_message.add_reaction('🚫')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['👍', '🚫'] and reaction.message.id == confirm_message.id

            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("No se recibió confirmación. La eliminación del registro ha sido cancelada.")
                return
            else:
                if str(reaction.emoji) == '🚫':
                    await ctx.send("La eliminación del registro ha sido cancelada.")
                    return

            # Eliminar el registro de la hoja de cálculo
            sheet.delete_rows(i + 2, i + 2)  # +2 porque la fila 1 es el encabezado y las filas en gspread empiezan en 1

            # Informar al usuario de que la eliminación fue exitosa
            await ctx.send("El registro ha sido eliminado con éxito.")

            # Registrar la acción
            action_log = f"El usuario {ctx.author} eliminó el registro {uuid} a las {datetime.now()}."
            print(action_log)
            # Aquí puedes agregar código para guardar el registro de acción en un archivo o en una base de datos

            return

    # Si no se encontró el registro, informar al usuario
    await ctx.send("No se encontró un registro con ese UUID.")
@eliminar_registro.error
async def eliminar_registro_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("Lo siento, no tienes permisos para usar este comando.")

@bot.command()
@commands.has_any_role('ADMIN')
async def ver_logs(ctx):
    

    log_records = sheet.get_all_records()
    
    if log_records:
        for record in log_records[1:]:
            log_id = record['UUID']
            log_data = record['Log']
            formatted_log = f"UUID: {log_id}\nRegistro de Log:\n{log_data}"
            await ctx.send(formatted_log)
    else:
        await ctx.send("No hay registros de log")
@ver_logs.error
async def ver_logs_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("Lo siento, no tienes permisos para usar este comando.")

@bot.command()
@commands.has_any_role('ADMIN')
async def editar_registro(ctx, uuid: str=None):
    if uuid is None:
        await ctx.send("Por favor, introduce el UUID del registro que quieres editar.")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        uuid_msg = await bot.wait_for('message', check=check)
        uuid = uuid_msg.content

    record, cell = await obtener_registro_por_uuid(uuid)
    
    fields = ["Nombre del banco/tarjeta/aplicacion", "Fecha", "Rubro", "Descuento", "Tope", "Enlace"]
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
    
    embed = discord.Embed(title="Selecciona el campo que quieres editar", description="\n".join(f"{emoji} {field}" for emoji, field in zip(emojis, fields)), color=0x00ff00)
    message = await ctx.send(embed=embed)

    for emoji in emojis:
        await message.add_reaction(emoji)
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in emojis

    reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
    
    index = emojis.index(str(reaction.emoji))
    field = fields[index]
    
    await ctx.send(f"Introduce el nuevo valor para {field}")

    def check(m):
        return m.author == ctx.author
    
    new_value = await bot.wait_for("message", check=check)
    
    sheet.update_cell(cell.row, index + 1, new_value.content)  # +1 para convertir el índice a 1-indexing y +1 porque los campos empiezan en la columna 2
    await ctx.send(f"{field} ha sido modificado a {new_value.content}.")
@editar_registro.error
async def editar_registro_error (ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("Lo siento, no tienes permisos para usar este comando.")

@bot.command()
@commands.has_role('ADMIN')  # Asegura que solo los administradores pueden usar este comando
async def replica(ctx):
    # Descargar todos los datos de Google Sheets
    datos_gsheet = sheet.get_all_records()

    # Descargar todos los datos de MongoDB
    datos_mongo = list(collection.find({}))

    # Convertir los datos de Google Sheets y MongoDB en diccionarios para facilitar la comparación
    datos_gsheet_dict = {dato['UUID']: dato for dato in datos_gsheet}
    datos_mongo_dict = {dato['UUID']: dato for dato in datos_mongo}

    # Identificar registros idénticos, diferentes y nuevos
    registros_identicos = []
    registros_diferentes = []
    registros_nuevos = []

    for referencia_interna, dato_gsheet in datos_gsheet_dict.items():
        dato_mongo = datos_mongo_dict.get(referencia_interna)
        if dato_mongo is None:
            # Este registro es nuevo
            registros_nuevos.append(dato_gsheet)
        elif dato_gsheet == dato_mongo:
            # Este registro es idéntico
            registros_identicos.append(dato_gsheet)
        else:
            # Este registro es diferente
            registros_diferentes.append((dato_gsheet, dato_mongo))
    # Interactuar con el usuario para obtener su confirmación antes de realizar cambios en la base de datos
    if registros_diferentes:
        msg = await ctx.send(f"Hay {len(registros_diferentes)} registros diferentes. ¿Deseas sobrescribirlos en MongoDB?")
        await msg.add_reaction('✅')  # Emoji de confirmación
        await msg.add_reaction('❌')  # Emoji de cancelación
    
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send('Se agotó el tiempo para responder. Operación cancelada.')
        else:
            if str(reaction.emoji) == '✅':
                # El usuario confirmó, sobrescribir los registros en MongoDB
                try:
                    for dato_gsheet, dato_mongo in registros_diferentes:
                        collection.replace_one({'UUID': dato_gsheet['UUID']}, dato_gsheet)
                    await ctx.send('Los registros diferentes han sido sobrescritos en MongoDB.')
                except Exception as e:
                    await ctx.send(f'Ocurrió un error al sobrescribir los registros en MongoDB: {e}')
            else:

                await ctx.send('Operación cancelada.')
    if registros_nuevos:
        msg = await ctx.send(f"Hay {len(registros_nuevos)} registros nuevos. ¿Deseas agregarlos a MongoDB?")
        await msg.add_reaction('✅')  # Emoji de confirmación
        await msg.add_reaction('❌')  # Emoji de cancelación

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('Se agotó el tiempo para responder. Operación cancelada.')
    else:
        if str(reaction.emoji) == '✅':
            # El usuario confirmó, agregar los registros nuevos a MongoDB
            try:
                collection.insert_many(registros_nuevos)
                await ctx.send('Los registros nuevos han sido agregados a MongoDB.')
            except Exception as e:
                await ctx.send(f'Ocurrió un error al agregar los registros nuevos a MongoDB: {e}')
        else:
            await ctx.send('Operación cancelada.')


@tasks.loop(hours=168)  # Ejecuta esta tarea cada 24 horas
async def check_expired_promotions():
    logging.info("Comenzando chequeo de vencimientos...")
    canal_promociones = bot.get_channel(channel_id)  # Reemplaza este número por el ID del canal donde quieres enviar el mensaje
    embed = discord.Embed(
        title=":warning: Chequeo de Vencimientos",
        description="Se está iniciando el proceso de chequeo de vencimientos de promociones.",
        color=discord.Color.orange()
        )
    
    embed.set_footer(text="Este proceso se realiza automáticamente cada 7 Dias.")
    await canal_promociones.send(embed=embed)

    # Obtén la fecha actual
    today = date.today()

    # Obtén todas las promociones de la hoja de cálculo de Google Sheets
    promociones = sheet.get_all_records()
    promociones_vencidas = []  # Lista para almacenar las promociones vencidas


    # Recorre todas las promociones
    for i in range(len(promociones), 1, -1):
        promocion = promociones[i-2]  # i-2 porque las listas en Python empiezan en 0 y la primera fila es la cabecera
        # Convierte la fecha de vencimiento de la promoción a un objeto datetimedate
        fecha_vencimiento =datetime.strptime(promocion['Fecha de vencimiento'], "%d/%m/%Y").date()
        
        # Comprueba si la promoción ha expirado
        if fecha_vencimiento < today:
            # Envía un mensaje a Discord
            promociones_vencidas.append(promocion)
            canal_promociones = bot.get_channel(channel_id)  # Reemplaza esto con el ID de tu canal
             # Añade la promoción a la lista de promociones vencidas
            await canal_promociones.send(f"La promoción {promocion['Nombre del banco/tarjeta/aplicacion']} con UUID {promocion['UUID']} y fecha de vencimiento {promocion['Fecha de vencimiento']} ha expirado y se ha eliminado el registro.")

            # Elimina la promoción de la hoja de cálculo de Google Sheets
            sheet.delete_row(i)
            
            # Marca la promoción como expirada en MongoDB
            collection.update_one({"UUID": promocion['UUID']}, {"$set": {"Vencimiento": "EXPIRED"}})
    
    if not promociones_vencidas:
        logging.info("No se encontraron promociones vencidas.")
        await canal_promociones.send("No se encontraron promociones vencidas.")
    else:
        logging.info(f"Se encontraron {len(promociones_vencidas)} promociones vencidas.")
        await canal_promociones.send(f"Se encontraron {len(promociones_vencidas)} promociones vencidas y fuero eliminadas con exito.")

# Inicia la tarea cuando el bot esté listo
@bot.event
async def on_ready():
    check_expired_promotions.start()



bot.run(token)
