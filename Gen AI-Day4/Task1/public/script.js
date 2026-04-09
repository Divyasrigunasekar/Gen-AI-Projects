const extractBtn = document.getElementById('extractBtn');
const inputText = document.getElementById('inputText');
const resultsContainer = document.getElementById('resultsContainer');
const keywordsOutput = document.getElementById('keywordsOutput');
const btnText = document.querySelector('.btn-text');
const loader = document.getElementById('loader');

extractBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    
    if (!text) {
        // Subtle shake animation
        inputText.style.animation = 'shake 0.5s ease';
        setTimeout(() => { inputText.style.animation = ''; }, 500);
        return;
    }

    // UI Loading state
    extractBtn.disabled = true;
    btnText.style.display = 'none';
    loader.style.display = 'block';
    resultsContainer.classList.remove('show');
    keywordsOutput.innerHTML = '';

    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });

        const data = await response.json();

        if (response.ok) {
            displayKeywords(data.keywords);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to connect to the server.');
    } finally {
        extractBtn.disabled = false;
        btnText.style.display = 'block';
        loader.style.display = 'none';
    }
});

function displayKeywords(keywordsString) {
    // Keywords should be separated by commas based on prompt instructions
    const keywordsArray = keywordsString.split(',').map(k => k.trim()).filter(k => k);
    
    keywordsArray.forEach((keyword, index) => {
        const span = document.createElement('span');
        span.className = 'keyword-tag';
        span.textContent = keyword;
        // Stagger the animation
        span.style.animationDelay = `${index * 0.1}s`;
        keywordsOutput.appendChild(span);
    });

    resultsContainer.classList.add('show');
}

// Add shake animation style dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        50% { transform: translateX(5px); }
        75% { transform: translateX(-5px); }
    }
`;
document.head.appendChild(style);
