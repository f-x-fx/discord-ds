       var xhr = new XMLHttpRequest();
      xhr.open('GET', '/lista/canais_texto/' + id_canal_texto, true);
      xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
        window.scrollTo(0, document.body.scrollHeight + 1000);
          var canais = eval(xhr.responseText);
          var listaCanais = document.getElementById('canais_de_texto');
          for (var i = 0; i < canais.length; i++) {

              var canal = canais[i];
              var li = document.createElement('li');
              li.className = 'listsv'
              var a = document.createElement('a');
              a.textContent = " # " + canal.nome;
              a.href = '/mensagens/' + id_canal_texto + "/" + canal.id_canal  ;
              a.className = 'abutton'
              li.appendChild(a);
              var hr = document.createElement('hr');
              listaCanais.appendChild(li);
              listaCanais.appendChild(hr);
          }
        }
      };
      xhr.send();
      window.scrollTo(0, document.body.scrollHeight + 1000);