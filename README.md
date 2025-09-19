# PyTube Downloader 🚀

Um web app moderno para download de vídeos do YouTube, containerizado com Docker e pronto para produção, construído para demonstrar a importância de **background workers** para uma experiência de usuário fluida e um backend escalável.

## ✨ O Projeto: Mais que um Simples Downloader

Já utilizou um site que trava completamente enquanto processa uma tarefa pesada? O PyTube Downloader foi criado para atacar exatamente esse problema. Ele usa o download de vídeos como uma **prova de conceito** para mostrar como aplicações web podem (e devem) realizar operações demoradas sem comprometer a responsividade da interface.

Para um **usuário**, é uma ferramenta simples e intuitiva: cole um link do YouTube, escolha o formato e baixe. A interface, com um design moderno de *glassmorphism*, é limpa e totalmente responsiva.

Mas em sua implementação, este projeto demonstra:
  * **Arquitetura Assíncrona:** A capacidade de projetar sistemas que não bloqueiam o usuário, melhorando drasticamente a experiência e permitindo que o backend escale de forma independente.
  * **Domínio de Frontend e Backend:** Uma solução completa, desde a estilização com CSS puro e interatividade com JavaScript vanilla até a orquestração de tarefas complexas no servidor com Python.
  * **Foco em Performance:** Uma aplicação leve e rápida, evitando o excesso de dependências e frameworks pesados no frontend.
  * **Práticas de DevOps:** O uso de **Docker** e **Docker Compose** para criar um ambiente de desenvolvimento e produção consistente, confiável e facilmente replicável com um único comando.

-----

## 🔧 Funcionalidades

  * **Busca de Vídeo Instantânea:** Cole uma URL do YouTube para ver os detalhes do vídeo.
  * **Seleção de Formato Flexível:** Escolha entre múltiplas resoluções de vídeo ou formatos de áudio.
  * **Feedback em Tempo Real:** Acompanhe o progresso do download com uma barra de progresso que é atualizada ao vivo, sem congelar a página.
  * **Interface Moderna:** Um design limpo e atraente com efeito de *glassmorphism* e totalmente adaptável a qualquer tamanho de tela.

-----

## 🏛️ Arquitetura e Conceitos Técnicos

### O Fluxo Assíncrono com Celery

O segredo para a responsividade da aplicação é o uso de **Celery** como um gerenciador de tarefas em segundo plano.

**O problema:** um download de vídeo pode levar de segundos a minutos. Se o servidor Flask tentasse fazer o download diretamente ao receber a requisição, o navegador do usuário ficaria "congelado", esperando uma resposta que só chegaria no final do processo.

**A solução:** desacoplar a requisição da execução da tarefa.

O fluxo funciona da seguinte maneira:

1.  **Frontend (JS):** O usuário clica em "Confirm Download". O JavaScript envia uma requisição `fetch` assíncrona para o endpoint `/download`.
2.  **Backend (Flask):** A rota `/download` **não** inicia o download. Em vez disso, ela agenda uma nova tarefa (`tasks.download_stream.delay(...)`) no Celery e retorna imediatamente um `taskId` para o frontend. A resposta é quase instantânea.
3.  **Broker (Redis):** O Celery usa o Redis como uma fila de mensagens. A tarefa agendada é colocada nessa fila.
4.  **Celery Worker:** Um processo separado (o *worker*) está constantemente monitorando a fila. Ele pega a tarefa e começa a executá-la (chama a função `download_stream` para baixar o vídeo).
5.  **Atualização de Progresso:** Durante o download, o worker utiliza o método `self.update_state()` para publicar o progresso (ex: `{ 'state': 'DOWNLOADING', 'percentage': 42 }`) no *backend* de resultados do Celery (também Redis).
6.  **Polling do Frontend:** Após receber o `taskId` (passo 2), o JavaScript começa a "perguntar" ao servidor sobre o status da tarefa a cada 1000ms, fazendo requisições ao endpoint `/download/<task_id>/status`.
7.  **Status Check (Flask):** Esta rota consulta o backend de resultados do Celery e retorna o estado atual da tarefa para o frontend.
8.  **UI Dinâmica:** O JavaScript recebe o status e atualiza a barra de progresso na tela, proporcionando feedback em tempo real ao usuário.
9.  **Conclusão:** Quando o download termina, o worker atualiza o estado da tarefa para `SUCCESS` e armazena o caminho do arquivo final como resultado. Na próxima vez que o frontend perguntar, ele receberá o status de sucesso e redirecionará o usuário para o endpoint final de download, que serve o arquivo.

### O Desafio do Pareamento de Streams

Um desafio técnico significativo do projeto é traduzir a enorme quantidade de formatos brutos que o YouTube oferece em uma lista de opções simples e funcionais para o usuário.

  * **O Problema:** Para qualquer vídeo em alta qualidade, o YouTube não oferece um arquivo único com vídeo e áudio. Em vez disso, ele disponibiliza dezenas de *streams* separadas: múltiplos arquivos apenas de vídeo (em codecs como `VP9` dentro de um container `.webm`, ou `AVC1` em `.mp4`) e múltiplos arquivos apenas de áudio (em codecs como `Opus` ou `AAC`).

  * **A Complexidade:** O desafio é duplo:

    1.  **Filtragem:** Além de somente opções de video e audio o Youtube ainda oferece múltiplos outros tipos de arquivo como storyboards e de metadados do vídeo.
    2.  **Compatibilidade:** Nem todo codec de vídeo pode ser combinado com qualquer codec de áudio. Tentar mesclar, por exemplo, um vídeo `.webm` com um áudio `.m4a` (AAC) pode causar erros no `ffmpeg`.

  * **A Solução (`youtube_utils.py`):** Foi implementado um algoritmo customizado que:

    1.  Separa e filtra as listas de vídeo e áudio, ordenando-as por qualidade.
    2.  Executa uma lógica de pareamento inteligente, que escalona o pareamento das *streams* de vídeo e audio baseado na sua qualidade e compatibilidade. De forma que a resolução do video, qualidade do audio e tamanho dos arquivos sejam coerentes com o que o usuário selecionar.
    3.  Calcula o tamanho final combinado do arquivo para informar ao usuário.

Isso abstrai toda a complexidade, transformando uma lista de mais de 50 opções técnicas confusas em um menu de seleção claro e funcional, como "1080p" ou "720p".


-----

### Pronto para Produção: Docker, Gunicorn & WhiteNoise

Este projeto não é apenas um protótipo; ele é construído sobre uma base sólida para implantação em produção.

  * **Docker & Docker Compose:** A aplicação inteira é orquestrada pelo Docker Compose. Isso define, em código, uma arquitetura multi-container que separa as responsabilidades:

      * `web`: Um container para a aplicação Flask, servida por um servidor WSGI robusto.
      * `worker`: Um container dedicado para o Celery, que pode ser escalado de forma independente para lidar com mais downloads simultâneos.
      * `redis`: Um container para o broker de mensagens e backend de resultados.
        Isso garante que o ambiente de desenvolvimento seja idêntico ao de produção, eliminando o clássico "mas na minha máquina funciona".

  * **Gunicorn (WSGI Server):** O servidor de desenvolvimento do Flask não foi feito para produção. O **Gunicorn** atua como um servidor WSGI de nível de produção, capaz de gerenciar múltiplos processos para lidar com requisições concorrentes, garantindo performance e estabilidade.

  * **WhiteNoise:** O Gunicorn é excelente para rodar a lógica Python, mas não é otimizado para servir arquivos estáticos (CSS, JS). O **WhiteNoise** se integra à aplicação Flask para servir esses arquivos de forma eficiente, com cache e compressão adequados, uma prática recomendada para produção.

-----

## 🛠️ Tecnologias Utilizadas

| Frontend | Backend | DevOps & Infraestrutura |
| :--- | :--- | :--- |
| HTML5 | Python 3.13 | Docker & Docker Compose |
| CSS3 (Vanilla) | Flask | Gunicorn (WSGI Server) |
| JavaScript (Vanilla) | Celery | Redis |
| Glassmorphism (UI Design) | yt-dlp | WhiteNoise |
| Jinja2 | FFmpeg | |

-----

## 🛠️ Como Executar o Projeto Localmente

### Pré-requisitos

  * Docker
  * Git

### Passos para Instalação

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/edu292/pytube-downloader.git
    cd pytube-downloader
    ```

2.  **Suba os containers:**

    ```bash
    docker compose up -d --build
    ```
    Isso iniciará:
    * O serviço `web` (Flask + Gunicorn) na porta `80`.
    * O serviço `worker` (Celery).
    * O serviço `redis` (Broker + Result Backend).

### Uso

Após a conclusão do passo anterior, a aplicação estará pronta para uso.

1.  Abra seu navegador e acesse:
    ```
    http://localhost
    ```
    ou
    ```
    http://127.0.0.1
    ```
2.  Cole uma URL de um vídeo do YouTube no campo de busca e clique em "Search".
3.  Escolha o formato de vídeo ou áudio desejado e clique em "Confirm Download".

Para parar todos os serviços, execute o seguinte comando no diretório do projeto:
```bash
docker-compose down -v
```

-----

## 📁 Estrutura do Código

```
.
├── docker-compose.yaml   # Orquestra todos os serviços
├── Dockerfile            # Define a imagem da aplicação Python
├── requirements.txt      # Dependências Python
└── src
    ├── app.py            # Servidor Flask (endpoints da API)
    ├── tasks.py          # Tarefas do Celery (lógica de download)
    ├── youtube_utils.py  # Módulo de interação com yt-dlp
    ├── static
    │   ├── css
    │   │   └── style.css # Estilos e customização da página
    │   └── js
    │       └── index.js  # Interatividade e comunicação com o servidor
    └── templates
        └── index.html    # Código de estruturação da página principal
```

-----
