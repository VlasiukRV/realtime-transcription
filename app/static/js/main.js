(function () {

    const serverIp = window.location.hostname;
    const $serviceMessageOutput = $("#service-message-output");
    const $serviceMessageOutputIcon = $("#service-message-output-icon");
    const $textDisplay = $('#output');
    const $footer = $('.footer');
    const $toggleThemeBtn = $('#toggle-theme-btn');

    let isPaused = false;
    let socket = null;
    let reconnectInterval;
    let languagesDb = [
        {value: 'en', text: 'English'},
        {value: 'ru', text: 'Russian'},
        {value: 'fr', text: 'Français'}
    ];

    // Constants for icons
    const ICON_SUN = '☀️';
    const ICON_MOON = '🌙';
    const ICON_CLEAR = '🔄';
    const ICON_PLAY = '▶️';
    let ICON_PAUSE = '⏯';

    // Theme structure, storing theme names and related icons
    const THEMES = {
        light: {
            name: 'light',
            icon: ICON_SUN
        },
        dark: {
            name: 'dark',
            icon: ICON_MOON
        }
    };

    // Set theme based on localStorage upon page load
    function setThemeFromLocalStorage() {
        const savedTheme = localStorage.getItem('theme') || THEMES.light.name; // Default theme
        $("html").attr('data-theme', savedTheme);
        $toggleThemeBtn.text(savedTheme === THEMES.dark.name ? ICON_SUN : ICON_MOON);
    }

    // Toggle between light and dark themes
    function toggleTheme() {
        const currentTheme = $("html").attr('data-theme') || THEMES.light.name;
        const newTheme = currentTheme === THEMES.light.name ? THEMES.dark.name : THEMES.light.name;
        $("html").attr('data-theme', newTheme);
        localStorage.setItem('theme', newTheme); // Save new theme in localStorage
        $toggleThemeBtn.text(newTheme === THEMES.dark.name ? ICON_SUN : ICON_MOON); // Update button text accordingly
    }

    // Connect to WebSocket with the specified language
    async function connectWebSocket(lang) {
        if (!lang) return; // Do not connect if no language is specified

        $serviceMessageOutput.html(`Connecting to ${serverIp}...`);

        socket = new WebSocket(`ws://${serverIp}:8000/ws/transcribe/${lang}`);

        socket.onmessage = (event) => handleWebSocketMessage(event); // Handle incoming messages
        socket.onopen = () => handleWebSocketOpen(lang); // Handle WebSocket open event
        socket.onclose = () => handleWebSocketClose(); // Handle WebSocket close event
        socket.onerror = (error) => handleWebSocketError(error); // Handle WebSocket error event
    }

    let isPlaying = false;  // A flag to track if audio is currently playing

    function playAudio(audioBase64, callAfterEndPlaying) {
        if (isPlaying) {
            console.log("Audio is already playing. Please wait.");
            return; // Exit the function if audio is already playing
        }

        // Set the flag to indicate that audio is playing
        isPlaying = true;

        // Create a Blob from the base64-encoded string
        let audioBlob = new Blob([new Uint8Array(atob(audioBase64).split("").map(char => char.charCodeAt(0)))], {type: 'audio/mp3'});

        // Create a URL for the audio Blob
        let audioUrl = URL.createObjectURL(audioBlob);

        // Create an HTMLAudioElement to play the audio
        let audio = new Audio(audioUrl);

        // Play the audio
        audio.play().catch(error => {
            console.error("Error playing the audio:", error);
        });

        // Listen for the "ended" event to know when the audio is finished
        audio.onended = function () {
            isPlaying = false; // Reset the flag when the audio finishes
            callAfterEndPlaying()
        };
    }

    async function getNextAudioContentWithDelay($element) {
        let $next_element = $element.next();

        if ($next_element.length > 0) {
            return $next_element;
        }

        await new Promise(resolve => setTimeout(resolve, 1000));

        return getNextAudioContentWithDelay($element);
    }

    async function playAudioFromElement($element) {

        if ($element.attr('data-audio-content')) {
            playAudio($element.attr('data-audio-content'), async function () {
                $element.removeAttr('data-audio-content');
                $element.addClass('played');

                let $nextElement = await getNextAudioContentWithDelay($element);
                playAudioFromElement($nextElement);
            })
        }
    }

    // Event listener for the button click
    document.getElementById('playAudioButton').addEventListener('click', function () {
        // Now you can play audio after the user clicks the button
        $textDisplay.children().each(function (index, element) {
            playAudioFromElement($(element))
        });

    });

    // Handle incoming WebSocket messages
    function handleWebSocketMessage(event) {
        let jsonMessage = JSON.parse(event.data);

        if (jsonMessage.translated_text) {
            addText(jsonMessage); // Add regular messages to the display
        }
        // $serviceMessageOutput.append(`<p><strong>Service status:</strong> ${message.slice(17)}</p>`);

    }

    // Handle WebSocket open event (connection established)
    function handleWebSocketOpen(lang) {
        console.log(`WebSocket connected for language: ${lang}`);
        $serviceMessageOutput.html(`Connected to WebSocket for language: ${lang}`);
        $serviceMessageOutputIcon.addClass('blinking');
        clearInterval(reconnectInterval); // Stop checking for reconnections once connected
    }

    // Handle WebSocket close event (disconnected)
    function handleWebSocketClose() {
        console.log("Disconnected from WebSocket");
        $serviceMessageOutput.html(`Disconnected from WebSocket`);
        $serviceMessageOutputIcon.removeClass('blinking');
        reconnectInterval = setInterval(checkConnection, 5000); // Check connection every 5 seconds
    }

    // Handle WebSocket error event
    function handleWebSocketError(error) {
        console.error("WebSocket Error:", error);
        $serviceMessageOutput.html(`WebSocket Error${error}`);
        $serviceMessageOutputIcon.removeClass('blinking');
        $serviceMessageOutput.html(`Error: ${error}`); // Show error message
    }

    // Check WebSocket connection and attempt to reconnect if necessary
    function checkConnection() {
        if (socket.readyState === WebSocket.CLOSED || socket.readyState === WebSocket.CLOSING) {
            console.log("Attempting to reconnect...");
            connectWebSocket(localStorage.getItem('selectedLanguage')); // Reconnect using the saved language
        }
    }

    // Add text to the display with auto-scroll
    function addText(jsonMessage) {
        if (!isPaused) { // Only add text if not paused
            const newText = $('<p>').text(jsonMessage.translated_text);
            if (jsonMessage.audio_content) {
                newText.attr('data-audio-content', jsonMessage.audio_content)
            }
            $textDisplay.append(newText);
            $textDisplay.scrollTop($textDisplay[0].scrollHeight); // Auto-scroll to the bottom
        }
    }

    // Toggle pause/resume functionality
    function togglePause($button) {
        isPaused = !isPaused;

        const $icon = $button.find('img');

        if (isPaused) {
            $serviceMessageOutputIcon.removeClass('blinking');
            $icon.attr('src', '/static/img/play-svgrepo-com.svg');
        } else {
            $icon.attr('src', '/static/img/play-pause-svgrepo-com.svg');
            $serviceMessageOutputIcon.addClass('blinking');
        }

    }

    // Clear all displayed text
    function clearText() {
        $textDisplay.empty();
    }

    // Change the language and update WebSocket connection
    async function changeLanguageSelect(newLang) {
        localStorage.setItem('selectedLanguage', newLang); // Store the selected language in localStorage
        try {
            const response = await fetch("/api/addLang", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({lang: newLang}) // Send the selected language to the server
            });

            if (response.ok) {
                if (socket) socket.close(1000, 'Normal closure'); // Close current WebSocket if it exists
                await connectWebSocket(newLang); // Reconnect with the new language
                const result = await response.json();
                console.log(result.message); // Log the response from the server
            } else {
                const error = await response.json();
                console.log(`Error: ${error.detail}`); // Log error if the response is not OK
            }
        } catch (error) {
            console.error("Error:", error); // Log any network or other errors
        }
    }

    // Create and append the language select dropdown with jQuery
    function createLanguageSelect(languagesDb, defaultLang = '') {

        // Create <select> element
        const $select = $('<select>', {id: 'language-select'});

        // Generate and append <option> elements
        languagesDb.forEach(lang => {
            $select.append($('<option>', {
                value: lang.value,
                text: lang.text
            }));
        });

        $select.val(defaultLang); // Set the language select dropdown to the saved language
        $select.on("change", function (event) {
            const newLang = event.target.value;
            changeLanguageSelect(newLang).then((result) => {

            }).catch((error) => {
                console.error("Error changing language:", error);
            });
        });

        // Append the <select> element to the DOM (e.g., to the body or specific container)
        $('#language-container').append($select);
    }

    function getButtonElement(img_url, alt_text, func) {

        const $button = $('<button>', {
            html: `<img src="${img_url}" alt="${alt_text}">`,
            click: func
        });
        $button.addClass('button');

        return $button
    }

    function createFooterButtons() {

        const $clearButton = getButtonElement('/static/img/refresh-cw-alt-1-svgrepo-com.svg', "clear", function () {
            clearText();
        })
        const $pauseButton = getButtonElement('/static/img/play-pause-svgrepo-com.svg', 'pause play', function () {
            togglePause($pauseButton);
        })
        const $settingsButton = getButtonElement('/static/img/settings-cog-svgrepo-com.svg', 'settings', function () {
            window.location.href = "/settings";
        })

        $footer.append($clearButton, $pauseButton, $settingsButton);
    }

    async function fetchLanguages() {
      try {
        const response = await fetch('/api/languages');

        if (!response.ok) {
          throw new Error('Failed to fetch languages');
        }
        const languages = await response.json();

        languagesDb = languages.map(languageCode => {
          return { value: languageCode, text: languageCode };
        });

      } catch (error) {
        console.error('Error fetching languages:', error);
      }
    }

    let wakeLock = null;

    async function requestWakeLock() {
        try {
            wakeLock = await navigator.wakeLock.request('screen');
            wakeLock.addEventListener('release', () => {
                console.log('Wake Lock was released');
            });
            console.log('Wake Lock is active');
        } catch (err) {
            console.error(`${err.name}, ${err.message}`);
        }
    }

    // Initialize the page when it loads
    $(document).ready(async function () {
        createFooterButtons();
        setThemeFromLocalStorage(); // Set theme based on localStorage
        await fetchLanguages()

        let lang = localStorage.getItem('selectedLanguage') || 'ru'; // Default language is 'ru' if none is stored
        createLanguageSelect(languagesDb, lang); // Create language select dropdown

        changeLanguageSelect(lang).then((result) => {

        }).catch((error) => {
            console.error("Error connect WebSocket:", error);
        });
        // Connect to WebSocket with the saved language

        $toggleThemeBtn.on('click', toggleTheme); // Add event listener for the theme toggle button
        requestWakeLock();

    });
})();
