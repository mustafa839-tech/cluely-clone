const toggleButton = document.getElementById('toggle-button');
const status = document.getElementById('status');
const transcript = document.getElementById('transcript');
const analysis = document.getElementById('analysis');
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const searchResults = document.getElementById('search-results');
const kbList = document.getElementById('knowledge-base-list');
const kbForm = document.getElementById('knowledge-base-form');
const kbTerm = document.getElementById('kb-term');
const kbDefinition = document.getElementById('kb-definition');
const languageSelect = document.getElementById('language-select');
let mediaRecorder;
let isRecording = false;
let socket;
let knowledgeBase = { "custom_terms": [] };

document.addEventListener('DOMContentLoaded', () => {
    loadKnowledgeBase();
});

toggleButton.addEventListener('click', () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

searchButton.addEventListener('click', async () => {
    const query = searchInput.value;
    if (!query) {
        searchResults.innerHTML = 'Please enter a search term.';
        return;
    }

    try {
        const response = await fetch(`http://localhost:8080/search?q=${encodeURIComponent(query)}`);
        const results = await response.json();

        if (results.length === 0) {
            searchResults.innerHTML = 'No results found.';
            return;
        }

        searchResults.innerHTML = results.map(result => `
            <div>
                <strong>${result.file}:</strong> ${result.line}
            </div>
        `).join('');
    } catch (error) {
        console.error('Error searching:', error);
        searchResults.innerHTML = 'An error occurred during search.';
    }
});

kbForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const newTerm = {
        term: kbTerm.value,
        definition: kbDefinition.value
    };
    knowledgeBase.custom_terms.push(newTerm);

    try {
        await fetch('http://localhost:8080/knowledge-base', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(knowledgeBase)
        });
        kbTerm.value = '';
        kbDefinition.value = '';
        renderKnowledgeBase();
    } catch (error) {
        console.error('Error updating knowledge base:', error);
    }
});

async function loadKnowledgeBase() {
    try {
        const response = await fetch('http://localhost:8080/knowledge-base');
        knowledgeBase = await response.json();
        renderKnowledgeBase();
    } catch (error) {
        console.error('Error loading knowledge base:', error);
    }
}

function renderKnowledgeBase() {
    kbList.innerHTML = knowledgeBase.custom_terms.map(item => `
        <div><strong>${item.term}:</strong> ${item.definition}</div>
    `).join('');
}

async function startRecording() {
    try {
        const language = languageSelect.value;
        socket = new WebSocket(`ws://localhost:8765?language=${language}`);

        socket.onopen = () => {
            console.log('WebSocket connection established');
            status.textContent = 'Recording';
            isRecording = true;
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'interim') {
                transcript.textContent = data.transcript;
            } else {
                const analysisData = JSON.parse(data);
                analysis.innerHTML = `
                    <h3>Summary</h3>
                    <p>${analysisData.summary}</p>
                    <h3>Questions</h3>
                    <ul>
                        ${analysisData.questions.map(q => `<li>${q}</li>`).join('')}
                    </ul>
                    <h3>Key Concepts</h3>
                    <ul>
                        ${analysisData.concepts.map(c => `<li>${c}</li>`).join('')}
                    </ul>
                `;
            }
        };

        socket.onclose = () => {
            console.log('WebSocket connection closed');
            status.textContent = 'Idle';
            isRecording = false;
        };

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                socket.send(e.data);
            }
        };
        mediaRecorder.start(1000); // Send data every 1 second
    } catch (error) {
        console.error('Error starting recording:', error);
        status.textContent = 'Error';
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
    }
}