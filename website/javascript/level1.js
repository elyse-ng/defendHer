const box = document.getElementById('expandBox');
const drag = document.getElementById('dragger');

let isDragging = false;
let startY = 0;

drag.addEventListener('mousedown', (e) => {
    isDragging = true;
    startY = e.clientY;
});

document.addEventListener('mousemove', (e) => {
    if (!isDragging) return; // do nothing if were not dragging
    const distanceMoved = e.clientY - startY;

    if (distanceMoved > 0) { // only respond to downward movement
        box.style.height = `${150 + distanceMoved}px`;
    }
});

document.getElementById('closeBtn').addEventListener('click', () => {
    box.classList.remove('expanded');
    box.style.height = '150px';
});

document.addEventListener('mouseup', (e) => {
    if (!isDragging) return;
    isDragging = false;
    const distanceMoved = e.clientY - startY;
    if (distanceMoved > 100) {
        box.classList.add('expanded');
    } else {
        box.style.height = '150px';
    }
});