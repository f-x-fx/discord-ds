import io, logging, json, redis, random, string, requests
from flask import Flask, render_template, abort, redirect, url_for,  request, send_file
from flask.logging import default_handler
from flask_httpauth import HTTPBasicAuth
from PIL import Image
import subprocess as sp
# Conecta ao Redis, se houver falha, o aplicativo web não irá funcionar.
r = redis.Redis(host="localhost", port=6379, db=0)
# Logging caso necessite
root = logging.getLogger()
root.addHandler(default_handler)
# Gerar código aleatório para sessão
app = Flask(__name__)
app.config["SECRET_KEY"] = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation) for i in range(32))
# variáveis
extProc = None
bot_thread = None
didnt_start = True
senha_app = "" # Senha para não entrarem no seu Discord ao acessar a página.
auth = HTTPBasicAuth()
usuarios = {
    "admin": "senha",
}
ip_liberados = ["127.0.0.1"]
max_tentativas = 3
def liberar_ip(ip):
    ip_liberados.append(ip)


@auth.verify_password
def verificar_senha(usuario, senha):
    if pegar_ip() in ip_liberados:
        return usuario
    if usuario in usuarios and \
            usuarios.get(usuario) == senha:
        if not pegar_ip() in ip_liberados:
            liberar_ip(pegar_ip())

        return usuario
    else:
        adicionar_ip(pegar_ip())
        return None


@app.route("/")
@auth.login_required
def index():
    return redirect(url_for('servidores_html'))


def pegar_ip():
    headers_list = request.headers.getlist("HTTP_X_FORWARDED_FOR")
    http_x_real_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    ip_address = headers_list[0] if headers_list else http_x_real_ip
    return ip_address


@app.route("/servidores")
@auth.login_required
def servidores_html():
    return render_template("servidores.html", servidores=json.loads(api_servidores()))


@app.route("/reniciar")
@auth.login_required
def reniciar():
         return reniciar_discord()


@app.route("/grupos")
@auth.login_required
def grupos_html():
         return render_template("grupos.html", grupos=json.loads(api_grupos()))


@app.route("/canais_de_texto/<servidor>")
@auth.login_required
def canais_texto_html(servidor):
         return render_template("canais.html", servidor=f"{servidor}", canais_de_texto=json.loads(api_canais_texto(servidor)))


@app.route("/mensagens/<canal>")
@auth.login_required
def mensagens_dm_html(canal):
         return gerar_html_mensagens(None,canal)


@app.route("/mensagens/<servidor>/<canal>")
@auth.login_required
def mensagens_html(servidor, canal):
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


def api_servidores():
    print(r.lpush("list_acoes", json.dumps({"acao": "carregar_lista_servidor"})))
    lista = r.get("lista_servidores")
    while not lista:
        lista = r.get("lista_servidores")
    r.delete("lista_servidores")
    return lista


@app.route("/enviar/mensagem/<canal>/<conteudo>/<horario>")
@auth.login_required
def enviar_mensagem(canal, conteudo, horario):
    print(horario)
    return api_enviar_mensagem(None, canal, conteudo, horario)


@app.route("/enviar/mensagem/<servidor>/<canal>/<conteudo>/<horario>")
@auth.login_required
def enviar_mensagem_servidor(servidor, canal, conteudo, horario):
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

ip_ban_list = {'191.123.123.21': 3}


@app.before_request
def detectar_ip():
    ip = pegar_ip()
    if ip in ip_ban_list and ip_ban_list[ip] > max_tentativas:  # verifica se o valor é maior que 2
        abort(403)  # bloqueia o acesso


def adicionar_ip(ip):

    if ip in ip_ban_list:  # verifica se o IP já está no dicionário
        ip_ban_list[ip] += 1  # incrementa o valor em 1
    else:  # se não estiver no dicionário
        ip_ban_list[ip] = 1  # adiciona com o valor 1
    print(ip_ban_list)
    print(ip + " adicionado")


@app.errorhandler(404)
@auth.login_required
def pagina_nao_encontrada(e):
    return e


@app.route('/ip')
@auth.login_required
def retornar_ip():
    return f"IP: {pegar_ip()} <br><br> {str(request.headers)}"


@app.route('/proxy/imagem')
@auth.login_required
def baixar_imagem():
         # obter a URL da imagem a partir do parâmetro de consulta 'url'
    url_da_imagem = request.args.get('url')

    # fazer a solicitação HTTP para obter a imagem
    resposta = requests.get(url_da_imagem)

    # verificar se a solicitação foi bem-sucedida
    if resposta.status_code == 200:
        # obter o conteúdo da imagem a partir da resposta HTTP
        conteudo_da_imagem = resposta.content

        # abrir a imagem usando a biblioteca Pillow
        imagem = Image.open(io.BytesIO(conteudo_da_imagem))
        if imagem.mode == 'RGBA':
            imagem = imagem.convert('RGB')
        # redimensionar a imagem se a altura for maior que 600 pixels
        if imagem.height > 530:
            width = int(imagem.width * (530 / imagem.height))
            height = 530
            imagem = imagem.resize((width, height))

        # enviar a imagem como uma resposta do Flask
        saida = io.BytesIO()
        imagem.save(saida, format='JPEG')
        saida.seek(0)
        return send_file(saida, mimetype='image/jpeg')

    # se a solicitação não foi bem-sucedida, retornar uma mensagem de erro
    return 'Erro ao baixar imagem', 400

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

@app.route("/lista/mensagens/<canal>/<horario>", methods=["GET"])
@auth.login_required
def get_messages(canal, horario):
    print(horario)
    return pegar_mensagens(None, canal)

@app.route("/lista/mensagens/<servidor>/<canal>/<horario>", methods=["GET"])
@auth.login_required
def get_server_messages(servidor, canal, horario):
    print(horario)
    return pegar_mensagens(servidor, canal)

# Pega mensagens penndentes do servidor.
# Logging foi desativado pois não é necessário.
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
        # print(f"(i) Mensagem lida: {mensagem_decodificada}")
    # Imprime as mensagens lidas
    if mensagens:
        # print(f"(i) Mensagens lidas: {mensagens}")
        return mensagens
    else:
        # print("(!) Nenhuma mensagem foi encontrada")
        return mensagens
        
if not iniciar_discord():
    print("discord iniciado com sucesso")
else:
    print("erro ao iniciar discord")