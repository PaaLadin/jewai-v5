
const term = document.getElementById('term');
const inputLine = document.getElementById('inputLine');
const inputText = document.getElementById('inputText');
let state = 0, lang = 'en', config = {}, inputBuf = '', isTyping = false, typingQueue = [], fullText = "";

const i18n = {
    en: {
        welcome: "JEWAI OS v5 // SYSTEM INSTALLER\n\nSelect language / Выберите язык [en/ru]: ",
        path: "\n[1/5] Installation path (e.g. C:\\JewAI_v5): ",
        basePort: "\n[2/5] Base port for agents (e.g. 8760): ",
        agentCount: "\n[3/5] Number of agents (1-10): ",
        chatPort: "\n[4/5] Mainframe chat port (e.g. 8670): ",
        proxyPort: "\n[5/6] DoH proxy port (e.g. 9999): ",
        names: "\n[6/6] Agent names (comma separated, e.g. Arkady, Boris. Leave empty for A, B): ",
        summary: "\n--- SUMMARY ---\nPath: {0}\nPorts: {1}/{3}/{4}\nAgents: {2}\n\nProceed? [y/n]: ",
        installing: "\nInstalling...\n",
        installDone: "\nInstallation complete. Launch all services now? [y/n]: ",
        launching: "\nStarting services...\n",
        launchDone: "\nAll services started. Mainframe: http://127.0.0.1:{0}/\n\nYou can now close this window.",
        cancelled: "\nCancelled. You can now close this window.",
        invalid: "\nPlease answer 'y' or 'n'.\n> ",
        fail: "\nFAILED: {0}\nYou can now close this window."
    },
    ru: {
        welcome: "JEWAI OS v5 // СИСТЕМА УСТАНОВКИ\n\nSelect language / Выберите язык [en/ru]: ",
        path: "\n[1/5] Путь установки (например C:\\JewAI_v5): ",
        basePort: "\n[2/5] Базовый порт агентов (например 8760): ",
        agentCount: "\n[3/5] Количество агентов (1-10): ",
        chatPort: "\n[4/5] Порт мейнфрейма (например 8670): ",
        proxyPort: "\n[5/6] Порт DoH-прокси (например 9999): ",
        names: "\n[6/6] Имена агентов (через запятую, например Аркадий, Борис. Оставьте пустым для A, B): ",
        summary: "\n--- ПОДТВЕРЖДЕНИЕ ---\nПуть: {0}\nПорты: {1}/{3}/{4}\nАгентов: {2}\n\nПродолжить? [y/n]: ",
        installing: "\nУстановка...\n",
        installDone: "\nУстановка завершена. Запустить все сервисы сейчас? [y/n]: ",
        launching: "\nЗапуск сервисов...\n",
        launchDone: "\nСервисы запущены. Мейнфрейм: http://127.0.0.1:{0}/\n\nТеперь вы можете закрыть это окно.",
        cancelled: "\nОтменено. Вы можете закрыть это окно.",
        invalid: "\nПожалуйста, ответьте 'y' или 'n'.\n> ",
        fail: "\nОШИБКА: {0}\nВы можете закрыть это окно."
    }
};

function typeText(text) {
    typingQueue.push(text);
    if (!isTyping) processQueue();
}

function processQueue() {
    if (typingQueue.length === 0) {
        isTyping = false;
        if (state === 1 || (state >= 2 && state <= 8) || state === 10) showInput();
        return;
    }
    isTyping = true;
    let text = typingQueue.shift();
    let i = 0;
    inputLine.style.display = 'none';
    
    function typeChar() {
        if (i < text.length) {
            fullText += text.charAt(i);
            term.textContent = fullText;
            if (text.charAt(i) !== ' ' && text.charAt(i) !== '\n') sfxType();
            window.scrollTo(0, document.body.scrollHeight);
            i++;
            setTimeout(typeChar, 40); // SLOWED DOWN
        } else {
            processQueue();
        }
    }
    typeChar();
}

function showInput() {
    inputLine.style.display = 'block';
    inputBuf = '';
    inputText.textContent = '';
    window.scrollTo(0, document.body.scrollHeight);
}

function submitInput(val) {
    const lower = val.trim().toLowerCase();
    fullText += val + "\n";
    term.textContent = fullText;
    inputBuf = '';
    inputText.textContent = '';

    if (state === 1) {
        if (['ru', 'rus', 'russian', 'рус', 'русский', 'ру'].includes(lower)) lang = 'ru';
        else lang = 'en';
        state = 2;
        typeText(i18n[lang].path);
    } else if (state === 2) {
        config.root = val || 'C:\\JewAI_v5';
        state = 3;
        typeText(i18n[lang].basePort);
    } else if (state === 3) {
        config.basePort = parseInt(val) || 8760;
        state = 4;
        typeText(i18n[lang].agentCount);
    } else if (state === 4) {
        config.agentCount = parseInt(val) || 4;
        state = 5;
        typeText(i18n[lang].chatPort);
    } else if (state === 5) {
        config.chatPort = parseInt(val) || 8670;
        state = 6;
        typeText(i18n[lang].proxyPort);
    } else if (state === 6) {
        config.proxyPort = parseInt(val) || 9999;
        state = 7;
        typeText(i18n[lang].names);
    } else if (state === 7) {
        config.names = val;
        state = 8;
        let s = i18n[lang].summary;
        typeText(s.replace('{0}', config.root).replace('{1}', config.basePort).replace('{2}', config.agentCount).replace('{3}', config.chatPort).replace('{4}', config.proxyPort));
    } else if (state === 8) {
        if (['y', 'yes', 'да', 'д'].includes(lower)) {
            state = 9;
            sfxDisk();
            typeText(i18n[lang].installing);
            fetch('/api/install', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(config)
            }).then(r => r.json()).then(res => {
                if (res.ok) {
                    state = 10;
                    typeText(i18n[lang].installDone);
                } else {
                    state = 12;
                    typeText(i18n[lang].fail.replace('{0}', res.error || 'unknown'));
                }
            }).catch(err => {
                state = 12;
                typeText(i18n[lang].fail.replace('{0}', err.toString()));
            });
        } else if (['n', 'no', 'нет', 'н'].includes(lower)) {
            state = 12;
            typeText(i18n[lang].cancelled);
        } else {
            typeText(i18n[lang].invalid);
        }
    } else if (state === 10) {
        if (['y', 'yes', 'да', 'д'].includes(lower)) {
            state = 11;
            sfxDisk();
            typeText(i18n[lang].launching);
            fetch('/api/launch', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(config)
            }).then(r => r.json()).then(res => {
                state = 12;
                typeText(i18n[lang].launchDone.replace('{0}', config.chatPort));
                window.open('http://127.0.0.1:' + config.chatPort + '/', '_blank');
            }).catch(err => {
                state = 12;
                typeText(i18n[lang].fail.replace('{0}', err.toString()));
            });
        } else if (['n', 'no', 'нет', 'н'].includes(lower)) {
            state = 12;
            typeText(i18n[lang].cancelled);
        } else {
            typeText(i18n[lang].invalid);
        }
    }
}

// Handle first keypress
document.addEventListener('keydown', (e) => {
    if (state === -1) {
        e.preventDefault(); // prevent scrolling
        initAudio();
        document.getElementById('boot-screen').style.display = 'none';
        
        // Start Splash Sequence
        const splash = document.getElementById('splash-screen');
        splash.style.display = 'flex';
        
        const ai = document.querySelector('.l-ai');
        setTimeout(() => { ai.classList.add('anim-fade-in'); }, 100); // AI fades in
        
        setTimeout(() => {
            // 1-3-2 order: J, w, e
            document.querySelector('.l-j').classList.add('drop-j');
            playWebMoneyCoins(); // Start sound precisely
            setTimeout(() => { document.querySelector('.l-w').classList.add('drop-w'); }, 100); // Sync to second hit
            setTimeout(() => { document.querySelector('.l-e').classList.add('drop-e'); }, 300); // Sync to third hit
        }, 1200); // AI fade in completes
        
        // Wait 1.5s after full logo (1.2 + 2.5 = 3.7) -> 5.2s
        setTimeout(() => {
            splash.style.transition = 'opacity 1.5s';
            splash.style.opacity = '0';
        }, 5200); 

        // Hide splash after 1.5s fade out -> 6.7s, then show terminal
        setTimeout(() => {
            splash.style.display = 'none';
            document.getElementById('crt-container').style.display = 'block';
            state = 1;
            typeText(i18n['en'].welcome);
        }, 6700);
        return;
    }

    if (isTyping || state === 0 || state >= 12) return;
    
    if (e.key === 'Enter') {
        sfxEnter();
        submitInput(inputBuf);
    } else if (e.key.length === 1) {
        sfxKey();
        inputBuf += e.key;
        inputText.textContent = inputBuf;
    } else if (e.key === 'Backspace') {
        sfxKey();
        inputBuf = inputBuf.slice(0, -1);
        inputText.textContent = inputBuf;
    }
});

// Init
inputLine.style.display = 'none';
state = -1; // wait for first key
