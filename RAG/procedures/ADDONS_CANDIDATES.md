# ADDONS_CANDIDATES - RAG-реестр внешних проектов для JewAI

**Обновлён:** 2026-11-10, 10C (Семён).
**Назначение:** реестр проектов, которые можно интегрировать как аддоны/расширения.
**Формат:** GitHub URL, идеология, лицензия, что брать, куда в JewAI.

---

## 1. Голос и общение

### 1.1 faster-whisper (STT)
- URL: https://github.com/SYSTRAN/faster-whisper
- Что: Whisper на CTranslate2, 4x быстрее, RU ок.
- Идеология: быстрый инференс без потери точности.
- Лицензия: MIT.
- Брать: pip install faster-whisper, модели с HF (large-v3 / small).
- Куда: замена текущего STT.

### 1.2 Silero VAD
- URL: https://github.com/snakers4/silero-vad
- Что: детектор голосовой активности, отсекает тишину/шум, CPU.
- Идеология: enterprise-grade VAD с открытым кодом.
- Лицензия: CC BY-NC-SA (некоммерческое).
- Брать: pip install silero-vad.
- Куда: фильтр перед STT.

### 1.3 Piper (TTS)
- URL: https://github.com/rhasspy/piper (форк OHF-Voice/piper1-gpl)
- Что: локальный нейро-TTS, RU-голоса, 20МБ на голос, edge-устройства.
- Идеология: TTS без облака.
- Лицензия: MIT (оригинал), GPL (форк).
- Брать: бинарник + .onnx с HF rhasspy/piper-voices.
- Куда: замена PowerShell SAPI, приятный голос.

### 1.4 Porcupine (wake-word)
- URL: https://github.com/Picovoice/Porcupine
- Что: детектор «Джошуа», always-listening, RU-модели.
- Идеология: always-listening без облака, кастомные слова.
- Лицензия: Apache 2.0 (free tier).
- Брать: pip install pvporcupine + AccessKey Picovoice Console.
- Куда: будильник агента.

### 1.5 openWakeWord (альтернатива)
- URL: https://github.com/dscripka/openWakeWord
- Что: открытый wake-word, обучаемый, свои модели.
- Идеология: полностью открытый wake-word.
- Лицензия: Apache 2.0.
- Брать: pip install openwakeword, модели из релизов.
- Куда: если не хочется зависимости от Picovoice.

### 1.6 RealtimeSTT + RealtimeTTS
- URL: https://github.com/KoljaB/RealtimeSTT
- Что: готовая связка «услышал -> распознал -> ответил голосом» для LLM, VAD+wake+streaming.
- Идеология: разговор с ИИ в реальном времени, локально.
- Лицензия: MIT.
- Брать: pip install RealtimeSTT RealtimeTTS.
- Куда: быстрый голосовой агент без склейки трёх библиотек.

## 2. Рисование и изображения

### 2.1 ComfyUI
- URL: https://github.com/Comfy-Org/ComfyUI
- Что: node-граф для SD, txt2img/img2img/inpaint/upscale, API.
- Идеология: максимальный контроль над каждым шагом.
- Лицензия: GPL-3.0.
- Брать: git clone + pip install -r requirements.txt, API на :8188.
- Куда: основной движок «нарисуй».

### 2.2 Fooocus
- URL: https://github.com/lllyasviel/Fooocus
- Что: «SD без боли», одна кнопка, хорошие результаты из коробки.
- Идеология: сфокусируйся на промпте, не на параметрах.
- Лицензия: GPL-3.0.
- Брать: Windows-архив из релизов.
- Куда: простой режим «нарисуй кота».

### 2.3 InvokeAI
- URL: https://github.com/invoke-ai/InvokeAI
- Что: профессиональный WebUI, чистый API, canvas, inpaint.
- Идеология: индустриальный движок визуального контента.
- Лицензия: Apache 2.0.
- Брать: pip install invokeai, invokeai-web.
- Куда: программное рисование и редактирование.

### 2.4 Draw Things
- URL: https://drawthings.ai/
- Что: локальное приложение Mac/Windows, Metal/CUDA, без Python.
- Идеология: SD на устройстве без зависимостей.
- Лицензия: MIT.
- Куда: лёгкий fallback.

### 2.5 stable-diffusion.cpp
- URL: https://github.com/leejet/stable-diffusion.cpp
- Что: SD на C++/ggml без PyTorch, CPU.
- Идеология: SD без Python и GPU.
- Лицензия: MIT.
- Куда: слабые машины.

### 2.6 Krita AI Diffusion
- URL: https://github.com/Acly/krita-ai-diffusion
- Что: плагин Krita для inpaint, генерации, оживления набросков.
- Идеология: рисуй руками, AI помогает.
- Лицензия: GPL.
- Куда: связка с рисованием руками.

## 3. Память и знания

### 3.1 mem0
- URL: https://github.com/mem0ai/mem0
- Что: слой памяти агента, предпочтения/сессии/факты, любые LLM.
- Идеология: универсальная память для AI-агентов.
- Лицензия: Apache 2.0.
- Брать: pip install mem0ai, cloud или self-hosted.
- Куда: Семён и Аркаша помнят между сессиями.

### 3.2 Chroma
- URL: https://github.com/chroma-core/chroma
- Что: векторная БД для RAG, локальная.
- Идеология: open-source база эмбеддингов.
- Лицензия: Apache 2.0.
- Куда: эмбеддинги документов/логов.

### 3.3 LlamaIndex
- URL: https://github.com/run-llama/llama_index
- Что: фреймворк RAG, индексы, ретриверы, агенты.
- Идеология: свяжи LLM с данными.
- Лицензия: MIT.
- Куда: идеи для улучшения RAG (не тащить целиком).

### 3.4 Qdrant
- URL: https://github.com/qdrant/qdrant
- Что: векторная БД на Rust, production, фильтрация.
- Идеология: высокопроизводительный поиск.
- Лицензия: Apache 2.0.
- Куда: если Chroma станет мало.

### 3.5 LanceDB
- URL: https://github.com/lancedb/lancedb
- Что: векторная БД на файлах, embedded.
- Идеология: векторный поиск как SQLite.
- Лицензия: Apache 2.0.
- Куда: лёгкая замена Chroma.

### 3.6 Khoj
- URL: https://github.com/khoj-ai/khoj
- Что: «второй мозг»: RAG по заметкам, голос, агенты.
- Идеология: личный AI, знающий твои данные.
- Лицензия: AGPL.
- Куда: образец UX и архитектуры памяти.

### 3.7 AnythingLLM
- URL: https://github.com/Mintplex-Labs/anything-llm
- Что: готовый чат с документами, локальный RAG.
- Идеология: чат с файлами без облака.
- Лицензия: MIT.
- Куда: образец интерфейса.

### 3.8 Letta (MemGPT)
- URL: https://github.com/letta-ai/letta
- Что: агент с долгосрочной памятью, саморедактирование.
- Идеология: память как часть агента.
- Лицензия: Apache 2.0.
- Куда: концепт самообучающейся памяти.

## 4. Агентские возможности

### 4.1 LangGraph
- URL: https://github.com/langchain-ai/langgraph
- Что: граф-оркестрация stateful-агентов.
- Идеология: низкоуровневый контроль, агент как граф.
- Лицензия: MIT.
- Брать: pip install langgraph.
- Куда: переписать логику моста как граф (idle->collect->exec->report).

### 4.2 CrewAI
- URL: https://github.com/crewAIInc/crewAI
- Что: оркестрация команды агентов с ролями.
- Идеология: агенты как команда с ролями.
- Лицензия: MIT.
- Куда: образец триумвирата A/B/C/D.

### 4.3 AutoGen (Microsoft)
- URL: https://github.com/microsoft/autogen
- Что: мультиагентные диалоги.
- Идеология: агенты решают задачи вместе.
- Лицензия: Apache 2.0.
- Куда: образец протокола общения.

### 4.4 OpenHands
- URL: https://github.com/All-Hands-AI/OpenHands
- Что: агент-программист с песочницей.
- Идеология: автономный разработчик.
- Лицензия: MIT.
- Куда: образец для агента-кодера.

### 4.5 Dify
- URL: https://github.com/langgenius/dify
- Что: платформа LLM-приложений, RAG+агенты+API.
- Идеология: собери AI-приложение без кода.
- Лицензия: Apache 2.0 (с ограничениями).
- Куда: альтернатива Mainframe, тяжелее.

### 4.6 Flowise
- URL: https://github.com/FlowiseAI/Flowise
- Что: no-code конструктор LLM-флоу.
- Идеология: drag&drop для LLM.
- Лицензия: Apache 2.0.
- Куда: прототипирование сценариев.

## 5. Автоматизация

### 5.1 n8n
- URL: https://github.com/n8n-io/n8n
- Что: workflow-автоматизация, 400+ интеграций, self-hosted.
- Идеология: fair-code автоматизация.
- Лицензия: Sustainable Use.
- Куда: склейка сценариев (почта -> агент -> уведомление).

### 5.2 Home Assistant
- URL: https://github.com/home-assistant/core
- Что: платформа умного дома, локальный контроль.
- Идеология: локальность и приватность.
- Лицензия: Apache 2.0.
- Куда: управление устройствами через агента.

## 6. OCR и Vision

### 6.1 Tesseract OCR
- URL: https://github.com/tesseract-ocr/tesseract
- Что: OCR, 130 языков включая RU.
- Идеология: открытый OCR с 1985.
- Лицензия: Apache 2.0.
- Брать: бинарник + pytesseract.
- Куда: «прочитай текст с картинки».

### 6.2 PaddleOCR
- URL: https://github.com/PaddlePaddle/PaddleOCR
- Что: OCR Baidu, точный для RU/CN.
- Идеология: промышленный OCR.
- Лицензия: Apache 2.0.
- Куда: альтернатива Tesseract.

### 6.3 Moondream
- URL: https://github.com/vikhyat/moondream
- Что: VLM 1.7B, описывает картинки, отвечает на вопросы.
- Идеология: vision-LLM, работающая везде.
- Лицензия: Apache 2.0.
- Куда: «что на картинке?».

### 6.4 LLaVA
- URL: https://github.com/haotian-liu/LLaVA
- Что: большая VLM, близка к GPT-4V.
- Идеология: visual instruction tuning.
- Лицензия: Apache 2.0 (модели могут отличаться).
- Куда: если Moondream мало.

### 6.5 Qwen-VL
- URL: https://github.com/QwenLM/Qwen-VL
- Что: VLM Alibaba, RU/CN хорошие.
- Идеология: сильная открытая VLM.
- Лицензия: Apache 2.0.
- Куда: ещё одна VLM-опция.

## 7. Локальные LLM-серверы

### 7.1 Ollama
- URL: https://github.com/ollama/ollama
- Что: локальный сервер LLM, OpenAI-API, Qwen/Llama/Mistral/Gemma.
- Идеология: запусти LLM одной командой.
- Лицензия: MIT.
- Брать: ollama.com, ollama run qwen2.5:7b.
- Куда: замена LocalAI в v6.

### 7.2 llama.cpp
- URL: https://github.com/ggerganov/llama.cpp
- Что: LLM на C++, GGUF, CPU/GPU.
- Идеология: максимум производительности на потребительском железе.
- Лицензия: MIT.
- Куда: нижний слой Ollama/LocalAI.

### 7.3 LocalAI
- URL: https://github.com/mudler/LocalAI
- Что: мультимодельный локальный сервер (LLM, изображения, аудио).
- Идеология: OpenAI-API для всего локального.
- Лицензия: MIT.
- Куда: текущий кандидат в v6.

## 8. Приоритеты 10C

1. Ollama - замена LocalAI, проще/быстрее.
2. faster-whisper + Silero VAD + Piper - голосовой цикл.
3. Porcupine или openWakeWord - «Джошуа».
4. ComfyUI + Fooocus - рисование (API + простой).
5. mem0 - память между сессиями.
6. Tesseract - OCR (быстро, бесплатно).
7. Moondream - Vision (лёгкая).
8. n8n - автоматизация (по необходимости).

**Идеология:** локально, офлайн, заменяемо. JewAI - оркестратор, не монолит.

## 9. Как внедрять

- Голос: voice_loop.py, слушает wake-word, распознаёт, шлёт в мост, озвучивает.
- Рисование: HTTP-клиент ComfyUI, команда «нарисуй ...» -> API.
- Память: mem0 поверх ledger.json + SESSION_STATE.md.
- Vision/OCR: «прочитай картинку <path>» -> Tesseract/Moondream.
- Автоматизация: n8n как внешний сервис, агент дёргает webhook.

Dixi. 10C, 2026-11-10.
