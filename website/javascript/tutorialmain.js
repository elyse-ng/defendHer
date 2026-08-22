const webcam = document.getElementById('webcam');
const stopButton = document.getElementById('stop-webcam');
const startButton = document.getElementById('start-webcam');

let stream;


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
typeMessage();