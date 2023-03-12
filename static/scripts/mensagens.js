var delay = 1000;
var x = 0;

var desativar_timeout = false;
var enviar_mensagem = true;
var xhr_enviar_mensagem = new XMLHttpRequest();
  xhr_enviar_mensagem.onreadystatechange = function() {
    if (this.readyState === 4 && this.status === 200) {
        enviar_mensagem = true;
      if (this.responseText === "ok") {

        desativar_timeout = true;
        atualizarMensagens();
      } else {
        alert(this.responseText);
      }
      document.getElementById('mensagem').value = "";
    }
  };

xhr_enviar_mensagem.onerror = function(e){
    alert("Erro ao enviar mensagem. Renicie a página e tente novamente");
};
function descerSite() {
  window.scrollTo(0, document.body.scrollHeight + 1000);
}

function descerLista() {
  var objDiv = document.getElementById("mensagens");
  objDiv.scrollTop = objDiv.scrollHeight;
}


function enviarMensagem() {
  if (enviar_mensagem)
  {
      enviar_mensagem = false;
      var mensagem = document.getElementById('mensagem').value;
      xhr_enviar_mensagem.open('GET', caminho_enviar_mensagem + "/" + encodeURIComponent(mensagem) + "/" + (new Date()).getTime(), true);
      xhr_enviar_mensagem.send(null);

  }
  else
  {
     alert("Aguarde, enviando mensagem...");
  }
}

function atualizarMensagens() {
	var xhr_ler_mensagens = new XMLHttpRequest();
	xhr_ler_mensagens.onreadystatechange = function() {

	  if (this.readyState === 4 && this.status === 200) {
		var mensagens = eval('(' + this.responseText + ')');
		var objDiv = document.getElementById('mensagens');
		var estava_descido = objDiv.scrollHeight - objDiv.offsetHeight <= objDiv.scrollTop;
		if (mensagens.length) {
		  var lista = document.getElementById('mensagens');
		  for (var i = 0; i < mensagens.length; i++) {
			var mensagem = mensagens[i];
			var li = document.createElement('li');
			var a = document.createElement('a');
			a.href = '/usuario/' + mensagem.id_autor;
			a.className = 'nome';
			a.innerText = mensagem.nome_autor;
			var space = document.createTextNode('  ');
			a.appendChild(space);
			li.appendChild(a);
			var span = document.createElement('span');
			span.className = 'horas';
			span.innerText = mensagem.horas;
			li.appendChild(span);
			var p = document.createElement('p');
			p.className = 'mensagem';
			p.innerText = mensagem.mensagem;
			li.appendChild(p);
			li.innerHTML = li.innerHTML + mensagem.html_externo + "<br>";
			lista.appendChild(li);
		  }
		  if (estava_descido) {
			descerLista();
		  }
		}
	  }
	};

  xhr_ler_mensagens.open('GET', caminho_listar_mensagens + "/" + ((new Date()).getTime() + x), true);
  xhr_ler_mensagens.send(null);
  if (!desativar_timeout) {
  setTimeout(atualizarMensagens, delay);
  }
  desativar_timeout = false;
}

window.onload = function() {
  var objDiv = document.getElementById('mensagens');
  descerSite();
  descerLista();
  atualizarMensagens();

};
