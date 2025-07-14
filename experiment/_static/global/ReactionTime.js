console.log('Script loaded');
document.addEventListener('DOMContentLoaded', () => {
    const centerCircle = document.getElementById('center-circle');
    const message = document.getElementById('message');

    let isGreen = false;
    let waiting = false;
    let timeoutId = null;
    let stimulusShownAt = null;
    let trialIndex = 0;

    function showMessage(text) {
        message.innerText = text;
        setTimeout(() => {
            message.innerText = '';
        }, 1000);
    }

    function startTrial() {
        // Reset state
        isGreen = false;
        waiting = true;
        stimulusShownAt = null;
        centerCircle.style.backgroundColor = 'gray';

        // Delay before showing green
        const delay = Math.random() * 6000 + 1000;
        timeoutId = setTimeout(() => {
            centerCircle.style.backgroundColor = '#005000';
            isGreen = true;
            waiting = false;
            stimulusShownAt = performance.now();
        }, delay);
    }

    function handleClick() {
        if (waiting && !isGreen) {
            clearTimeout(timeoutId);
            showMessage('Too soon!');
            startTrial(); // reset trial
        } else if (isGreen) {
            const rt = performance.now() - stimulusShownAt;
            showMessage('Correct!');

            liveSend({
                trial_index: trialIndex,
                reaction_time: rt.toFixed(2)
            });

            trialIndex++;
            // Reset immediately so green doesn't stay
            isGreen = false;
            centerCircle.style.backgroundColor = 'gray';

            // Delay before next trial starts
            setTimeout(startTrial, 1000);
        }
    }

    centerCircle.addEventListener('click', handleClick);

    document.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') {
            handleClick();
        }
    });

    // Start first trial
    startTrial();
});