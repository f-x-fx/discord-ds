# discord-ds
Cliente de discord leve otimizado para o nintendo dsi browser 

## Intuito
Quis fazer um cliente para dispositivos bem antigos, que muitas vezes tem um navegador de internet muito simples, como no caso do Nintendo DSi. Ele apenas tem 16mb ram e 133mhz, o que apesar de ser suficiente pra rodar jogos de ds e dsi que não tem muita diferença entre os dois, na questão de aplicativos como o Nintendo DSi Browser, ele entrega relativamente bem, porém por ser muito desatualizado não suporta as tecnologias mais recentes e o uso de javascript nele é limitado, por isso foi criado o Discord DS.

## Como funciona?
O jeito que funciona é meio gambiarra, mas foi o único jeito q consegui pra que não ficasse interferindo no processo um do outro. O app.py e discord_bot.py rodam independente, e eles fazem apenas a comunicação por redis. Exemplo, se quer pegar a lista de servidores, o app manda sinal pelo redis que quer pegar a lista e fica verificando se chegou a informação ao discord_bot.py. O discord bot fica verificando em segundo plano a cada 1 segundo se chegou alguma ação nova no redis e caso acontecer, ele retorna a resposta para uma chave no redis. O app detecta que houve mudança de resposta, e pega a resposta e limpa os conteúdos dela e assim sucessivamente.

## Requisitos
- Depende de um servidor que tenha suporte a WSGI e Flask (Python) hoje em dia você consegue pegar trial de azure ou gcloud com cartão temporário, ou usar always free do oracle (necessita cartão crédito físico)
- Versão mínima do Python: 3.8
- Depende de libraries, como flask, redis, e o discord self (no arquivo de requerimentos está todas as libraries)

## Isso é contra as políticas do Discord?
Sim infelizmente. Pode até dar banimento ao usuário que usar, por se tratar de um selfbot, mas o único usuário "eu" não foi banido até agora.

## Instalação
O código ainda tá muito bagunçado, porém é só colocar o token no discord_bot.py e depois tentar deployar o aplicativo flask, tem tutoriais na internet de como fazer isso.
