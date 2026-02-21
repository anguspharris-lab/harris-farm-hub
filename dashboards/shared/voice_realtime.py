"""
Harris Farm Hub — OpenAI Realtime Voice Component
Connects via WebSocket to gpt-4o-realtime-preview for voice-driven data queries.
Falls back to existing Web Speech API implementation if connection fails.

Usage:
    from shared.voice_realtime import render_voice_data_box
    render_voice_data_box("sales", tools=[...])
"""

import json
import os

import streamlit as st
import streamlit.components.v1 as components

API_URL = os.getenv("API_URL", "http://localhost:8000")
REALTIME_KEY = os.getenv("OPENAI_REALTIME_API_KEY", "")

# Default tool: query the Hub backend (works for any dashboard context)
DEFAULT_TOOL = {
    "type": "function",
    "name": "query_hub_data",
    "description": (
        "Query Harris Farm Hub data. Routes to the correct database "
        "(weekly sales, profitability, market share, PLU, transactions) "
        "based on the dataset parameter. Ask natural language questions "
        "about stores, products, sales, margins, customers, or market share."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Natural language data question",
            },
            "dataset": {
                "type": "string",
                "description": "Dataset context for routing the query",
                "enum": [
                    "sales", "profitability", "customers", "market_share",
                    "trending", "store_ops", "product_intel", "revenue_bridge",
                    "buying_hub", "plu", "general",
                ],
            },
        },
        "required": ["question", "dataset"],
    },
}

# Dashboard-specific tool definitions
DASHBOARD_TOOLS = {
    "sales": [
        {
            "type": "function",
            "name": "get_sales_summary",
            "description": "Get sales and gross profit summary by store, department, or period. Can compare budget vs actual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Sales question, e.g. 'top 5 stores by sales this week'"},
                },
                "required": ["question"],
            },
        },
    ],
    "profitability": [
        {
            "type": "function",
            "name": "get_profitability_data",
            "description": "Get gross profit margins, shrinkage, wastage by store or department. Includes budget variance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Profitability question"},
                },
                "required": ["question"],
            },
        },
    ],
    "customers": [
        {
            "type": "function",
            "name": "get_customer_insights",
            "description": "Get customer counts, segments, retention, and demographic data by postcode or store.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Customer analytics question"},
                },
                "required": ["question"],
            },
        },
    ],
    "market_share": [
        {
            "type": "function",
            "name": "get_market_share_data",
            "description": "Get market share percentages, penetration, and spend per customer by postcode, state, or store trade area. CBAS modelled data — share % is reliable, dollar values directional only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Market share question"},
                },
                "required": ["question"],
            },
        },
    ],
    "store_ops": [
        {
            "type": "function",
            "name": "get_store_operations",
            "description": "Get transaction-level store operations data: items sold, basket size, staff metrics, stocktake variance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Store operations question"},
                },
                "required": ["question"],
            },
        },
    ],
    "product_intel": [
        {
            "type": "function",
            "name": "get_product_intelligence",
            "description": "Get product-level data: PLU performance, price analysis, margin by product, wastage by item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Product intelligence question"},
                },
                "required": ["question"],
            },
        },
    ],
    "revenue_bridge": [
        {
            "type": "function",
            "name": "get_revenue_bridge",
            "description": "Get revenue bridge analysis: sales drivers, period comparisons, variance decomposition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Revenue bridge question"},
                },
                "required": ["question"],
            },
        },
    ],
    "buying_hub": [
        {
            "type": "function",
            "name": "get_buying_data",
            "description": "Get buying and procurement data: supplier performance, cost analysis, order patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Buying hub question"},
                },
                "required": ["question"],
            },
        },
    ],
    "trending": [
        {
            "type": "function",
            "name": "get_trending_data",
            "description": "Get trending analysis: momentum indicators, emerging patterns, week-over-week changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Trending analysis question"},
                },
                "required": ["question"],
            },
        },
    ],
    "plu": [
        {
            "type": "function",
            "name": "get_plu_data",
            "description": "Get PLU-level intelligence: 27M+ weekly records, wastage hotspots, stocktake variance, margin by PLU.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "PLU intelligence question"},
                },
                "required": ["question"],
            },
        },
    ],
}


def render_voice_data_box(page_context: str, tools=None):
    """Render the OpenAI Realtime voice data box.

    Args:
        page_context: Dashboard context for routing queries.
        tools: Optional list of additional tool definitions.
               If None, uses defaults for the page_context.
    """
    # Build tools list
    all_tools = [DEFAULT_TOOL]
    if tools:
        all_tools.extend(tools)
    elif page_context in DASHBOARD_TOOLS:
        all_tools.extend(DASHBOARD_TOOLS[page_context])

    tools_json = json.dumps(all_tools)
    api_key = REALTIME_KEY
    api_url = API_URL

    # If no API key, fall back to label-only mode (component still renders
    # but uses Web Speech API fallback)
    has_realtime = bool(api_key)

    _render_component(
        page_context=page_context,
        api_key=api_key,
        api_url=api_url,
        tools_json=tools_json,
        has_realtime=has_realtime,
    )


def _render_component(
    page_context: str,
    api_key: str,
    api_url: str,
    tools_json: str,
    has_realtime: bool,
):
    """Render the HTML/JS voice component."""
    # Escape for safe embedding
    escaped_key = api_key.replace("'", "\\'")
    escaped_url = api_url.replace("'", "\\'")

    html = f"""
    <style>
        #vdb-container {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 8px 0;
        }}
        #vdb-controls {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        #vdb-mic-btn {{
            width: 52px; height: 52px;
            border-radius: 50%;
            border: 2px solid #e0e0e0;
            background: #f8f9fa;
            cursor: pointer;
            font-size: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        #vdb-mic-btn:hover {{ background: #e8f5e9; border-color: #4ba021; }}
        #vdb-mic-btn.listening {{
            background: #ef4444;
            border-color: #dc2626;
            animation: vdb-pulse 1.5s infinite;
        }}
        #vdb-mic-btn.thinking {{
            background: #f59e0b;
            border-color: #d97706;
            animation: vdb-spin 1s infinite linear;
        }}
        #vdb-mic-btn.speaking {{
            background: #4ba021;
            border-color: #3d8a1b;
            animation: vdb-pulse 1s infinite;
        }}
        @keyframes vdb-pulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(75,160,33,0.4); }}
            50% {{ box-shadow: 0 0 0 12px rgba(75,160,33,0); }}
        }}
        @keyframes vdb-spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        #vdb-status {{
            color: #666;
            font-size: 13px;
            flex: 1;
        }}
        #vdb-status .state {{ font-weight: 600; }}
        #vdb-transcript {{
            margin-top: 8px;
            padding: 8px 12px;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 13px;
            color: #333;
            display: none;
            max-height: 120px;
            overflow-y: auto;
        }}
        #vdb-transcript.active {{ display: block; }}
        .vdb-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
        }}
        .vdb-badge.realtime {{ background: #dcfce7; color: #166534; }}
        .vdb-badge.fallback {{ background: #fef3c7; color: #92400e; }}
    </style>

    <div id="vdb-container">
        <div id="vdb-controls">
            <button id="vdb-mic-btn" onclick="vdbToggle()" title="Click to talk to your data">
                <span id="vdb-mic-icon">&#127908;</span>
            </button>
            <div id="vdb-status">
                <span class="vdb-badge {'realtime' if has_realtime else 'fallback'}">
                    {'Realtime' if has_realtime else 'Voice'}
                </span>
                <span id="vdb-state-text">Click mic to ask a question</span>
            </div>
        </div>
        <div id="vdb-transcript"></div>
    </div>

    <script>
    (function() {{
        const API_KEY = '{escaped_key}';
        const API_URL = '{escaped_url}';
        const PAGE_CONTEXT = '{page_context}';
        const TOOLS = {tools_json};
        const HAS_REALTIME = {'true' if has_realtime else 'false'};

        const btn = document.getElementById('vdb-mic-btn');
        const icon = document.getElementById('vdb-mic-icon');
        const stateText = document.getElementById('vdb-state-text');
        const transcript = document.getElementById('vdb-transcript');

        let ws = null;
        let audioCtx = null;
        let mediaStream = null;
        let scriptNode = null;
        let playbackQueue = [];
        let isPlaying = false;
        let state = 'idle'; // idle, connecting, listening, thinking, speaking
        let currentCallId = null;

        function setState(newState, msg) {{
            state = newState;
            btn.className = newState === 'idle' ? '' : newState;
            stateText.textContent = msg || '';

            const icons = {{
                idle: String.fromCodePoint(0x1F3A4),
                connecting: String.fromCodePoint(0x23F3),
                listening: String.fromCodePoint(0x1F534),
                thinking: String.fromCodePoint(0x1F4AD),
                speaking: String.fromCodePoint(0x1F50A),
            }};
            icon.textContent = icons[newState] || String.fromCodePoint(0x1F3A4);
        }}

        function showTranscript(text) {{
            transcript.textContent = text;
            transcript.classList.add('active');
        }}

        function hideTranscript() {{
            transcript.classList.remove('active');
        }}

        // ── Realtime WebSocket Mode ──────────────────────────────────────

        async function startRealtime() {{
            setState('connecting', 'Connecting...');

            try {{
                audioCtx = new (window.AudioContext || window.webkitAudioContext)({{
                    sampleRate: 24000
                }});

                mediaStream = await navigator.mediaDevices.getUserMedia({{
                    audio: {{ sampleRate: 24000, channelCount: 1, echoCancellation: true }}
                }});

                ws = new WebSocket(
                    'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview',
                    ['openai-insecure-api-key.' + API_KEY, 'openai-beta.realtime-v1']
                );

                // Auth via first message after open
                ws.onopen = () => {{
                    // Send session config
                    ws.send(JSON.stringify({{
                        type: 'session.update',
                        session: {{
                            modalities: ['text', 'audio'],
                            instructions: 'You are the Harris Farm Hub voice assistant. ' +
                                'You help staff query data from dashboards about sales, profitability, ' +
                                'customers, market share, and operations. ' +
                                'Currently on the ' + PAGE_CONTEXT.replace('_', ' ') + ' dashboard. ' +
                                'Be concise and friendly. Use Australian English. ' +
                                'When you need data, call the available functions.',
                            voice: 'sage',
                            input_audio_format: 'pcm16',
                            output_audio_format: 'pcm16',
                            input_audio_transcription: {{ model: 'whisper-1' }},
                            turn_detection: {{
                                type: 'server_vad',
                                threshold: 0.5,
                                prefix_padding_ms: 300,
                                silence_duration_ms: 500,
                            }},
                            tools: TOOLS,
                        }}
                    }}));

                    startMicCapture();
                    setState('listening', 'Listening... speak your question');
                }};

                ws.onmessage = handleRealtimeEvent;

                ws.onerror = (e) => {{
                    console.error('WebSocket error:', e);
                    stopRealtime();
                    // Fall back
                    if (HAS_REALTIME) {{
                        showTranscript('Realtime connection failed. Using voice fallback.');
                        setTimeout(() => {{ startFallback(); }}, 1000);
                    }}
                }};

                ws.onclose = () => {{
                    if (state !== 'idle') {{
                        stopMicCapture();
                        setState('idle', 'Disconnected');
                    }}
                }};

            }} catch (e) {{
                console.error('Realtime setup failed:', e);
                setState('idle', 'Connection failed — try again');
                startFallback();
            }}
        }}

        function handleRealtimeEvent(event) {{
            const data = JSON.parse(event.data);

            switch (data.type) {{
                case 'session.created':
                    break;

                case 'input_audio_buffer.speech_started':
                    setState('listening', 'Hearing you...');
                    // Stop any playback
                    playbackQueue = [];
                    break;

                case 'input_audio_buffer.speech_stopped':
                    setState('thinking', 'Processing...');
                    break;

                case 'conversation.item.input_audio_transcription.completed':
                    if (data.transcript) {{
                        showTranscript('You: ' + data.transcript);
                    }}
                    break;

                case 'response.audio.delta':
                    if (data.delta) {{
                        playbackQueue.push(data.delta);
                        if (!isPlaying) playAudioQueue();
                        setState('speaking', 'Speaking...');
                    }}
                    break;

                case 'response.audio_transcript.delta':
                    if (data.delta) {{
                        const current = transcript.textContent || '';
                        if (current.startsWith('Assistant:')) {{
                            showTranscript(current + data.delta);
                        }} else {{
                            showTranscript('Assistant: ' + data.delta);
                        }}
                    }}
                    break;

                case 'response.function_call_arguments.done':
                    handleFunctionCall(data);
                    break;

                case 'response.done':
                    if (state === 'speaking') {{
                        // Wait for audio to finish, then go back to listening
                        setTimeout(() => {{
                            if (state !== 'idle') setState('listening', 'Listening...');
                        }}, 1500);
                    }}
                    break;

                case 'error':
                    console.error('Realtime error:', data.error);
                    showTranscript('Error: ' + (data.error?.message || 'Unknown error'));
                    break;
            }}
        }}

        async function handleFunctionCall(data) {{
            setState('thinking', 'Querying data...');
            const callId = data.call_id;
            const fnName = data.name;
            let args = {{}};
            try {{ args = JSON.parse(data.arguments || '{{}}'); }} catch(e) {{}}

            // Route all function calls through the Hub backend
            let question = args.question || args.query || JSON.stringify(args);
            let dataset = args.dataset || PAGE_CONTEXT;

            try {{
                const resp = await fetch(API_URL + '/api/query', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        question: question,
                        dataset: dataset,
                        user_id: 'hub_voice',
                    }}),
                }});
                const result = await resp.json();

                // Send function result back to the model
                ws.send(JSON.stringify({{
                    type: 'conversation.item.create',
                    item: {{
                        type: 'function_call_output',
                        call_id: callId,
                        output: JSON.stringify({{
                            explanation: result.explanation || 'No results found.',
                            data: (result.results || []).slice(0, 20),
                            sql: result.generated_sql || '',
                        }}),
                    }}
                }}));

                // Ask model to continue responding
                ws.send(JSON.stringify({{ type: 'response.create' }}));

            }} catch (e) {{
                // Send error back
                ws.send(JSON.stringify({{
                    type: 'conversation.item.create',
                    item: {{
                        type: 'function_call_output',
                        call_id: callId,
                        output: JSON.stringify({{ error: 'Backend query failed: ' + e.message }}),
                    }}
                }}));
                ws.send(JSON.stringify({{ type: 'response.create' }}));
            }}
        }}

        // ── Audio Capture ────────────────────────────────────────────────

        function startMicCapture() {{
            if (!audioCtx || !mediaStream) return;

            const source = audioCtx.createMediaStreamSource(mediaStream);
            // Use ScriptProcessor for broad compatibility
            scriptNode = audioCtx.createScriptProcessor(4096, 1, 1);

            scriptNode.onaudioprocess = (e) => {{
                if (!ws || ws.readyState !== WebSocket.OPEN) return;
                if (state === 'idle') return;

                const input = e.inputBuffer.getChannelData(0);
                // Convert float32 to int16
                const pcm16 = new Int16Array(input.length);
                for (let i = 0; i < input.length; i++) {{
                    const s = Math.max(-1, Math.min(1, input[i]));
                    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }}

                // Base64 encode
                const bytes = new Uint8Array(pcm16.buffer);
                let binary = '';
                for (let i = 0; i < bytes.length; i++) {{
                    binary += String.fromCharCode(bytes[i]);
                }}
                const b64 = btoa(binary);

                ws.send(JSON.stringify({{
                    type: 'input_audio_buffer.append',
                    audio: b64,
                }}));
            }};

            source.connect(scriptNode);
            scriptNode.connect(audioCtx.destination);
        }}

        function stopMicCapture() {{
            if (scriptNode) {{
                scriptNode.disconnect();
                scriptNode = null;
            }}
            if (mediaStream) {{
                mediaStream.getTracks().forEach(t => t.stop());
                mediaStream = null;
            }}
        }}

        // ── Audio Playback ───────────────────────────────────────────────

        async function playAudioQueue() {{
            isPlaying = true;
            while (playbackQueue.length > 0) {{
                const b64 = playbackQueue.shift();
                try {{
                    const binary = atob(b64);
                    const bytes = new Uint8Array(binary.length);
                    for (let i = 0; i < binary.length; i++) {{
                        bytes[i] = binary.charCodeAt(i);
                    }}
                    const pcm16 = new Int16Array(bytes.buffer);
                    const float32 = new Float32Array(pcm16.length);
                    for (let i = 0; i < pcm16.length; i++) {{
                        float32[i] = pcm16[i] / 32768.0;
                    }}

                    const buffer = audioCtx.createBuffer(1, float32.length, 24000);
                    buffer.getChannelData(0).set(float32);
                    const src = audioCtx.createBufferSource();
                    src.buffer = buffer;
                    src.connect(audioCtx.destination);
                    src.start();

                    // Wait for chunk to play
                    await new Promise(resolve => {{
                        src.onended = resolve;
                        setTimeout(resolve, (float32.length / 24000) * 1000 + 10);
                    }});
                }} catch (e) {{
                    console.error('Playback error:', e);
                }}
            }}
            isPlaying = false;
        }}

        // ── Stop/Cleanup ─────────────────────────────────────────────────

        function stopRealtime() {{
            if (ws) {{
                ws.close();
                ws = null;
            }}
            stopMicCapture();
            if (audioCtx) {{
                audioCtx.close().catch(() => {{}});
                audioCtx = null;
            }}
            playbackQueue = [];
            isPlaying = false;
            setState('idle', 'Click mic to ask a question');
            hideTranscript();
        }}

        // ── Fallback: Web Speech API ─────────────────────────────────────

        let fallbackRecognition = null;

        function startFallback() {{
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SR) {{
                showTranscript('Voice not supported in this browser');
                return;
            }}

            fallbackRecognition = new SR();
            fallbackRecognition.continuous = false;
            fallbackRecognition.interimResults = true;
            fallbackRecognition.lang = 'en-AU';

            fallbackRecognition.onresult = (e) => {{
                let text = '';
                for (let i = e.resultIndex; i < e.results.length; i++) {{
                    text += e.results[i][0].transcript;
                }}
                showTranscript('You: ' + text);

                if (e.results[e.results.length - 1].isFinal) {{
                    // Send to backend
                    queryBackend(text);
                }}
            }};

            fallbackRecognition.onend = () => {{
                if (state === 'listening') setState('thinking', 'Processing...');
            }};

            fallbackRecognition.onerror = (e) => {{
                setState('idle', e.error === 'not-allowed' ?
                    'Microphone access denied' : 'Voice error — try again');
            }};

            setState('listening', 'Listening (fallback mode)...');
            fallbackRecognition.start();
        }}

        async function queryBackend(question) {{
            setState('thinking', 'Querying data...');
            try {{
                const resp = await fetch(API_URL + '/api/query', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        question: question,
                        dataset: PAGE_CONTEXT,
                        user_id: 'hub_voice',
                    }}),
                }});
                const result = await resp.json();
                const answer = result.explanation || 'No answer available.';
                showTranscript('Assistant: ' + answer);

                // Read answer aloud via SpeechSynthesis
                const synth = window.parent.speechSynthesis || window.speechSynthesis;
                if (synth) {{
                    const utt = new SpeechSynthesisUtterance(answer);
                    utt.lang = 'en-AU';
                    utt.rate = 0.95;
                    setState('speaking', 'Speaking...');
                    utt.onend = () => setState('idle', 'Click mic to ask another question');
                    synth.speak(utt);
                }} else {{
                    setState('idle', 'Done — click mic for another question');
                }}
            }} catch (e) {{
                showTranscript('Error: Could not connect to backend. Is the API running?');
                setState('idle', 'Query failed — try again');
            }}
        }}

        // ── Main Toggle ──────────────────────────────────────────────────

        window.vdbToggle = function() {{
            if (state !== 'idle') {{
                // Stop everything
                if (ws) stopRealtime();
                else if (fallbackRecognition) {{
                    fallbackRecognition.stop();
                    fallbackRecognition = null;
                }}
                const synth = window.parent.speechSynthesis || window.speechSynthesis;
                if (synth) synth.cancel();
                setState('idle', 'Click mic to ask a question');
                hideTranscript();
                return;
            }}

            if (HAS_REALTIME && API_KEY) {{
                startRealtime();
            }} else {{
                startFallback();
            }}
        }};

    }})();
    </script>
    """
    components.html(html, height=140, scrolling=False)
