const webcam = document.getElementById('webcam');
const stopButton = document.getElementById('stop-webcam');
const startButton = document.getElementById('start-webcam');


let stream;

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