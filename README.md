# PyTube Downloader 🚀

Um web app moderno para download de vídeos do YouTube, construído para demonstrar a importância de **background workers** para uma experiência de usuário fluida e um backend escalável.

## ✨ O Projeto: Mais que um Simples Downloader

Já utilizou um site que trava completamente enquanto processa uma tarefa pesada? O PyTube Downloader foi criado para atacar exatamente esse problema. Ele usa o download de vídeos como uma **prova de conceito** para mostrar como aplicações web podem (e devem) realizar operações demoradas sem comprometer a responsividade da interface.

Para um **usuário**, é uma ferramenta simples e intuitiva: cole um link do YouTube, escolha o formato e baixe. A interface, com um design moderno de *glassmorphism*, é limpa e totalmente responsiva.

Mas por trás dos panos, este projeto demonstra:

  * **Arquitetura Assíncrona:** A capacidade de projetar sistemas que não bloqueiam o usuário, melhorando drasticamente a experiência e permitindo que o backend escale de forma independente.
  * **Domínio de Frontend e Backend:** Uma solução completa, desde a estilização com CSS puro e interatividade com JavaScript vanilla até a orquestração de tarefas complexas no servidor com Python.
  * **Foco em Performance:** Uma aplicação leve e rápida, evitando o excesso de dependências e frameworks pesados no frontend.

-----

## 🔧 Funcionalidades

  * **Busca de Vídeo Instantânea:** Cole uma URL do YouTube para ver os detalhes do vídeo.
  * **Seleção de Formato Flexível:** Escolha entre múltiplas resoluções de vídeo ou formatos de áudio.
  * **Feedback em Tempo Real:** Acompanhe o progresso do download com uma barra de progresso que é atualizada ao vivo, sem congelar a página.
  * **Interface Moderna:** Um design limpo e atraente com efeito de *glassmorphism* e totalmente adaptável a qualquer tamanho de tela.

-----

## 🏛️ Arquitetura e Conceitos Técnicos

O segredo para a responsividade da aplicação é o uso de **Celery** como um gerenciador de tarefas em segundo plano.

**O problema:** um download de vídeo pode levar de segundos a minutos. Se o servidor Flask tentasse fazer o download diretamente ao receber a requisição, o navegador do usuário ficaria "congelado", esperando uma resposta que só chegaria no final do processo.

**A solução:** desacoplar a requisição da execução da tarefa.

O fluxo funciona da seguinte maneira:

1.  **Frontend (JS):** O usuário clica em "Confirm Download". O JavaScript envia uma requisição `fetch` assíncrona para o endpoint `/download`.
2.  **Backend (Flask):** A rota `/download` **não** inicia o download. Em vez disso, ela agenda uma nova tarefa (`tasks.download_stream.delay(...)`) no Celery e retorna imediatamente um `taskId` para o frontend. A resposta é quase instantânea.
3.  **Broker (Redis):** O Celery usa o Redis como uma fila de mensagens. A tarefa agendada é colocada nessa fila.
4.  **Celery Worker:** Um processo separado (o *worker*) está constantemente monitorando a fila. Ele pega a tarefa e começa a executá-la (chama a função `download_stream` para baixar o vídeo).
5.  **Atualização de Progresso:** Durante o download, o worker utiliza o método `self.update_state()` para publicar o progresso (ex: `{ 'state': 'DOWNLOADING', 'percentage': 42 }`) no *backend* de resultados do Celery (também Redis).
6.  **Polling do Frontend:** Após receber o `taskId` (passo 2), o JavaScript começa a "perguntar" ao servidor sobre o status da tarefa a cada 500ms, fazendo requisições ao endpoint `/download/<task_id>/status`.
7.  **Status Check (Flask):** Esta rota consulta o backend de resultados do Celery e retorna o estado atual da tarefa para o frontend.
8.  **UI Dinâmica:** O JavaScript recebe o status e atualiza a barra de progresso na tela, proporcionando feedback em tempo real ao usuário.
9.  **Conclusão:** Quando o download termina, o worker atualiza o estado da tarefa para `SUCCESS` e armazena o caminho do arquivo final como resultado. Na próxima vez que o frontend perguntar, ele receberá o status de sucesso e redirecionará o usuário para o endpoint final de download, que serve o arquivo.

-----

## 🛠️ Como Executar o Projeto Localmente

### Pré-requisitos

  * Python 3.13
  * Redis (pode ser executado via Docker ou instalado localmente)
  * Ffmpeg
  * Git

### Passos para Instalação

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/edu292/pytube-downloader.git
    cd pytube-downloader
    ```

2.  **Crie e ative um ambiente virtual:**

    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS / Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicie o servidor Redis:**
    Se você tem o Redis instalado, simplesmente execute:

    ```bash
    redis-server
    ```

    Ou use Docker:

    ```bash
    docker run -d -p 6379:6379 redis
    ```

5.  **Inicie o Worker do Celery:**
    Abra um **novo terminal**, ative o ambiente virtual (`venv`) e execute:

    ```bash
    celery -A tasks.app worker
    ```

    > Para uma melhor compatibilidade talvez seja mais fácil rodar o celery em linux

    O worker se conectará ao Redis e aguardará por tarefas.

7.  **Inicie a aplicação Flask:**
    Abra um **terceiro terminal**, ative o ambiente virtual e execute:

    ```bash
    python app.py
    ```

8.  **Acesse a aplicação:**
    Abra seu navegador e acesse `http://127.0.0.1:5000`.

-----

## 📁 Estrutura do Código

  * `app.py`: O servidor web **Flask**. Responsável por servir o HTML e expor os endpoints da API para agendar tarefas e verificar seus status.
  * `tasks.py`: Define a aplicação **Celery** e as tarefas que serão executadas em segundo plano. É aqui que a lógica de download pesado reside.
  * `youtube_utils.py`: Um módulo utilitário que abstrai toda a interação com a biblioteca `yt-dlp`, responsável por extrair metadados e baixar os vídeos.
  * `templates/index.html`: A única página da aplicação. Utiliza o motor de templates **Jinja2** para renderizar os dados do vídeo e contém o **JavaScript vanilla** para a interatividade do frontend.
  * `static/css/style.css`: A folha de estilos. Utiliza variáveis CSS, Flexbox e Media Queries para criar uma interface moderna e responsiva sem depender de frameworks como Bootstrap ou Tailwind.
