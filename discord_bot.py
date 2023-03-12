from datetime import timedelta
from random import gauss
import urllib, discord, redis, asyncio, json
from utils import emoticon

r = redis.Redis(host='localhost', port=6379, db=0)
token = 'token aqui.'
client = discord.Client()
delay = 1
lista_ids_liberadas = []
nao_logado = True


async def processar_acoes():
    print("(i) Processando Ações do Redis...")
    while True:
        try:
            acoes = []
            while True:
                acao = r.rpop('list_acoes')
                if acao is None:
                    break
                acoes.append(json.loads(acao.decode('utf-8')))
            for atividade in acoes:
                print(atividade)
                if atividade["acao"] == "enviar_mensagem":
                    if 'servidor' in atividade:
                        r.set(f"mensagem_enviada.{atividade['servidor']}.{atividade['canal']}.{atividade['horario']}",
                              await enviar_mensagem(atividade["conteudo"], atividade["servidor"], atividade["canal"]))
                    else:
                        r.set(f"mensagem_enviada.{atividade['canal']}.{atividade['horario']}",
                              await enviar_mensagem(atividade["conteudo"], None, atividade["canal"]))

                if atividade["acao"] == "carregar_historico":
                    if 'servidor' in atividade:
                        r.set(f"historico.{atividade['servidor']}.{atividade['canal']}",  await historico_mensagens(atividade["servidor"], atividade["canal"]))
                    else:
                        r.set(f"historico.{atividade['canal']}", await historico_mensagens(None, atividade["canal"]))
                if atividade["acao"] == "carregar_lista_servidor":
                    r.set("lista_servidores", lista_servidores())
                if atividade["acao"] == "carregar_lista_grupos_dm":
                    r.set("lista_grupos_dm", lista_grupos_dm())
                if atividade["acao"] == "carregar_lista_canais_texto":
                    print(r.set(f'lista_canais_texto.{atividade["conteudo"]}', lista_canais_texto(atividade["conteudo"])))
                if atividade["acao"] == "liberar_carregar_mensagens":
                    r.set(f'carregar_mensagens_liberada.{atividade["conteudo"]}', "0")
                    if not servidor_liberado(atividade["conteudo"]):
                        lista_ids_liberadas.append(atividade["conteudo"])
        except Exception as e:
            print(e)
        await asyncio.sleep(delay + gauss(0, 0.2))


@client.event
async def on_ready():
    print(f'(i) Logado como: {client.user.name}')
    r.set("nome", client.user.name)
    global nao_logado
    if nao_logado:
        nao_logado = False
        asyncio.create_task(processar_acoes())

async def enviar_mensagem(conteudo, id_servidor, id_canal_texto):
    try:
        if id_servidor:
            servidor = client.get_guild(int(id_servidor))
            canal = servidor.get_channel(int(id_canal_texto))
        else:
            canal = client.get_channel(int(id_canal_texto))

        await canal.send(conteudo)
        return "ok"
    except Exception as e:
        return f"{e}"

async def historico_mensagens(id_servidor, id_canal_texto):
    try:
        if id_servidor:
            servidor = client.get_guild(int(id_servidor))
            canal = servidor.get_channel(int(id_canal_texto))
        else:
            canal = client.get_channel(int(id_canal_texto))

        mensagens = []
        async for message in canal.history(limit=50):
            mensagens.append(gerar_dict_mensagem(message))
        return json.dumps(mensagens[::-1])
    except Exception as e:
        print(e)
        return "[]"


def servidor_liberado(id_servidor):
    if id_servidor in lista_ids_liberadas: return True
    return False


def lista_canais_texto(id_canal):
    servidor = client.get_guild(int(id_canal))
    canais_texto = []
    for text_channel in servidor.text_channels:
        canais_texto.append(
            {
                "nome": text_channel.name,
                "id_canal": str(text_channel.id)
            })
    return json.dumps(canais_texto)


def lista_servidores():
    servidores = []
    for guild in client.guilds:

        servidores.append(
            {
                "nome": guild.name,
                "id_servidor": str(guild.id)
            })
    return json.dumps(servidores)


def lista_grupos_dm():
    grupos = []
    for private_channel in client.private_channels:
        if isinstance(private_channel, discord.DMChannel):
            nome = private_channel.recipient.name
            if nome is None:
                break
            grupos.append(
                {
                    "nome": nome,
                    "id_grupo": str(private_channel.id),
                    "tipo": "\uE008"  # conversa privada
                })
        else:
            nome = private_channel.name
            if nome is None:
                nome = f"Sem nome ({private_channel.id})"
            grupos.append(
                {
                    "nome": nome,
                    "id_grupo": str(private_channel.id),
                    "tipo": "\uE012"  # grupo
                })
    return json.dumps(grupos)


@client.event
async def on_message(message):
    if message.guild:
        push_key = f'msglist.{message.guild.id}.{message.channel.id}'
    else:
        push_key = f'msglist.{message.channel.id}'
    if not servidor_liberado(push_key):
        print(f"(!) {push_key} nao foi liberado.")
        return
    mensagem = json.dumps(gerar_dict_mensagem(message))
    print(f"\n(i) id_mensagem Redis: {r.lpush(push_key, mensagem)}")


def gerar_dict_mensagem(message):
    todos_links = ""
    if message.attachments:
        for arquivo in message.attachments:
            todos_links = f'{todos_links}<a href="/proxy/imagem?url={urllib.parse.quote(str(arquivo).encode("utf8"), safe="")}">{arquivo.content_type}</a>'
        mensagem = f"{message.content}"
    else:
        mensagem = processar_mensagem(message.content)
    return {
            "nome_autor": processar_nome(message.author.display_name),
            "id_autor": message.author.id,
            "mensagem": mensagem,
            "id_mensagem": message.id,
            "html_externo": f"{todos_links}",
            "horas": processar_horas(message.created_at)
        }


def processar_nome(nome):
    return emoticon.converter(nome)


def processar_horas(horario):
    horario = horario - timedelta(hours=3)
    today = horario.now().date()
    yesterday = today - timedelta(days=1)

    if horario.date() == today:
        return f'Hoje às {horario.strftime("%H:%M")}'
    elif horario.date() == yesterday:
        return f'Ontem às {horario.strftime("%H:%M")}'
    else:
        return horario.strftime("%d/%m/%Y %H:%M")


def processar_mensagem(mensagem):
    return emoticon.converter(mensagem)


def carregar_discord():
    print("(i) Carregando Discord")
    client.run(token)


if __name__ == "__main__":
    carregar_discord()

