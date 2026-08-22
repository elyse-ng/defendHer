

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

typeMessage();
// Start with message 1