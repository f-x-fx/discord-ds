       var xhr = new XMLHttpRequest();
      xhr.open('GET', '/lista/servidores', true);
      xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
        window.scrollTo(0, document.body.scrollHeight + 1000);
          var servidores = eval(xhr.responseText);
          var listaServidores = document.getElementById('servidores');
          for (var i = 0; i < servidores.length; i++) {

              var servidor = servidores[i];
              var li = document.createElement('li');
              li.className = 'listsv'
              var a = document.createElement('a');
              a.textContent = servidor.nome;
              a.href = '/canais_de_texto/' + (servidor.id_servidor);
              a.className = 'abutton'
              li.appendChild(a);
              var hr = document.createElement('hr');
              listaServidores.appendChild(li);
              listaServidores.appendChild(hr);
          }
        }
      };
      xhr.send();
      window.scrollTo(0, document.body.scrollHeight + 1000);