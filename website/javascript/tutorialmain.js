const webcam = document.getElementById('webcam');
const stopButton = document.getElementById('stop-webcam');
const startButton = document.getElementById('start-webcam');


let stream;
let mediaRecorder;
let recordedChunks = [];


// CAMERA STARTS WHEN PAGE LOADS
navigator.mediaDevices.getUserMedia({ video: true })
.then(mediaStream => {
    stream = mediaStream;
    webcam.srcObject = stream;
})
.catch((error) => {
    console.error(error);
});


// STOP CAMERA
stopButton.addEventListener('click', (event) => {

    event.stopPropagation();

    if (stream) {
        stream.getTracks().forEach(track => track.stop());

        webcam.srcObject = null;
        stream = null;
    }
});


// START CAMERA
startButton.addEventListener('click', (event) => {

    event.stopPropagation();

    navigator.mediaDevices.getUserMedia({ video: true })
    .then(mediaStream => {
        stream = mediaStream;
        webcam.srcObject = stream;
    })
    .catch((error) => {
        console.error(error);
    });


});