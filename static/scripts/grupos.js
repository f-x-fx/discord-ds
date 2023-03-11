       var xhr = new XMLHttpRequest();
      xhr.open('GET', '/lista/grupos', true);
      xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
        window.scrollTo(0, document.body.scrollHeight + 1000);
          var servidores = eval(xhr.responseText);
          var listaServidores = document.getElementById('grupos');
          for (var i = 0; i < servidores.length; i++) {

              var servidor = servidores[i];
              var li = document.createElement('li');
              li.className = 'listsv'
              var a = document.createElement('a');
              a.textContent = servidor.nome;
              a.href = '/mensagens/' + (servidor.id_grupo);
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