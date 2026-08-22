// put this in a script on resultslevel1.html (or wherever you set this up)
document.addEventListener("DOMContentLoaded", () => {
    const video = document.querySelector(".user-output");
    const source = video.querySelector("source");
    
    // cache-bust with current timestamp
    source.src = "../../outputs/result_coordinate.mp4?t=" + Date.now();
    video.load(); // forces the browser to reload the <source>
});