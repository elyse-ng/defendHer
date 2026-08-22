const webcam = document.getElementById('lvlwebcam');
const stopButton = document.getElementById('stop-webcam');
const startButton = document.getElementById('start-webcam');

const startRecordingButton = document.getElementById('start-recording');
const stopRecordingButton = document.getElementById('stop-recording');

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
