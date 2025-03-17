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

    // Handle incoming WebSocket messages
    function handleWebSocketMessage(event) {
        let message = event.data;
        if (message.startsWith("Service Message:")) {
            $serviceMessageOutput.append(`<p><strong>Service status:</strong> ${message.slice(17)}</p>`);
        } else {
            addText(event.data); // Add regular messages to the display
        }
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
    function addText(text) {
        if (!isPaused) { // Only add text if not paused
            const newText = $('<p>').text(text);
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

    // Initialize the page when it loads
    $(document).ready(function () {
        createFooterButtons();
        setThemeFromLocalStorage(); // Set theme based on localStorage

        let lang = localStorage.getItem('selectedLanguage') || 'ru'; // Default language is 'ru' if none is stored
        createLanguageSelect(languagesDb, lang); // Create language select dropdown

        changeLanguageSelect(lang).then((result) => {

        }).catch((error) => {
            console.error("Error connect WebSocket:", error);
        });
        // Connect to WebSocket with the saved language

        $toggleThemeBtn.on('click', toggleTheme); // Add event listener for the theme toggle button
    });
})();
