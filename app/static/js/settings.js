(function () {
    const messageTemplate = `<h2>Status: {status}</h2><p id="message">{message}</p>`;

    // Function to render the status message
    function renderMessage(response_json) {
        const status = response_json.status;
        const transcriber_status = response_json.transcriber_status;
        const message = response_json.message;
        const statusColor = status === 'ok' ? 'green' : 'red';

        // Get the current date and time
        const currentTime = new Date().toLocaleString();

        // Update the DOM with the status, message, and time
        $('#state_json')
            .append(
                $(`<h2 style="color:${statusColor};">Status: ${transcriber_status}</h2>`)
            )
            .append(
                $(`<p id="message">${message}</p>`)
            )
            .append(
                $(`<p>Time: ${currentTime}</p>`) // Add the current time
            )
            .append(
                $('<br>') // Corrected: Adding a line break
            );
    }


    // Function to send requests with error handling and loading state
    async function sendRequest(url, method, data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json', // Set content type to JSON
            }
        };

        // Include body only for POST requests
        if (data) {
            options.body = JSON.stringify(data); // Stringify the body if any data is provided
        }

        try {
            // Make the fetch request
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Unknown error'); // If response is not OK, throw an error
            }
            return await response.json(); // Return the JSON response
        } catch (error) {
            throw new Error(error.message); // Handle any errors that occur during the request
        }
    }

    // Handler for the "start" button
    document.getElementById('startButton').addEventListener('click', async () => {
        try {
            // Send a POST request to the /api/start endpoint
            $('#startButton').disabled = true; // Disable the button to prevent repeated clicks
            $('#responseMessage').innerHTML = 'Loading...'; // Show loading status

            const response_json = await sendRequest('/api/start', 'POST'); // Send request
            renderMessage(response_json); // Render the status message
        } catch (error) {
            // If an error occurs, display the error message
            $('#responseMessage').innerHTML = `
                        Error: $
                        {
                            error.message
                        }
        `;
        } finally {
            // Re-enable the start button after request completes
            document.getElementById('startButton').disabled = false;
        }
    });

    // Handler for the "stop" button
    document.getElementById('stopButton').addEventListener('click', async () => {
        try {
            // Send a POST request to the /api/stop endpoint
            document.getElementById('stopButton').disabled = true; // Disable the button
            document.getElementById('responseMessage').innerHTML = 'Loading...'; // Show loading status

            const response_json = await sendRequest('/api/stop', 'POST'); // Send request
            renderMessage(response_json); // Render the status message
        } catch (error) {
            // If an error occurs, display the error message
            document.getElementById('responseMessage').innerHTML = `
        Error: $
        {
            error.message
        }
        `;
        } finally {
            // Re-enable the stop button after request completes
            document.getElementById('stopButton').disabled = false;
        }
    });

    // Function to load the current state when the page loads
    window.onload = async function () {
        try {
            // Send a GET request to the /api/state_json endpoint to fetch the current state
            const response_json = await sendRequest('/api/state_json', 'GET');
            renderMessage(response_json); // Render the current state
        } catch (error) {
            // If an error occurs, display the error message
            document.getElementById('state_json').innerHTML = `
        Error: $
        {
            error.message
        }
        `;
        }
    };

})();
