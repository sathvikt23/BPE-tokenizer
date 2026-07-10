// Multilingual BPE Tokenizer Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
    const textArea = document.getElementById('text');
    const outputDiv = document.getElementById('output');
    const searchInput = document.getElementById('search');
    const vocabDiv = document.getElementById('vocab');
    const tooltip = document.getElementById('tooltip');

    const charsVal = document.getElementById('chars');
    const wordsVal = document.getElementById('words');
    const tokensVal = document.getElementById('tokens');
    const ratioVal = document.getElementById('ratio');

    let vocabList = [];

    // Helper to escape HTML tags
    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Helper to format BPE tokens visually
    function formatToken(token) {
        if (!token) return '';
        // Replace GPT-2 BPE space character Ġ with a normal space for readability
        let formatted = token.replace(/Ġ/g, ' ');
        // Replace SentencePiece space character   with a space
        formatted = formatted.replace(/ /g, ' ');
        // Format control characters/newlines
        formatted = formatted.replace(/\n/g, '↵');
        formatted = formatted.replace(/\t/g, '⇥');
        return formatted;
    }

    // Debounce function to limit API requests
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // Fetch and render vocabulary
    async function loadVocabulary() {
        vocabDiv.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>Loading vocabulary...</span>
            </div>
        `;
        try {
            const response = await fetch('/vocabulary');
            if (!response.ok) throw new Error('Failed to load vocabulary');
            vocabList = await response.json();
            renderVocab(vocabList);
        } catch (error) {
            vocabDiv.innerHTML = `
                <div style="color: #ef4444; padding: 12px; font-size: 13px; text-align: center;">
                    ⚠️ Error loading vocabulary: ${error.message}
                </div>
            `;
        }
    }

    // Render vocabulary list (limited to first 150 items for DOM performance)
    function renderVocab(list) {
        vocabDiv.innerHTML = '';
        if (list.length === 0) {
            vocabDiv.innerHTML = `
                <div style="color: var(--text-muted); text-align: center; padding: 20px; font-size: 13px;">
                    No matching tokens found
                </div>
            `;
            return;
        }

        const maxDisplay = 150;
        const itemsToRender = list.slice(0, maxDisplay);

        itemsToRender.forEach(item => {
            const div = document.createElement('div');
            div.className = 'vocab-item';

            const tokenSpan = document.createElement('span');
            tokenSpan.className = 'vocab-token';
            tokenSpan.textContent = formatToken(item.token);
            // If the token was BPE spaces, keep trace of raw representation in title hover
            if (item.token !== tokenSpan.textContent) {
                tokenSpan.title = `Raw token: "${item.token}"`;
            }

            const idSpan = document.createElement('span');
            idSpan.className = 'vocab-id';
            idSpan.textContent = `ID: ${item.id}`;

            div.appendChild(tokenSpan);
            div.appendChild(idSpan);
            vocabDiv.appendChild(div);
        });

        if (list.length > maxDisplay) {
            const moreDiv = document.createElement('div');
            moreDiv.style.textAlign = 'center';
            moreDiv.style.padding = '10px 0';
            moreDiv.style.fontSize = '12px';
            moreDiv.style.color = 'var(--text-muted)';
            moreDiv.style.borderTop = '1px solid rgba(255, 255, 255, 0.05)';
            moreDiv.textContent = `... and ${list.length - maxDisplay} more items`;
            vocabDiv.appendChild(moreDiv);
        }
    }

    // Vocabulary Search Filter
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase().trim();
        if (!query) {
            renderVocab(vocabList);
            return;
        }

        const filtered = vocabList.filter(item => 
            item.token.toLowerCase().includes(query) || 
            item.id.toString().includes(query)
        );
        renderVocab(filtered);
    });

    // Tokenize text input via backend API
    async function performTokenization() {
        const text = textArea.value;
        if (!text) {
            outputDiv.innerHTML = '<span style="color: var(--text-muted);">Start typing...</span>';
            charsVal.textContent = '0';
            wordsVal.textContent = '0';
            tokensVal.textContent = '0';
            ratioVal.textContent = '0.0000';
            return;
        }

        try {
            const response = await fetch('/tokenize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            if (!response.ok) throw new Error('Tokenization failed');
            const data = await response.json();

            // Update stats
            charsVal.textContent = data.character_count;
            wordsVal.textContent = data.word_count;
            tokensVal.textContent = data.token_count;
            
            const ratio = data.word_count > 0 ? (data.token_count / data.word_count) : 0;
            ratioVal.textContent = ratio.toFixed(4);

            // Render interactive tokens
            outputDiv.innerHTML = '';
            data.tokens.forEach((token, index) => {
                const span = document.createElement('span');
                // Cycle color classes c0 to c7
                span.className = `token c${index % 8}`;
                
                // Represent spaces clearly
                let displayVal = formatToken(token.token);
                // If token is just spaces, make it visible space
                if (displayVal.trim() === '') {
                    displayVal = ' '.repeat(displayVal.length || 1);
                }
                span.textContent = displayVal;

                // Tooltip hover interactions
                span.addEventListener('mouseenter', (e) => {
                    const rawSub = text.substring(token.start, token.end);
                    tooltip.innerHTML = `
                        <div style="font-weight: 700; color: #ffffff; margin-bottom: 6px; font-family: 'Fira Code', monospace;">
                            "${escapeHtml(token.token)}"
                        </div>
                        <div style="margin-bottom: 4px;"><strong>Token ID:</strong> ${token.id}</div>
                        <div style="margin-bottom: 4px;"><strong>Offsets:</strong> [${token.start}, ${token.end}]</div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.15); margin-top: 8px; padding-top: 6px;">
                            <strong style="color: #d4d4d8;">Text segment:</strong> 
                            <span style="font-style: italic; background: rgba(255,255,255,0.05); padding: 2px 4px; border-radius: 4px;">
                                "${escapeHtml(rawSub)}"
                            </span>
                        </div>
                    `;
                    tooltip.style.display = 'block';
                });

                span.addEventListener('mousemove', (e) => {
                    // Position tooltip nicely near cursor
                    tooltip.style.left = `${e.clientX + 15}px`;
                    tooltip.style.top = `${e.clientY + 15}px`;
                });

                span.addEventListener('mouseleave', () => {
                    tooltip.style.display = 'none';
                });

                outputDiv.appendChild(span);
            });

        } catch (error) {
            outputDiv.innerHTML = `
                <span style="color: #ef4444; font-weight: 500;">
                    ⚠️ Error: ${error.message}
                </span>
            `;
        }
    }

    // Debounced listener on text area input
    const debouncedTokenization = debounce(performTokenization, 200);
    textArea.addEventListener('input', debouncedTokenization);

    // Initial setup loads vocabulary and performs first tokenization
    loadVocabulary();
    performTokenization();
});
