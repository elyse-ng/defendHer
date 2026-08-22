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
}).catch((error) => {
    console.error(error);
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

        const response = await fetch("http://localhost:8000/predict", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();

        console.log("Backend response:", data);

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