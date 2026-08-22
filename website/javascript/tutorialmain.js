const webcam = document.getElementById('webcam');
const stopButton = document.getElementById('stop-webcam');
const startButton = document.getElementById('start-webcam');

const startRecordingButton = document.getElementById('start-recording');
const stopRecordingButton = document.getElementById('stop-recording');

const resultDiv = document.getElementById("result");

let stream;
let mediaRecorder;
let recordedChunks = [];

navigator.mediaDevices.getUserMedia({ video: true })
.then(mediaStream => {
    stream = mediaStream;
    webcam.srcObject = stream;
})
.catch(error => {
    console.error("Camera error:", error);
});

stopButton.addEventListener('click', () => {
    if (stream){
        stream.getTracks().forEach(track => track.stop());

        webcam.srcObject = null;
        stream = null;
    }
});

startButton.addEventListener('click', () => {

    navigator.mediaDevices.getUserMedia({ video: true })
    .then(mediaStream => {
        stream = mediaStream;
        webcam.srcObject = stream;
    })
    .catch((error) => {
        console.error(error);
    });


});

startRecordingButton.addEventListener('click', () => {

    if (!stream) {
        alert("Please start the camera first.");
        return;
    }

    recordedChunks = [];

    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };

    mediaRecorder.onstop = async () => {

    const videoBlob = new Blob(recordedChunks, {
        type: "video/webm"
    });

    console.log("Recording created:", videoBlob);

    const formData = new FormData();

    formData.append("file", videoBlob, "recording.webm");

    formData.append("action", "punch");

    try {
        console.log("SENDING VIDEO TO BACKEND...");

        const response = await fetch("http://localhost:8000/predict", {
            method: "POST",
            body: formData
        });

        console.log("BACKEND RESPONSE RECEIVED");

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();

        console.log("BACKEND DATA:", data);

        // Save the result immediately
        localStorage.setItem("punchResult", JSON.stringify(data));

        console.log("RESULT SAVED TO LOCAL STORAGE");

        localStorage.setItem("punchResult", JSON.stringify(data));

        console.log("RESULT SAVED");

        window.location.href = "results.html";

        resultDiv.textContent =
            `Result: ${data.label} — Confidence: ${(data.confidence * 100).toFixed(1)}%`;

    } catch (error) {

        console.error("Upload failed:", error);

    }

};

    mediaRecorder.start();

    console.log("Recording started!");

    
});

stopRecordingButton.addEventListener('click', () => {

    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();

        console.log("Recording stopped!");
    }

});

//TUTORIAL TEXT

const messages = [
    `GREETINGS! WELCOME TO DEFENDHER!<br>
    (click the screen to see to the next instructions)`,

    `To begin your self-defence journey,<br>
    we must first watch the tutorial video.`,

    "ok now GO watch the video. Right now.",

    "OK now that you've watched the video",

    `hit start camera and record yourself<br> 
    doing the moves you learned in the video.<br>`


];

let messageNumber = 0;
let typed;


function typeMessage() {

    typed = new Typed("#typed-text", {
        strings: [messages[messageNumber]],

        typeSpeed: 30,
        loop: false,

        onComplete: function() {

            // Wait for user to click anywhere
            document.addEventListener("click", nextMessage, {
                once: true
            });
        }
    });
}


function nextMessage() {

    // Move to the next message
    messageNumber++;

    // Check if another message exists
    if (messageNumber < messages.length) {

        // Remove old Typed text
        typed.destroy();

        // Type the next message
        typeMessage();
    }
}


// Start with message 1