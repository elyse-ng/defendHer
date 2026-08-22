var typed = new Typed("#typed-text", {
    strings: [
        "GREETINGS! WELCOME TO DEFENDHER!",
        "HAVE YOU EVER BEEN IN A SITUATION WHERE YOU WISHED YOU KNEW HOW TO DEFEND YOURSELF?"
    ],

    typeSpeed: 80,
    backSpeed: 20,
    backDelay: 1000,
    loop: false,

    onComplete: function() {
        // Show YES / NO buttons after the intro finishes
        document.getElementById("choice-buttons").style.display = "flex";
    }
});


// YES BUTTON
document.getElementById("yes-button").addEventListener("click", function() {

    // Hide YES / NO buttons
    document.getElementById("choice-buttons").style.display = "none";

    // Stop old Typed animation
    typed.destroy();

    // Start YES dialogue
    typed = new Typed("#typed-text", {
        strings: [
            `WELL you're in luck! Here at defendHer,<br>
            we teach YOU how to defend yourself<br>
            through self-defence modules. <br>
            Would you like to begin?`
        ],

        typeSpeed: 30,
        loop: false,

        onComplete: function() {
            // Show YES I'M READY button
            document.getElementById("transition-button-container").style.display = "block";
        }
    });
});


// NO BUTTON
document.getElementById("no-button").addEventListener("click", function() {

    // Hide YES / NO buttons
    document.getElementById("choice-buttons").style.display = "none";

    typed.destroy();

    // Start NO dialogue
    typed = new Typed("#typed-text", {
        strings: [
            `WELL, SINCE YOU'RE HERE,<br>
            YOU HAVE TO LEARN SELF-DEFENCE ANYWAY.<br>
            YOU DON'T GET A CHOICE.`
        ],

        typeSpeed: 30,
        loop: false,

        onComplete: function() {
            // Show YES I'M READY button
            document.getElementById("transition-button-container").style.display = "block";
        }
    });
});


// YES I'M READY BUTTON
document.getElementById("transition-button").addEventListener("click", function() {

    // Hide transition button
    document.getElementById("transition-button-container").style.display = "none";

    typed.destroy();

    //
});