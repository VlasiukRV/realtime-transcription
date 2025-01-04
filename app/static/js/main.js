const serverIp = window.location.hostname;

const serviceMessageOutput = document.getElementById("service-message-output")
const textDisplay = document.getElementById('output');
const pauseButton = document.getElementById('pause-btn');
const clearButton = document.getElementById('clear-btn');
const copyButton = document.getElementById('copy-btn');

let isPaused = false;

const toggleThemeBtn = document.getElementById('toggle-theme-btn');

let lang = '';
let socket = undefined;
let reconnectInterval;

async function connectWebSocket() {
    if (lang === "") {
        return
    }
    serviceMessageOutput.innerHTML = `Connecting to ${serverIp}......`;

    // Create a new WebSocket connection
    socket = new WebSocket(`ws://${serverIp}:8000/ws/transcribe/${lang}`);

    socket.onmessage = function (event) {
        let message = event.data;
        if (message.startsWith("Service Message:")) {
            serviceMessageOutput.innerHTML += `<p><strong>Service status:</strong> ${message.slice(17)}</p>`;
        } else {
            addText(event.data);
        }
    };

    socket.onopen = function () {
        console.log(`WebSocket connected for language: ${lang}`);
        serviceMessageOutput.innerHTML = `Connected to WebSocket for language: ${lang}`;

        // If the connection is restored, stop the reconnection checks
        clearInterval(reconnectInterval);
    };

    socket.onclose = function () {
        console.log("Disconnected from WebSocket");
        serviceMessageOutput.innerHTML = `Disconnected from WebSocket`;

        // Start checking the connection every 5 seconds
        reconnectInterval = setInterval(checkConnection, 5000);
    };

    socket.onerror = function (error) {
        console.log("WebSocket Error:", error);
        serviceMessageOutput.innerHTML = `Error: ${error}`;
    };
}

function checkConnection() {
    console.log("Checking WebSocket connection...");

    // If the WebSocket connection is closed or in the process of closing, try to reconnect
    if (socket.readyState === WebSocket.CLOSED || socket.readyState === WebSocket.CLOSING) {
        console.log("Attempting to reconnect...");
        connectWebSocket();  // Reconnect
    }
}

// Проверка сохранённой темы в localStorage
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
    toggleThemeBtn.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
}

// Переключение темы
toggleThemeBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    // Установить новую тему
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Обновить текст кнопки
    toggleThemeBtn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
});

// Добавление текста с интервалом
function addText(text) {
    if (!isPaused) {
        const newText = document.createElement('p');
        newText.textContent = text;
        textDisplay.appendChild(newText);

        // Автопрокрутка вниз
        textDisplay.scrollTop = textDisplay.scrollHeight;

    }
}

// Обработчик кнопки паузы
pauseButton.addEventListener('click', () => {
    isPaused = !isPaused;
    pauseButton.textContent = isPaused ? "▶️" : "⏯";
});

// Обработчик кнопки очистки
clearButton.addEventListener('click', () => {
    textDisplay.innerHTML = '';
});

// Обработчик кнопки копирования
// copyButton.addEventListener('click', () => {
//     const text = Array.from(textDisplay.children)
//         .map(child => child.textContent)
//         .join('\n');
//     navigator.clipboard.writeText(text).then(() => {
//         alert('Текст скопирован!');
//     });
// });

async function changeLanguage(event) {
    lang = event.target.value;

        try {
            const response = await fetch("/api/addLang", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({lang: lang}) // Отправляем JSON с языком
            });

            if (response.ok) {

                if (socket && socket instanceof WebSocket) {
                    socket.close(1000, 'Обычное завершение');
                }

                await connectWebSocket();
                const result = await response.json();
                console.log(result.message);
            } else {
                const error = await response.json();
                console.log(`Error: ${error.detail}`);
            }
        } catch (error) {
            console.error("Error:", error);
        }
}

window.onload = function () {
    const languageSelect = document.getElementById("languageSelect");

    languageSelect.addEventListener("change", changeLanguage);

};
