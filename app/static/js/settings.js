(function () {
// const service_status_output = document.getElementById('service-status-output');
//
// const eventSource = new EventSource("/api/status");
//
// eventSource.onmessage = function (event) {
//     service_status_output.innerHTML = JSON.stringify(event.data, null, 2);
// };
//
// eventSource.onerror = function (error) {
//     console.log("Ошибка SSE:", error);
// };

// Adding a click event listener to the "startButton"
    document.getElementById('startButton').addEventListener('click', async () => {
        try {
            // Sending a POST request to the 'api/start' endpoint
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', // Setting the content type to JSON
                },
            });

            if (response.ok) {
                // If the response is successful, display the response text
                let text;
                text = await response.text();
                document.getElementById('responseMessage').innerHTML = text;
            } else {
                // If the response is not successful, show an error message
                document.getElementById('responseMessage').innerHTML = "Error starting the worker.";
            }
        } catch (error) {
            // Handle any errors that occur during the connection with the server
            document.getElementById('responseMessage').innerHTML = "Connection error with the server.";
        }
    });

// Adding a click event listener to the "stopButton"
    document.getElementById('stopButton').addEventListener('click', async () => {
        try {
            // Sending a POST request to the 'api/stop' endpoint
            const response = await fetch('/api/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', // Setting the content type to JSON
                },
            });

            if (response.ok) {
                // If the response is successful, display the response text
                let text;
                text = await response.text();
                document.getElementById('responseMessage').innerHTML = text;
            } else {
                // If the response is not successful, show an error message
                document.getElementById('responseMessage').innerHTML = "Error stopping the worker.";
            }
        } catch (error) {
            // Handle any errors that occur during the connection with the server
            document.getElementById('responseMessage').innerHTML = "Connection error with the server.";
        }
    });


    window.onload = async function () {

        try {
            // Sending a POST request to the 'api/stop' endpoint
            const response = await fetch('/api/state_json', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json', // Setting the content type to JSON
                },
            });

            if (response.ok) {
                // If the response is successful, display the response text
                let text;
                text = await response.text();
                document.getElementById('state_json').innerHTML = text;
            } else {
                // If the response is not successful, show an error message
                document.getElementById('state_json').innerHTML = "Error stopping the worker.";
            }
        } catch (error) {
            // Handle any errors that occur during the connection with the server
            document.getElementById('state_json').innerHTML = "Connection error with the server.";
        }

    };

})();
