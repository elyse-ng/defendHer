// put this in a script on resultslevel1.html (or wherever you set this up)
document.addEventListener("DOMContentLoaded", () => {
    const video = document.querySelector(".user-output");
    const source = video.querySelector("source");
    const message = document.querySelector(".results-message");
    
    // cache-bust with current timestamp
    source.src = "../../outputs/result_coordinate.webm?t=" + Date.now();
    video.load(); // forces the browser to reload the <source>

    fetch("../../outputs/prediction.json?t=" + Date.now())
        .then((response) => {
            if (!response.ok) {
                throw new Error("Could not load prediction");
            }
            return response.json();
        })
        .then((prediction) => {
            const label = String(prediction.label).toLowerCase();
            const probability = Math.round(Number(prediction.confidence) * 100);
            const isGood = label === "good" || label === "1"
                || prediction.prediction === 1 || prediction.prediction === "1";
            const resultText = isGood
                ? "Good !"
                : "Bad...";

            message.textContent = `${resultText} (Probability ${probability}%)`;
        })
        .catch(() => {
            message.textContent = "Prediction unavailable";
        });
});