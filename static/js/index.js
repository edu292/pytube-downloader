class ProgressBar {
    #frameId = null;
    #currentPercentage = 0;
    #targetPercentage = 0;
    #body = null;
    #fill = null;
    #options = null;

    constructor(body, fill, options = {}) {
        this.#body = body;
        this.#fill = fill

        this.#options = {
            animationSpeed: 0.02,
            hiddenClass: 'hidden',
            indeterminateClass: 'progress-bar--indeterminate',
            ...options
        }
    }

    #animate = () => {
        if (this.#targetPercentage - this.#currentPercentage < 0.1) {
            this.#currentPercentage = this.#targetPercentage;
        } else {
            this.#currentPercentage += (this.#targetPercentage - this.#currentPercentage) * this.#options.animationSpeed;
        }

        this.#fill.style.width = `${this.#currentPercentage}%`;

        if (this.#currentPercentage < this.#targetPercentage) {
            this.#frameId = requestAnimationFrame(this.#animate);
        } else {
            this.#frameId = null;
        }
    }

    setPercentage(newTarget) {
        this.#targetPercentage = newTarget;

        if (!this.#frameId) {
            this.#frameId = requestAnimationFrame(this.#animate);
        }
        if (this.#body.classList.contains(this.#options.indeterminateClass)) {
            this.#body.classList.remove(this.#options.indeterminateClass);
        }
    }

    show() {
        this.#body.classList.add(this.#options.indeterminateClass);
        this.#body.classList.remove(this.#options.hiddenClass);
    }

    hide() {
        this.#body.classList.add(this.#options.hiddenClass)
        this.#fill.style.width = '0';
    }
}


const dropdownMenu = {
    button: document.getElementById('streams-dropdown-button'),
    body: document.getElementById('streams-dropdown-body'),
    tabs: document.getElementById('streams-tab-selector'),
    tabButtons: document.querySelectorAll('.dropdown-menu__tab-button'),
    pane: document.getElementById('streams-dropdown-pane'),
    paneContents: document.querySelectorAll('.dropdown-menu__pane-content'),
}

const progressBar = new ProgressBar(
    document.getElementById('progress-bar-body'),
    document.getElementById('progress-bar-fill')
)

const videoCardActions = document.getElementById('video-card-actions')
const confirmDownloadButton = document.getElementById('confirm-download');

const urlParams = new URLSearchParams(window.location.search);
const videoUrl = urlParams.get('url');

dropdownMenu.button.addEventListener('click', (evt) => {
    dropdownMenu.body.classList.toggle('hidden');
    evt.stopPropagation();
});

dropdownMenu.tabs.addEventListener('click', (evt) => {
    let clickedButton = evt.target;
    let selectedPane = document.getElementById(clickedButton.dataset.target);

    dropdownMenu.tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    clickedButton.classList.add('active');

    dropdownMenu.paneContents.forEach(content => {
        content.classList.add('hidden');
    })
    selectedPane.classList.remove('hidden');

    evt.stopPropagation()
});

dropdownMenu.pane.addEventListener('click', (evt) => {
    let selectedStreamButton = evt.target.closest("button");
    dropdownMenu.button.textContent = selectedStreamButton.innerText;

    confirmDownloadButton.removeAttribute('disabled');
    confirmDownloadButton.classList.add('button');
    confirmDownloadButton.classList.add('button--secondary');

    confirmDownloadButton.dataset.videoStreamId = selectedStreamButton.dataset.videoStreamId;
    confirmDownloadButton.dataset.audioStreamId = selectedStreamButton.dataset.audioStreamId;
});

confirmDownloadButton.addEventListener('click', function () {
    progressBar.show();
    videoCardActions.classList.add('hidden');

    const urlEndpoint = new URL('/download', window.location.origin);
    urlEndpoint.searchParams.append('url', videoUrl);

    const optionalParams = {
        'video-stream-id': confirmDownloadButton.dataset.videoStreamId,
        'audio-stream-id': confirmDownloadButton.dataset.audioStreamId,
    };

    for (const [key, value] of Object.entries(optionalParams)) {
        if (value && value !== 'null') {
            urlEndpoint.searchParams.append(key, value);
        }
    }

    scheduleWorker(urlEndpoint);
});

window.addEventListener('click', function () {
    dropdownMenu.body.classList.add('hidden');
});


async function scheduleWorker(urlEndpoint) {
    const response = await fetch(urlEndpoint);
    const data = await response.json();
    const taskId = data.taskId;

    pollStatus(taskId);
}


async function pollStatus(taskId) {
    const response = await fetch(`/download/${taskId}/status`);
    const data = await response.json();

    if (data.state === 'SUCCESS') {
        progressBar.setPercentage(100);
        window.location.assign(`download/${taskId}`);
        setTimeout(() => {
            progressBar.hide();
            videoCardActions.classList.remove('hidden');
        }, 800);
    } else {
        if (data.state === 'DOWNLOADING') {
            progressBar.setPercentage(data.percentage);
        }

        setTimeout(() => pollStatus(taskId), 1000);
    }
}