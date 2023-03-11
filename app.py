import io
import logging

from flask import Flask, render_template, request, Response, redirect, url_for,  request, send_file

from PIL import Image
import json
import redis
import random
import string
import subprocess as sp
import requests
r = redis.Redis(host="localhost", port=6379, db=0)

from flask.logging import default_handler

root = logging.getLogger()
root.addHandler(default_handler)

app = Flask(__name__)
secret = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation) for i in range(32))
secret = 'fds'
print(secret)
app.config["SECRET_KEY"] = secret
from flask import session
extProc = None
bot_thread = None
didnt_start = True
senha_app = ""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/servidores")
def servidores_html():
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return render_template("servidores.html", servidores=json.loads(api_servidores()))

@app.route("/reniciar")
def reniciar():
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return reniciar_discord()

@app.route("/grupos")
def grupos_html():
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return render_template("grupos.html", grupos=json.loads(api_grupos()))

@app.route("/canais_de_texto/<servidor>")
def canais_texto_html(servidor):
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return render_template("canais.html", servidor=f"{servidor}", canais_de_texto=json.loads(api_canais_texto(servidor)))

@app.route("/mensagens/<canal>")
def mensagens_dm_html(canal):
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return gerar_html_mensagens(None,canal)


@app.route("/mensagens/<servidor>/<canal>")
def mensagens_html(servidor, canal):
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return gerar_html_mensagens(servidor,canal)


def gerar_html_mensagens(servidor, canal):

    print("====Processo de Capturar Mensagens====")
    # carrega a lista de mensagens
    if servidor:
        chave_historico = f"historico.{servidor}.{canal}"
    else:
        chave_historico = f"historico.{canal}"
    print(chave_historico)
    # deleta chave
    print(f" (i) Histórico: {r.delete(chave_historico)}")

    if servidor:
        print(f' (i) Carregar lista de mensagens: '
              f'{r.lpush("list_acoes", json.dumps({"acao": "carregar_historico", "servidor": f"{servidor}", "canal": f"{canal}"}))}')

    else:
        print(f' (i) Carregar lista de mensagens: '
              f'{r.lpush("list_acoes", json.dumps({"acao": "carregar_historico", "canal": f"{canal}"}))}')

    historico = r.get(chave_historico)
    while not historico:
        historico = r.get(chave_historico)
    print(" (i) Carregou histórico")
    # código para liberar a lista de mensagens
    if servidor:
        id_lista_mensagens = f'msglist.{servidor}.{canal}'
    else:
        id_lista_mensagens = f'msglist.{canal}'
    print(f' (i) Liberar lista de mensagens: '
          f'{r.lpush("list_acoes", json.dumps({"acao": "liberar_carregar_mensagens", "conteudo": f"{id_lista_mensagens}"}))}')

    chave_lista = f'carregar_mensagens_liberada.{id_lista_mensagens}'
    lista = r.get(chave_lista)
    while not lista:
        lista = r.get(chave_lista)
    print(" (i) Carregou lista")
    r.delete(id_lista_mensagens)
    if servidor:
        return render_template("mensagens.html", servidor=servidor, canal=canal, mensagens=json.loads(historico))
    else:
        return render_template("mensagens.html", servidor="null", canal=canal, mensagens=json.loads(historico))

@app.route("/iniciar")
def iniciar():
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    global didnt_start
    if didnt_start:
        didnt_start = False
        return {
            "status": r.lpush("list_acoes", json.dumps({"acao": "carregar_discord"}))
        }
    return "ja comecou"


@app.route("/client")
def client():
    return r.get("nome")


@app.route("/lista/servidores")
def servidores():
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return api_servidores()

def api_servidores():
    print(r.lpush("list_acoes", json.dumps({"acao": "carregar_lista_servidor"})))
    lista = r.get("lista_servidores")
    while not lista:
        lista = r.get("lista_servidores")
    r.delete("lista_servidores")
    return lista

@app.route("/lista/grupos")
def grupos():
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return grupos


@app.route("/enviar/mensagem/<canal>/<conteudo>/<horario>")
def enviar_mensagem(canal, conteudo, horario):
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    print(horario)
    return api_enviar_mensagem(None, canal, conteudo, horario)


@app.route("/enviar/mensagem/<servidor>/<canal>/<conteudo>/<horario>")
def enviar_mensagem_servidor(servidor, canal, conteudo, horario):
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    print(horario)
    return api_enviar_mensagem(servidor, canal, conteudo, horario)


def api_enviar_mensagem(servidor, canal, conteudo, horario):
    if servidor:
        print(r.lpush("list_acoes", json.dumps(
            {
                "acao": "enviar_mensagem",
                "servidor": f"{servidor}",
                "canal": f"{canal}",
                "conteudo": f"{conteudo}",
                "horario": f"{horario}"
            }
        )))
        chave_enviar_mensagem = f"mensagem_enviada.{servidor}.{canal}.{horario}"
    else:
        print(r.lpush("list_acoes", json.dumps(
            {
                "acao": "enviar_mensagem",
                "canal": f"{canal}",
                "conteudo": f"{conteudo}",
                "horario": f"{horario}"
            }
        )))
        chave_enviar_mensagem = f"mensagem_enviada.{canal}.{horario}"
    status = r.get(chave_enviar_mensagem)
    while not status:
        status = r.get(chave_enviar_mensagem)

    r.delete(chave_enviar_mensagem)
    return status
def api_grupos():
    print(r.lpush("list_acoes", json.dumps({"acao": "carregar_lista_grupos_dm"})))
    lista = r.get("lista_grupos_dm")
    while not lista:
        lista = r.get("lista_grupos_dm")
    r.delete("lista_grupos_dm")
    return lista

def iniciar_discord():
    r.flushall()
    global extProc
    extProc = sp.Popen(['python3', 'discord_bot.py'])  # runs myPyScript.py
    print(extProc)
    return sp.Popen.poll(extProc)


def reniciar_discord():
    try:
        global extProc
        sp.Popen.terminate(extProc)
        print (f"Discord foi terminado: {sp.Popen.poll(extProc)}")  # closes the process

        if iniciar_discord():
            return "Não foi possivel reniciar o Discord."
        else:
            return redirect(url_for('index'))
    except Exception as e:
        return f"{e}"



@app.route('/proxy/imagem')
def download_image():
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    # obter a URL da imagem a partir do parâmetro de consulta 'url'
    image_url = request.args.get('url')

    # fazer a solicitação HTTP para obter a imagem
    response = requests.get(image_url)

    # verificar se a solicitação foi bem-sucedida
    if response.status_code == 200:
        # obter o conteúdo da imagem a partir da resposta HTTP
        image_content = response.content

        # abrir a imagem usando a biblioteca Pillow
        image = Image.open(io.BytesIO(image_content))
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        # redimensionar a imagem se a altura for maior que 600 pixels
        if image.height > 530:
            width = int(image.width * (530 / image.height))
            height = 530
            image = image.resize((width, height))

        # enviar a imagem como uma resposta do Flask
        output = io.BytesIO()
        image.save(output, format='JPEG')
        output.seek(0)
        return send_file(output, mimetype='image/jpeg')

    # se a solicitação não foi bem-sucedida, retornar uma mensagem de erro
    return 'Erro ao baixar imagem', 400


@app.route("/lista/canais_texto/<servidor>")
def canais_texto(servidor):
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    return api_canais_texto(servidor)

def api_canais_texto(servidor):
    id_servidor = servidor
    print(
        r.lpush(
            "list_acoes",
            json.dumps({"acao": "carregar_lista_canais_texto", "conteudo": str(id_servidor)}),
        )
    )
    lista = r.get(f"lista_canais_texto.{id_servidor}")
    while not lista:
        lista = r.get(f"lista_canais_texto.{id_servidor}")
    r.delete(f"lista_canais_texto.{id_servidor}")
    return lista


@app.route("/status")
def status():
    if "authenticated" in session:
        if session["authenticated"]:
            return '0'
    global didnt_start
    global senha_app
    senha = request.args.get("senha")
    print(senha, senha_app)
    if senha != senha_app:
        print("senha invalida")
        return Response(status=200)
    else:
        session["authenticated"] = True
        print("autenticado")
        return '0'


@app.route("/lista/mensagens/<canal>/<horario>", methods=["GET"])
def get_messages(canal, horario):
    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    print(horario)
    return pegar_mensagens(None, canal)

@app.route("/lista/mensagens/<servidor>/<canal>/<horario>", methods=["GET"])
def get_server_messages(servidor, canal, horario):

    if "authenticated" not in session or not session["authenticated"]:
        print("not authenticated")
        return Response(status=401)
    print(horario)
    return pegar_mensagens(servidor, canal)

def pegar_mensagens(servidor, canal):
    mensagens = []
    if servidor:
        id_lista = f"msglist.{servidor}.{canal}"
    else:
        id_lista = f"msglist.{canal}"

    while True:
        mensagem = r.rpop(id_lista)
        if mensagem is None:
            break
        mensagem_decodificada = mensagem.decode("utf-8")
        mensagens.append(json.loads(mensagem_decodificada))
        print(f"Mensagem lida: {mensagem_decodificada}")
    # Imprime as mensagens lidas
    if mensagens:
        print(f"Mensagens lidas: {mensagens}")
        return mensagens
    else:
        print("Nenhuma mensagem encontrada")
        return mensagens

if __name__ == "__main__":
    if not iniciar_discord():
        print("discord iniciado com sucesso")
    app.run(host='0.0.0.0', port=80)