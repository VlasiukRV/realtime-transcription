( ()=> {
    // Get the server hostname from the current window (useful for local/dev)
    const serverIp = window.location.hostname;

    // Cache important DOM elements
    const $serviceMessageOutput = $("#service-message-output");
    const $serviceMessageOutputIcon = $("#service-message-output-icon");
    const $textDisplay = $('#output');
    const $side_panel = $('#side-panel');
    const $langSelect = $('#targetLang');
    const $toggleSidePanel = $('#toggle-side-panel')

    // State variables
    let socket = null;
    let reconnectInterval = null;
    let isPaused = false;
    let isPlaying = false;
    let wakeLock = null;

    // ------------------ THEME ------------------

    // Load the theme preference from localStorage
    function setThemeFromLocalStorage() {
        if (localStorage.getItem('theme') === 'dark') {
            document.documentElement.classList.add('dark');
        }
    }

    // Toggle between dark and light themes
    function toggleTheme() {
        document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme',
            document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    }

    // ------------------ AUDIO ------------------

    // Play audio from a base64 string
    function playAudio(base64, onEnd) {
        if (isPlaying) return console.log("Audio already playing.");
        isPlaying = true;

        const audioBlob = new Blob(
            [new Uint8Array(atob(base64).split("").map(c => c.charCodeAt(0)))],
            {type: 'audio/mp3'}
        );
        const audio = new Audio(URL.createObjectURL(audioBlob));

        audio.play().catch(err => console.error("Play error:", err));
        audio.onended = () => {
            isPlaying = false;
            if (onEnd) onEnd();
        };
    }

    // Wait for the next element with delay (used for chaining audio)
    async function getNextAudioElement($el) {
        let $next = $el.next();
        if ($next.length) return $next;

        await new Promise(r => setTimeout(r, 500));
        return getNextAudioElement($el);
    }

    // Play audio recursively from elements that have data-audio-content
    async function playAudioFromElement($el) {
        const audioContent = $el.attr('data-audio-content');
        if (!audioContent) return;
        const $icon = $el.children('span');

        $icon.addClass('opacity-50 pointer-events-none');
        playAudio(audioContent, async () => {
            $el.removeAttr('data-audio-content')
            $icon.text('✔');
            await playAudioFromElement(await getNextAudioElement($el));
        });
    }

    // ------------------ WEBSOCKET ------------------

    // Connect to the WebSocket server with the selected language
    function connectWebSocket(lang) {
        if (!lang) return;
        $serviceMessageOutput.text(`Connecting to ${serverIp}...`);

        socket = new WebSocket(`ws://${serverIp}:8000/ws/transcribe/${lang}`);

        socket.onopen = () => {
            $serviceMessageOutput.text(`Connected: ${lang}`);
            $serviceMessageOutputIcon.addClass('blinking');
            clearInterval(reconnectInterval);
        };

        socket.onclose = () => {
            $serviceMessageOutput.text('Disconnected');
            $serviceMessageOutputIcon.removeClass('blinking');
            reconnectInterval = setInterval(() => {
                if (!socket || socket.readyState >= 2)
                    connectWebSocket(localStorage.getItem('selectedLanguage'));
            }, 5000);
        };

        socket.onerror = err => {
            console.error("WebSocket error:", err);
            $serviceMessageOutput.text(`Error: ${err}`);
        };

        // Receive message from server
        socket.onmessage = ({data}) => {
            const msg = JSON.parse(data);
            if (msg.translated_text) addText(msg);
        };
    }

    // ------------------ UI ------------------

    // Append new translated text to the display
    function addText({original_text, translated_text, audio_content}) {
        if (isPaused) return;

        $('<div class="flex items-center w-full">')  // Контейнер по ширине
            .append(
                $('<div class="message bg-blue-100 dark:bg-blue-800 text-blue-900 dark:text-blue-100 rounded-lg px-4 py-2 flex-1">')
                    .text(translated_text)
                    .attr('title', original_text)
            )
            .append(
                $('<span class="message-audio-icon ml-2 cursor-pointer w-1/12 text-center">🔊</span>').on('click', async  function (){
                    await playAudioFromElement($(this).parent());
                })
            )
            .attr('data-audio-content', audio_content || null)
            .appendTo($textDisplay);


        setTimeout(() => {
            $textDisplay.scrollTop($textDisplay[0].scrollHeight);
        }, 0);
    }

    // Clear all displayed transcriptions
    function clearText() {
        $textDisplay.empty();
    }

    // Toggle pause/resume UI state
    function togglePause($btn) {
        isPaused = !isPaused;
        const $icon = $btn.find('img');
        $icon.attr('src', isPaused
            ? '/static/img/play-svgrepo-com.svg'
            : '/static/img/play-pause-svgrepo-com.svg');

        $serviceMessageOutputIcon.toggleClass('blinking', !isPaused);
    }

    function toggleSidePanel() {
        $side_panel.toggleClass('hidden');
        $('main').toggleClass('shifted');
    }

    // Reusable button component generator
    function getButton(text, iconUrl, alt, onClick) {
        let html_img = `${text}<img src="${iconUrl}" alt="${alt}">`;
        if (iconUrl === '') {
            html_img = `${text}`;
        }
        return $('<button>', {
            html: html_img,
            click: onClick
        }).addClass('bg-gray-200 dark:bg-gray-700 px-3 py-1 rounded hover:bg-gray-300 dark:hover:bg-gray-600');
    }

    // Build and append control buttons to footer
    function createFooterButtons() {
        const $pauseBtn = getButton('', '/static/img/play-pause-svgrepo-com.svg', 'pause', () => togglePause($pauseBtn));
        $side_panel.append(
            getButton('', '/static/img/theme-store.svg', 'theme', toggleTheme),
            getButton('', '/static/img/refresh-cw-alt-1-svgrepo-com.svg', 'clear', clearText),
            $pauseBtn,
            getButton('', '/static/img/audio.svg', 'audio', () => {
                $textDisplay.children().each((_, el) => playAudioFromElement($(el)));
            }),
            getButton('', '/static/img/settings-cog-svgrepo-com.svg', 'settings', () => window.location.href = "/settings")
        );
    }

    // Send new language to backend and reconnect WebSocket
    async function changeLanguage(lang) {
        localStorage.setItem('selectedLanguage', lang);
        try {
            const res = await fetch('/api/addLang', {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({lang})
            });

            if (!res.ok) throw new Error((await res.json()).detail);
            if (socket) socket.close(1000, 'Lang switch');
            connectWebSocket(lang);
        } catch (err) {
            console.error("Change lang error:", err);
        }
    }

    // Populate the language dropdown and bind change event
    function initLanguageSelect(languages, selectedLang) {
        languages.forEach(({value, text}) => {
            $langSelect.append(new Option(text, value));
        });

        $langSelect.val(selectedLang);
        $langSelect.on("change", e => changeLanguage(e.target.value));
    }

    // Fetch supported languages from the server or use fallback
    async function fetchLanguages() {
        try {
            const res = await fetch('/api/languages');
            if (!res.ok) throw new Error('Fetch failed');
            const langs = await res.json();
            return langs.map(code => ({value: code, text: code}));
        } catch (err) {
            console.error('Lang fetch error:', err);
            return [
                {value: 'en', text: 'English'},
                {value: 'ru', text: 'Russian'},
                {value: 'fr', text: 'Français'}
            ];
        }
    }

    // Prevent the screen from sleeping using Wake Lock API
    async function requestWakeLock() {
        try {
            wakeLock = await navigator.wakeLock?.request('screen');
            console.log('Wake Lock is active');
        } catch (err) {
            console.error("Wake Lock error:", err);
        }
    }

    // ------------------ INIT ------------------

    // Run when the page is ready
    $(document).ready(async () => {

        tailwind.config = {
            darkMode: 'class',
        }

        createFooterButtons();
        setThemeFromLocalStorage();

        $toggleSidePanel.click( ()=> {
            toggleSidePanel();
        });
        const selectedLang = localStorage.getItem('selectedLanguage') || 'ru';
        const languages = await fetchLanguages();
        initLanguageSelect(languages, selectedLang);
        await changeLanguage(selectedLang);
        await requestWakeLock();
    });

})();
