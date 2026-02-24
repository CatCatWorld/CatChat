// ====================== Constants ======================
const catEmojis = ['🐱','😺','😸','😹','😻','😼','😽','🙀','😿','😾','🐈','🐈‍⬛','🐾','🦁'];
const catColors = ['#f582ae','#ff8c42','#ffd803','#a8d8a8','#8bd3dd','#b8a9c9','#f6a6b2','#ffb347','#87ceeb','#dda0dd','#98d8c8','#f7dc6f'];
const CAT_BREED_AVATARS = [
    { breed:'英国短毛猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,british-shorthair?lock=101' },
    { breed:'美国短毛猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,american-shorthair?lock=102' },
    { breed:'布偶猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,ragdoll?lock=103' },
    { breed:'暹罗猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,siamese?lock=104' },
    { breed:'波斯猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,persian-cat?lock=105' },
    { breed:'缅因猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,maine-coon?lock=106' },
    { breed:'挪威森林猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,norwegian-forest-cat?lock=107' },
    { breed:'俄罗斯蓝猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,russian-blue?lock=108' },
    { breed:'孟加拉猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,bengal-cat?lock=109' },
    { breed:'斯芬克斯猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,sphynx-cat?lock=110' },
    { breed:'阿比西尼亚猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,abyssinian-cat?lock=111' },
    { breed:'苏格兰折耳猫', icon:'🐱', imageUrl:'https://loremflickr.com/320/320/cat-face,closeup,portrait,scottish-fold?lock=112' }
];
const PROVIDERS = {
    openai: { name:'OpenAI',icon:'🟢',defaultUrl:'https://api.openai.com/v1/chat/completions',urlHint:'支持所有 OpenAI 兼容接口',models:['gpt-4o','gpt-4o-mini','gpt-4-turbo','gpt-3.5-turbo','deepseek-chat','qwen-turbo'],defaultModel:'gpt-4o-mini',badgeClass:'openai' },
    claude: { name:'Claude',icon:'🟠',defaultUrl:'https://api.anthropic.com/v1/messages',urlHint:'Anthropic 官方或代理地址',models:['claude-sonnet-4-20250514','claude-haiku-4-20250414','claude-3-5-sonnet-20241022','claude-3-opus-20240229'],defaultModel:'claude-sonnet-4-20250514',badgeClass:'claude' },
    glm: { name:'GLM',icon:'🔵',defaultUrl:'https://open.bigmodel.cn/api/paas/v4/chat/completions',urlHint:'智谱 AI 开放平台',models:['glm-4-plus','glm-4-flash','glm-4-air','glm-4-long','glm-4'],defaultModel:'glm-4-flash',badgeClass:'glm' },
    siliconflow: { name:'硅基流动',icon:'🟣',defaultUrl:'https://api.siliconflow.cn/v1/chat/completions',urlHint:'SiliconFlow OpenAI 兼容接口',models:['Pro/zai-org/GLM-4.7','deepseek-ai/DeepSeek-V3','Qwen/Qwen2.5-72B-Instruct','THUDM/glm-4-9b-chat'],defaultModel:'Pro/zai-org/GLM-4.7',badgeClass:'siliconflow' }
};
const WEREWOLF_ROLES = [
    { id:'werewolf',name:'狼人',icon:'🐺',team:'wolf',desc:'每晚可以选择猎杀一名玩家' },
    { id:'villager',name:'村民',icon:'👨‍🌾',team:'good',desc:'没有特殊能力但投票至关重要' },
    { id:'seer',name:'预言家',icon:'🔮',team:'good',desc:'每晚可查验一名玩家身份' },
    { id:'witch',name:'女巫',icon:'🧪',team:'good',desc:'拥有一瓶解药和一瓶毒药' },
    { id:'hunter',name:'猎人',icon:'🏹',team:'good',desc:'被淘汰时可开枪带走一人' },
    { id:'guard',name:'守卫',icon:'🛡️',team:'good',desc:'每晚可以守护一名玩家' },
    { id:'fool',name:'白痴',icon:'🤹',team:'good',desc:'白天被放逐时可翻牌免死一次' }
];
const MONITOR_CONFIG_STORAGE_KEY = 'catchat.monitor.config.v1';
const TTS_VOICE_MAP_STORAGE_KEY = 'catchat.tts.voice.map.v1';
const TTS_SETTINGS_STORAGE_KEY = 'catchat.tts.settings.v1';
const WEREWOLF_AUTO_ADVANCE_DELAY_MS = 12000;
const WEREWOLF_BACKEND_AUTO_ADVANCE_DELAY_MS = 1200;

// ====================== State ======================
let cats = [], messages = [];
let selectedEmoji = '🐱', selectedColor = '#f582ae', selectedProvider = 'openai';
let selectedAvatarUrl = '';
let selectedBreed = CAT_BREED_AVATARS[0].breed;
let gameMode = 'discuss', judgeView = true;
let wfState = {
    active:false,
    phase:'idle',
    round:0,
    roles:{},
    eliminated:[],
    eliminatedCauseByCatId:{},
    phaseMessages:[],
    backendLinked:true,
    linkedRoomId:'',
    hideNightRoleForAudience:true
};
let wfAutoAdvanceTimer = null;
let plState = { active:false, phase:'idle', requirement:'', roles:{}, results:{} };
let cliProxy = { enabled: false, url: 'http://localhost:3456', connected: false };
let dbState = { active:false, round:0, maxRounds:2, turnIndex:0, order:[], queue:[], speaking:false };
let monitorState = {
    apiBase: 'http://127.0.0.1:8000',
    roomId: '',
    ownerId: 'cat_01',
    playerCount: 11,
    viewMode: 'god',
    ws: null,
    isConnected: false,
    phaseLog: [],
    speechTimeline: [],
    speechSeenKeys: {},
    speechRenderedKeys: {},
    narrationSeenKeys: {},
    lastStateOrder: -1,
    wsLastEventId: 0,
    pendingRoomState: null,
    roomStateFlushScheduled: false,
    phaseStatePullTimer: null,
    pendingPhaseChangedPayload: null,
    players: [],
    playerMap: {},
    playerBindings: {},
    catOnlineById: {},
    agentHost: 'http://127.0.0.1',
    agentStartPort: 9101,
    modelApiUrl: '',
    modelApiKey: '',
    modelName: '',
    cliCommand: '',
    aiGod: false,
    godCatId: '',
    hideNightRoleForAudience: true,
    showThoughtInMonitor: true
};
let monitorForceApplying = false;

let ttsState = {
    enabled: true,
    rate: 1,
    volume: 1,
    initialized: false,
    supported: typeof window !== 'undefined' && typeof window.speechSynthesis !== 'undefined' && typeof window.SpeechSynthesisUtterance !== 'undefined',
    voices: [],
    voiceMap: {}
};

function ttsSaveSettings() {
    try {
        localStorage.setItem(TTS_SETTINGS_STORAGE_KEY, JSON.stringify({
            enabled: !!ttsState.enabled,
            rate: Number(ttsState.rate || 1),
            volume: Number(ttsState.volume || 1)
        }));
    } catch (_) {}
}

function ttsLoadSettings() {
    try {
        var raw = localStorage.getItem(TTS_SETTINGS_STORAGE_KEY);
        if (!raw) return;
        var parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== 'object') return;
        if (typeof parsed.enabled === 'boolean') ttsState.enabled = parsed.enabled;
        if (Number.isFinite(parsed.rate)) ttsState.rate = Math.max(0.6, Math.min(1.6, Number(parsed.rate)));
        if (Number.isFinite(parsed.volume)) ttsState.volume = Math.max(0, Math.min(1, Number(parsed.volume)));
    } catch (_) {}
}

function ttsUpdateSettingsUI() {
    var cb = document.getElementById('ttsEnabled');
    var label = document.getElementById('ttsEnabledLabel');
    var rate = document.getElementById('ttsRate');
    var rateValue = document.getElementById('ttsRateValue');
    var volume = document.getElementById('ttsVolume');
    var volumeValue = document.getElementById('ttsVolumeValue');
    if (!cb || !label || !rate || !rateValue || !volume || !volumeValue) return;

    cb.checked = !!ttsState.enabled;
    label.textContent = ttsState.enabled ? '已启用' : '未启用';
    label.style.color = ttsState.enabled ? '#16a34a' : '';

    rate.value = String(Number(ttsState.rate || 1));
    rateValue.textContent = Number(ttsState.rate || 1).toFixed(2) + 'x';

    volume.value = String(Number(ttsState.volume == null ? 1 : ttsState.volume));
    volumeValue.textContent = Math.round(Number(ttsState.volume == null ? 1 : ttsState.volume) * 100) + '%';

    var disabled = !ttsState.supported;
    cb.disabled = disabled;
    rate.disabled = disabled;
    volume.disabled = disabled;
    if (disabled) {
        label.textContent = '浏览器不支持';
        label.style.color = '#9ca3af';
    }
}

function ttsHash(text) {
    var raw = String(text || '');
    var h = 0;
    for (var i = 0; i < raw.length; i++) {
        h = (h * 31 + raw.charCodeAt(i)) >>> 0;
    }
    return h;
}

function ttsLoadVoiceMap() {
    try {
        var raw = localStorage.getItem(TTS_VOICE_MAP_STORAGE_KEY);
        if (!raw) return {};
        var parsed = JSON.parse(raw);
        return (parsed && typeof parsed === 'object') ? parsed : {};
    } catch (_) {
        return {};
    }
}

function ttsSaveVoiceMap() {
    try {
        localStorage.setItem(TTS_VOICE_MAP_STORAGE_KEY, JSON.stringify(ttsState.voiceMap || {}));
    } catch (_) {}
}

function ttsRefreshVoices() {
    if (!ttsState.supported) return;
    var all = window.speechSynthesis.getVoices() || [];
    var zh = all.filter(function(v) { return /^zh/i.test(v.lang || ''); });
    ttsState.voices = zh.length ? zh : all;
}

function ttsEnsureSpeakerAssignments() {
    if (!ttsState.supported) return;
    if (!Array.isArray(ttsState.voices) || !ttsState.voices.length) return;
    var map = ttsState.voiceMap || {};
    var keys = ['judge', 'owner'];
    cats.forEach(function(cat) {
        if (cat && cat.id) keys.push(cat.id);
    });
    keys.forEach(function(key) {
        if (map[key]) return;
        var idx = ttsHash(key) % ttsState.voices.length;
        map[key] = ttsState.voices[idx].voiceURI;
    });
    ttsState.voiceMap = map;
    ttsSaveVoiceMap();
}

function ttsInit() {
    if (!ttsState.supported || ttsState.initialized) return;
    ttsState.initialized = true;
    ttsLoadSettings();
    ttsState.voiceMap = ttsLoadVoiceMap();
    ttsRefreshVoices();
    ttsEnsureSpeakerAssignments();
    if (typeof window.speechSynthesis.onvoiceschanged !== 'undefined') {
        window.speechSynthesis.onvoiceschanged = function() {
            ttsRefreshVoices();
            ttsEnsureSpeakerAssignments();
        };
    }
    document.addEventListener('click', function() {
        try { window.speechSynthesis.resume(); } catch (_) {}
    }, { once: true });
}

function ttsNormalizeText(text) {
    var raw = String(text || '');
    raw = raw.replace(/\[[^\]]+\]/g, '');
    raw = raw.replace(/【[^】]{1,30}】/g, '');
    raw = raw.replace(/[\[{(（]\s*(?:第\s*\d+\s*[轮回局天夜]|第\s*\d+\s*轮|夜晚|白天|系统|旁白|公告|播报|阶段|回合|投票|讨论)\s*[\]}）)]/g, '');
    raw = raw.replace(/(?:^|[，。；、\s])(?:第\s*\d+\s*轮|第\s*\d+\s*[天夜]|夜晚|白天|系统|旁白|公告|播报|阶段|回合)\s*[:：]/g, ' ');
    raw = raw.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}]/gu, '');
    raw = raw.replace(/[（(]\s*(?:角色|身份|职业)\s*[:：]\s*[^）)]+[）)]/g, '');
    raw = raw.replace(/[（(]\s*(?:狼人|村民|预言家|女巫|猎人|守卫|白痴|法官|上帝|AI法官)\s*[）)]/g, '');
    raw = raw.replace(/(?:^|[，。；、\s])(?:角色|身份|职业)\s*[:：]\s*(?:狼人|村民|预言家|女巫|猎人|守卫|白痴|法官|上帝|AI法官)(?=$|[，。；、\s])/g, ' ');
    raw = raw.replace(/^\s*(?:狼人|村民|预言家|女巫|猎人|守卫|白痴|法官|上帝|AI法官)\s*[:：]\s*/g, '');
    raw = raw.replace(/^\s*[^，。；、:：]{1,20}[（(]\s*(?:狼人|村民|预言家|女巫|猎人|守卫|白痴|法官|上帝|AI法官)\s*[）)]\s*[:：]?\s*/g, '');
    raw = raw.replace(/\s*[（(]\s*(?:狼人|村民|预言家|女巫|猎人|守卫|白痴|法官|上帝|AI法官)\s*[）)]\s*/g, ' ');
    raw = raw.replace(/^\s*(?:系统|旁白|公告|播报|阶段|回合|第\s*\d+\s*轮|第\s*\d+\s*[天夜])\s*[:：\-—]+\s*/g, '');
    raw = raw.replace(/^\s*(?:\d+\.|\d+、|[-•·])\s*/g, '');
    raw = raw.replace(/[\r\n]+/g, '，');
    raw = raw.replace(/\s+/g, ' ').trim();
    if (raw.length > 1200) raw = raw.slice(0, 1200);
    return raw;
}

function ttsSplitSegments(text) {
    var normalized = String(text || '').trim();
    if (!normalized) return [];
    var parts = normalized.split(/(?<=[。！？!?；;])/);
    var maxLen = 90;
    var segments = [];
    var current = '';
    parts.forEach(function(part) {
        var p = String(part || '').trim();
        if (!p) return;
        if (!current) {
            current = p;
            return;
        }
        if ((current + p).length <= maxLen) {
            current += p;
        } else {
            segments.push(current);
            current = p;
        }
    });
    if (current) segments.push(current);

    var flat = [];
    segments.forEach(function(seg) {
        if (seg.length <= maxLen) {
            flat.push(seg);
            return;
        }
        for (var i = 0; i < seg.length; i += maxLen) {
            flat.push(seg.slice(i, i + maxLen));
        }
    });
    return flat.slice(0, 20);
}

function ttsInferSystemSpeaker(text, cls) {
    var t = String(text || '');
    var c = String(cls || '');
    if (/法官|AI法官|上帝视角/.test(t)) return { key: 'judge', name: '法官' };
    if (/^⚖️|^🤖/.test(t)) return { key: 'judge', name: '法官' };
    if (c.indexOf('pipeline-msg') !== -1 && /投票|出局|天亮|天黑/.test(t)) return { key: 'judge', name: '法官' };
    return null;
}

function ttsSpeak(speakerKey, speakerName, text) {
    if (!ttsState.supported || !ttsState.enabled) return;
    var content = ttsNormalizeText(text);
    if (!content) return;
    if (!ttsState.voices.length) ttsRefreshVoices();
    if (!ttsState.voices.length) return;

    if (!ttsState.voiceMap[speakerKey]) {
        var idx = ttsHash(speakerKey) % ttsState.voices.length;
        ttsState.voiceMap[speakerKey] = ttsState.voices[idx].voiceURI;
        ttsSaveVoiceMap();
    }

    var voice = ttsState.voices.find(function(v) {
        return v.voiceURI === ttsState.voiceMap[speakerKey];
    }) || ttsState.voices[0];
    if (!voice) return;

    var segments = ttsSplitSegments(content);
    if (!segments.length) return;
    segments.forEach(function(seg) {
        var utter = new SpeechSynthesisUtterance(seg);
        utter.voice = voice;
        utter.lang = voice.lang || 'zh-CN';
        utter.volume = Math.max(0, Math.min(1, Number(ttsState.volume == null ? 1 : ttsState.volume)));
        if (speakerKey === 'judge') {
            utter.rate = Math.max(0.6, Math.min(1.6, Number(ttsState.rate || 1) * 0.96));
            utter.pitch = 0.9;
        } else {
            utter.rate = Math.max(0.6, Math.min(1.6, Number(ttsState.rate || 1)));
            utter.pitch = 1.08;
        }
        try {
            window.speechSynthesis.speak(utter);
        } catch (_) {}
    });
}

function monitorPhaseLabel(phase) {
    var map = {
        prepare: '准备阶段',
        night_wolf_discuss: '夜晚·狼人讨论',
        night_wolf: '夜晚·狼人行动',
        night_guard: '夜晚·守卫行动',
        night_witch: '夜晚·女巫行动',
        night_seer: '夜晚·预言家查验',
        day_announce: '白天·法官播报',
        day_discuss: '白天·讨论阶段',
        day_vote: '白天·投票阶段',
        game_over: '游戏结束'
    };
    return map[phase] || phase || '未知阶段';
}

function monitorPhaseOrder(phase) {
    var map = {
        prepare: 0,
        night_wolf_discuss: 1,
        night_wolf: 2,
        night_guard: 3,
        night_witch: 4,
        night_seer: 5,
        day_announce: 6,
        day_discuss: 7,
        day_vote: 8,
        game_over: 9
    };
    return map[phase] != null ? map[phase] : 99;
}

function monitorStateOrderValue(state) {
    var roundNo = parseInt((state && state.round_no), 10);
    if (isNaN(roundNo) || roundNo < 0) roundNo = 0;
    return roundNo * 100 + monitorPhaseOrder((state && state.phase) || '');
}

function monitorSortSpeechHistory(rows) {
    return (rows || []).slice().sort(function(a, b) {
        var ta = Date.parse((a && a.timestamp) || '') || 0;
        var tb = Date.parse((b && b.timestamp) || '') || 0;
        if (ta !== tb) return ta - tb;
        var pa = monitorPhaseOrder((a && a.phase) || '');
        var pb = monitorPhaseOrder((b && b.phase) || '');
        if (pa !== pb) return pa - pb;
        var aa = (a && a.player_id) || '';
        var bb = (b && b.player_id) || '';
        return aa.localeCompare(bb);
    });
}

function monitorDeathCauseLabel(cause) {
    var map = {
        wolf: '被狼人袭击',
        poison: '被女巫毒杀',
        vote: '被投票放逐',
        hunter: '被猎人带走'
    };
    return map[cause] || cause || '未知原因';
}

function werewolfEliminatedCauseLabel(cause) {
    var map = {
        wolf: '被狼人刀',
        poison: '被女巫毒杀',
        vote: '被投死',
        hunter: '被猎人带走'
    };
    return map[cause] || '淘汰';
}

function monitorPlayerName(state, playerId) {
    var players = (state && state.players) || [];
    var p = players.find(function(item) { return item.player_id === playerId; });
    return (p && p.nickname) || playerId;
}

function monitorNarrateOnce(key, text, cls) {
    if (!key || !text) return;
    if (monitorState.narrationSeenKeys[key]) return;
    monitorState.narrationSeenKeys[key] = true;
    addSystemMessage(text, cls || 'vote-msg');
}

function monitorNarrateFromPhaseChanged(payload) {
    if (!payload || !payload.god_view || monitorState.viewMode !== 'god') return;
    var roomId = monitorState.roomId || '-';
    var consensus = payload.god_view.consensus_target || '';
    if (!consensus) return;
    var key = ['godview', roomId, payload.phase || '-', consensus].join('|');
    var prefix = payload.phase === 'night_wolf' ? '⚖️ 法官（上帝视角）：狼人讨论后目标一致为 ' : '⚖️ 法官（上帝视角）：狼人夜间目标倾向 ';
    monitorNarrateOnce(key, prefix + consensus + '。', 'pipeline-msg');
}

function monitorNarrateFromRoomState(state) {
    if (!state) return;
    if (monitorState.aiGod) return;
    var roomId = state.room_id || monitorState.roomId || '-';
    var roundNo = state.round_no || 0;
    var phase = state.phase || 'unknown';
    var phaseKey = ['phase', roomId, roundNo, phase].join('|');

        switch (phase) {
            case 'night_wolf_discuss':
                monitorNarrateOnce(phaseKey, '⚖️ 法官：天黑请闭眼，狼人请睁眼。先进入夜间讨论阶段，交换判断并达成一致目标。', 'pipeline-msg');
                break;
            case 'night_wolf':
                monitorNarrateOnce(phaseKey, '⚖️ 法官：天黑请闭眼，狼人请睁眼并执行最终猎杀目标。', 'pipeline-msg');
                break;
            case 'night_guard':
                monitorNarrateOnce(phaseKey, '⚖️ 法官：守卫请行动，选择今晚守护对象。', 'pipeline-msg');
                break;
            case 'night_witch':
                monitorNarrateOnce(phaseKey, '⚖️ 法官：女巫请行动，决定是否使用解药或毒药。', 'pipeline-msg');
                break;
            case 'night_seer':
                monitorNarrateOnce(phaseKey, '⚖️ 法官：预言家请查验一名玩家身份。', 'pipeline-msg');
                break;
            case 'day_announce':
                monitorNarrateOnce(phaseKey, '⚖️ 法官：天亮了，现在公布昨夜结果。', 'pipeline-msg');
                break;
            case 'day_discuss':
                monitorNarrateOnce(phaseKey, '⚖️ 法官：进入白天讨论环节，请各位依次发言。', 'pipeline-msg');
                var aliveDiscuss = ((state.players || []).filter(function(p) { return !!p.alive; })).map(function(p) {
                    return p.nickname || p.player_id;
                });
                var discussOrderKey = ['discuss_order', roomId, roundNo].join('|');
                if (aliveDiscuss.length > 0) {
                    monitorNarrateOnce(
                        discussOrderKey,
                        '⚖️ 法官点名发言顺序：' + aliveDiscuss.join(' → '),
                        'pipeline-msg'
                    );
                }
                break;
            case 'day_vote':
                monitorNarrateOnce(phaseKey, '⚖️ 法官：进入投票环节，请选择你要放逐的对象。', 'pipeline-msg');
                var aliveVote = ((state.players || []).filter(function(p) { return !!p.alive && !!p.can_vote; })).map(function(p) {
                    return p.nickname || p.player_id;
                });
                var voteOptionKey = ['vote_options', roomId, roundNo].join('|');
                if (aliveVote.length > 0) {
                    monitorNarrateOnce(
                        voteOptionKey,
                        '⚖️ 法官：当前可投票玩家：' + aliveVote.join('、'),
                        'vote-msg'
                    );
                }
                break;
    }

    if (phase === 'day_announce') {
        var deaths = state.deaths_this_round || {};
        var deathIds = Object.keys(deaths);
        var deathKey = ['death', roomId, roundNo, deathIds.sort().join(',')].join('|');
        if (deathIds.length === 0) {
            monitorNarrateOnce(deathKey, '⚖️ 法官：昨夜是平安夜，无人出局。', 'vote-msg');
        } else {
            deathIds.forEach(function(playerId) {
                var cause = deaths[playerId];
                var text = '⚖️ 法官：' + monitorPlayerName(state, playerId) + ' 出局（' + monitorDeathCauseLabel(cause) + '）。';
                var key = ['death', roomId, roundNo, playerId, cause].join('|');
                monitorNarrateOnce(key, text, 'vote-msg');
            });
        }
    }

    if (state.game_over) {
        var winner = state.winner || 'unknown';
        var gameOverKey = ['game_over', roomId, winner].join('|');
        var winnerText = winner === 'wolf' ? '狼人阵营' : (winner === 'good' ? '好人阵营' : winner);
        monitorNarrateOnce(gameOverKey, '🏁 法官：游戏结束，' + winnerText + ' 获胜。', 'pipeline-msg');
    }
}

function werewolfMapBackendPhase(phase) {
    if (!phase) return 'night';
    if (phase.indexOf('night_') === 0) return 'night';
    if (phase === 'day_vote') return 'vote';
    if (phase === 'day_announce' || phase === 'day_discuss') return 'day';
    if (phase === 'game_over') return 'day';
    return 'night';
}

function werewolfRoleMeta(roleId) {
    var found = WEREWOLF_ROLES.find(function(item) { return item.id === roleId; });
    if (found) return found;
    return { id: roleId || 'unknown', name: roleId || '未知', icon: '🎭', team: 'good' };
}

function werewolfSyncButtonsByState() {
    var startBtn = document.getElementById('wpStartBtn');
    var nextBtn = document.getElementById('wpNextBtn');
    var revealBtn = document.getElementById('wpRevealBtn');
    var endBtn = document.getElementById('wpEndBtn');
    if (!startBtn || !nextBtn || !revealBtn || !endBtn) return;
    startBtn.disabled = wfState.active;
    nextBtn.disabled = !wfState.active;
    endBtn.disabled = !wfState.active;
    revealBtn.disabled = true;
}

function werewolfAutoDelayMs() {
    return WEREWOLF_BACKEND_AUTO_ADVANCE_DELAY_MS;
}

function werewolfStopAutoAdvance() {
    if (wfAutoAdvanceTimer) {
        clearTimeout(wfAutoAdvanceTimer);
        wfAutoAdvanceTimer = null;
    }
}

function werewolfScheduleAutoAdvance(delayMs) {
    werewolfStopAutoAdvance();
    if (!wfState.active) return;
    var nextDelay = typeof delayMs === 'number' ? delayMs : werewolfAutoDelayMs();
    wfAutoAdvanceTimer = setTimeout(function() {
        if (!wfState.active) return;
        werewolfNextPhase(true);
    }, nextDelay);
}

function werewolfStartAutoAdvance() {
    if (!wfState.active) return;
    werewolfScheduleAutoAdvance(werewolfAutoDelayMs());
}

function werewolfRefreshLinkButton() {
    return;
}

function werewolfShouldHideNightRoleBadge(isNight) {
    return gameMode === 'werewolf' && !!isNight && !judgeView && !!wfState.hideNightRoleForAudience;
}

function werewolfSyncFromBackendState(state) {
    if (wfState.linkedRoomId && state.room_id && state.room_id !== wfState.linkedRoomId) return;

    var players = state.players || [];
    wfState.active = !!state.started && !state.game_over;
    wfState.phase = werewolfMapBackendPhase(state.phase);
    wfState.round = state.round_no || wfState.round || 1;
    var eliminated = [];
    var eliminatedCauseByCatId = {};
    var linkedRoles = {};
    players.forEach(function(p, idx) {
        var bound = monitorState.playerBindings[p.player_id] || {};
        if (!bound.catId && p && p.nickname) {
            var foundByName = cats.find(function(cat) { return (cat.name || '').trim() === (p.nickname || '').trim(); });
            if (foundByName) {
                bound = {
                    catId: foundByName.id,
                    nickname: foundByName.name,
                    breed: foundByName.breed,
                    color: foundByName.color,
                    emoji: foundByName.emoji,
                    avatarUrl: foundByName.avatarUrl || ''
                };
                monitorState.playerBindings[p.player_id] = bound;
            }
        }
        if (!bound.catId) {
            var catByIndex = cats[idx];
            if (catByIndex) {
                bound = {
                    catId: catByIndex.id,
                    nickname: catByIndex.name,
                    breed: catByIndex.breed,
                    color: catByIndex.color,
                    emoji: catByIndex.emoji,
                    avatarUrl: catByIndex.avatarUrl || ''
                };
                monitorState.playerBindings[p.player_id] = bound;
            }
        }
        var catId = bound.catId;
        if (catId) {
            if (!p.alive) {
                eliminated.push(catId);
                if (p.death_cause) eliminatedCauseByCatId[catId] = p.death_cause;
            }
            if (p.role) linkedRoles[catId] = werewolfRoleMeta(p.role);
        }
    });
    wfState.eliminated = eliminated;
    wfState.eliminatedCauseByCatId = eliminatedCauseByCatId;
    wfState.roles = linkedRoles;

    werewolfSyncButtonsByState();
    updateWerewolfStatus();
    renderMembers();

    if (state.game_over) {
        werewolfStopAutoAdvance();
        addSystemMessage('🏁 联动房间已结束，胜利方：' + (state.winner || '未知'), 'vote-msg');
    }
}

function werewolfPseudoCat(playerId) {
    var idx = Math.abs((playerId || '').split('').reduce(function(acc, ch) {
        return acc + ch.charCodeAt(0);
    }, 0)) % catColors.length;
    var avatar = CAT_BREED_AVATARS[idx % CAT_BREED_AVATARS.length];
    var mapped = monitorState.playerMap[playerId] || {};
    var bound = monitorState.playerBindings[playerId] || {};
    var roleMeta = null;
    if (mapped.role) {
        roleMeta = werewolfRoleMeta(mapped.role);
    } else if (bound.catId && wfState.roles && wfState.roles[bound.catId]) {
        roleMeta = wfState.roles[bound.catId];
    }
    return {
        id: 'linked_' + playerId,
        name: bound.nickname || mapped.nickname || playerId,
        emoji: bound.emoji || avatar.icon,
        color: bound.color || catColors[idx],
        breed: bound.breed || mapped.breed || avatar.breed,
        avatarUrl: bound.avatarUrl || '',
        role: roleMeta
    };
}

function monitorSanitizeDayDiscussDisplayText(text) {
    var speech = String(text || '').trim();
    if (!speech) return speech;
    var replaced = speech;
    [
        ['暴露狼人身份', '暴露真实身份'],
        ['狼人身份', '真实身份'],
        ['（狼人）', '（疑似狼人）'],
        ['就是狼人', '疑似狼人'],
        ['必是狼人', '疑似狼人'],
        ['是狼人', '疑似狼人'],
        ['为狼人', '疑似狼人']
    ].forEach(function(pair) {
        replaced = replaced.split(pair[0]).join(pair[1]);
    });
    return replaced;
}

function werewolfRenderLinkedSpeech(entry) {
    if (!entry) return;
    // Handle god_narration entries from AI God Orchestrator
    if (entry.event === 'god_narration') {
        var godContent = (entry.content || '').trim();
        if (!godContent) return;
        var prefix = entry.is_fallback ? '⚖️ 法官（托管）：' : '🤖 AI法官：';
        addSystemMessage(prefix + godContent, 'pipeline-msg');
        return;
    }
    if (entry.player_id === 'god') {
        var settleContent = (entry.content || '').trim();
        if (!settleContent) return;
        addSystemMessage('⚖️ 法官结算：' + settleContent, 'judge-settle-msg');
        return;
    }
    if (!entry.player_id) return;
    var inWerewolfLinked = (gameMode === 'werewolf' && wfState.backendLinked);
    var inMonitorMode = (gameMode === 'monitor');
    if (!inWerewolfLinked && !inMonitorMode) return;
    var cat = werewolfPseudoCat(entry.player_id);
    var isNight = (entry.phase || '').indexOf('night_') === 0;
    var phaseMap = {
        night_wolf_discuss: '🌙 狼人讨论',
        night_wolf: '🌙 狼人行动',
        night_guard: '🌙 守卫行动',
        night_witch: '🌙 女巫行动',
        night_seer: '🌙 预言家查验',
        day_discuss: '☀️ 白天讨论',
        day_vote: '🗳️ 白天投票',
        hunter_shot: '🏹 猎人开枪'
    };
    var phaseLabel = phaseMap[entry.phase] || monitorPhaseLabel(entry.phase);
    var content = (entry.content || '').trim();
    if (!content) content = '（无文本返回）';
    if (entry.phase === 'day_discuss') {
        content = monitorSanitizeDayDiscussDisplayText(content);
    }
    if (entry.phase === 'night_wolf_discuss') {
        content = '【讨论】' + content;
    }
    if (entry.is_fallback) {
        if (/^fallback\//i.test(content)) {
            content = '系统降级托管：' + content.replace(/^fallback\//i, '');
        }
        if (entry.fallback_reason) {
            content += '（fallback: ' + entry.fallback_reason + '）';
        } else {
            content += '（fallback）';
        }
    }
    addCatMessage(cat, '【' + phaseLabel + '】' + content, isNight);
    var thought = (entry.thought_content || '').trim();
    var canShowThought = (gameMode === 'monitor' && !!monitorState.showThoughtInMonitor) || (gameMode === 'werewolf' && judgeView);
    if (thought && canShowThought) {
        addSystemMessage('🧠 ' + cat.name + '（仅法官可见思考）：' + thought, 'pipeline-msg thought-msg', { speaker: { key: '' } });
        monitorApplyThoughtVisibility();
    }
}

function monitorApplyThoughtVisibility() {
    var show = !(gameMode === 'monitor' && !monitorState.showThoughtInMonitor);
    document.querySelectorAll('.thought-msg').forEach(function(el) {
        el.style.display = show ? '' : 'none';
    });
}

function monitorToggleThoughtVisibility() {
    var el = document.getElementById('monitorShowThought');
    monitorState.showThoughtInMonitor = !(el && el.checked === false);
    monitorPersistConfig();
    monitorApplyThoughtVisibility();
    monitorRenderSpeech();
}

function wpToggleAiGod() {
    if (wfState.active) {
        var wpCb = document.getElementById('wpAiGodToggle');
        if (wpCb) wpCb.checked = !!monitorState.aiGod;
        showToast('⚠️ 游戏已开始，不能再切换 AI 法官模式');
        return;
    }
    var checked = document.getElementById('wpAiGodToggle').checked;
    var sec = document.getElementById('wpAiGodConfig');
    if (sec) sec.style.display = checked ? 'block' : 'none';
    // Sync to monitor panel checkbox
    var mnCb = document.getElementById('monitorAiGod');
    if (mnCb) mnCb.checked = checked;
    var mnSec = document.getElementById('monitorGodConfig');
    if (mnSec) mnSec.style.display = checked ? 'block' : 'none';
    monitorState.aiGod = checked;
    monitorSyncPlayerCountFromCats();
    monitorPersistConfig();
    renderMembers();
}

function wpToggleNightRoleMask() {
    var el = document.getElementById('wpHideNightRole');
    wfState.hideNightRoleForAudience = !(el && el.checked === false);
    monitorState.hideNightRoleForAudience = !!wfState.hideNightRoleForAudience;
    monitorPersistConfig();
    refreshWerewolfVisibility();
}

function monitorRenderGodCatSelectors() {
    var monitorSel = document.getElementById('monitorGodCatId');
    var wpSel = document.getElementById('wpGodCatId');
    if (!monitorSel && !wpSel) return;

    var current = String(monitorState.godCatId || '');
    var hasCurrent = cats.some(function(cat) { return cat && cat.id === current; });
    if (!hasCurrent) {
        current = cats.length ? cats[0].id : '';
        monitorState.godCatId = current;
    }

    var options = cats.map(function(cat) {
        return '<option value="' + escapeHtml(cat.id) + '">' + escapeHtml(cat.name) + '</option>';
    }).join('');
    if (!options) {
        options = '<option value="">暂无猫猫</option>';
    }

    [monitorSel, wpSel].forEach(function(sel) {
        if (!sel) return;
        sel.innerHTML = options;
        sel.value = current;
        sel.disabled = cats.length === 0;
    });
}

function monitorPlayableCats() {
    if (!monitorState.aiGod || !monitorState.godCatId) return cats.slice();
    return cats.filter(function(cat) {
        return cat && cat.id !== monitorState.godCatId;
    });
}

function monitorLockGodConfigIfStarted() {
    var started = !!wfState.active;
    ['monitorAiGod', 'wpAiGodToggle', 'monitorGodCatId', 'wpGodCatId'].forEach(function(id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.disabled = started;
    });
}

function monitorOnGodCatChange(source) {
    if (wfState.active) {
        showToast('⚠️ 游戏已开始，不能再修改 AI 法官');
        monitorRenderGodCatSelectors();
        return;
    }
    var from = source === 'wp' ? document.getElementById('wpGodCatId') : document.getElementById('monitorGodCatId');
    var val = (from && from.value) ? from.value : '';
    monitorState.godCatId = val;

    var monitorSel = document.getElementById('monitorGodCatId');
    var wpSel = document.getElementById('wpGodCatId');
    if (monitorSel) monitorSel.value = val;
    if (wpSel) wpSel.value = val;

    monitorPersistConfig();
    renderMembers();
}

function monitorJudgeModeLabel(data) {
    var isAi = !!(data && data.ai_god);
    if (!isAi) return '系统法官';
    var judgeName = (data && data.god_cat_name) || '';
    if (!judgeName) {
        var judgeId = (data && data.god_cat_id) || monitorState.godCatId;
        var found = cats.find(function(cat) { return cat && cat.id === judgeId; });
        judgeName = found ? found.name : '';
    }
    return judgeName ? ('AI法官（' + judgeName + '）') : 'AI法官';
}

function werewolfToggleBackendLink() {
    wfState.backendLinked = true;
    werewolfSyncButtonsByState();
}

// Pipeline role definitions with preset system prompts
var PIPELINE_ROLES = {
    developer: {
        id:'developer', name:'架构师 & 开发工程师', icon:'🛠️', tag:'pp-role-dev',
        systemPrompt: function(req) {
            return '你是一位经验丰富的全栈开发工程师和架构师。你的职责是根据需求进行功能模块设计并完成代码开发。\n\n【工作规范】\n1. 先进行模块设计：分析需求，拆解功能模块，给出架构设计方案\n2. 再进行代码实现：输出完整的、可运行的代码\n3. 代码必须包含必要的注释和文档字符串\n4. 考虑边界场景和错误处理\n5. 遵循最佳实践和设计模式\n\n【输出格式】\n请按以下结构输出：\n## 📐 模块设计\n- 架构概述\n- 模块拆解\n- 接口设计\n\n## 💻 代码实现\n(完整的代码)\n\n## 📝 设计说明\n- 关键设计决策\n- 技术选型理由\n\n保持猫咪口吻，可以加入“喵”等语气词，但技术内容必须专业严谨。';
        },
        taskPrompt: function(req) {
            return '【铲屎官需求】\n' + req + '\n\n请开始进行功能模块设计和代码开发。注意架构设计要清晰，代码要完整可运行。';
        }
    },
    reviewer: {
        id:'reviewer', name:'代码检视专家', icon:'🔍', tag:'pp-role-review',
        systemPrompt: function(req) {
            return '你是一位严谨的代码检视专家（Code Reviewer）。你的职责是对开发工程师提交的代码进行全面检视。\n\n【检视规范】\n1. 代码质量：可读性、命名规范、代码风格\n2. 架构设计：模块划分、职责分离、设计模式\n3. 潜在问题：BUG、安全漏洞、性能问题、资源泄漏\n4. 错误处理：异常处理是否完善、边界场景考虑\n5. 最佳实践：是否符合行业规范\n6. 建议改进：提出具体的优化建议和改进方案\n\n【输出格式】\n请按以下结构输出：\n## 🔍 代码检视报告\n\n### ✅ 优点\n(列举代码中做得好的部分)\n\n### ⚠️ 问题与建议\n(按严重程度排序，每个问题给出具体位置和修改建议)\n\n### 🚨 严重问题 (必须修复)\n### 🟡 一般问题 (建议修改)\n### 🟢 小问题 (可以优化)\n\n### 📊 总体评价\n(给出总体评分和结论：通过 / 有条件通过 / 不通过)\n\n保持猫咪口吻但内容必须专业严谹，每个问题要给出具体地方和代码建议。';
        },
        taskPrompt: function(req, devOutput) {
            return '【原始需求】\n' + req + '\n\n【开发工程师提交的代码】\n' + devOutput + '\n\n请对以上代码进行全面的代码检视，给出专业详细的检视报告。';
        }
    },
    tester: {
        id:'tester', name:'测试工程师', icon:'🧪', tag:'pp-role-test',
        systemPrompt: function(req) {
            return '你是一位专业的软件测试工程师（QA Engineer）。你的职责是对开发工程师提交的代码进行全面测试并出具测试报告。\n\n【测试规范】\n1. 单元测试：编写关键函数的单元测试用例\n2. 功能测试：验证核心功能是否符合需求\n3. 边界测试：测试边界条件和异常情况\n4. 安全测试：检查常见安全漏洞\n5. 性能测试：评估基本性能指标\n\n【输出格式】\n请按以下结构输出测试报告：\n## 🧪 测试报告\n\n### 测试环境\n(描述测试预设环境)\n\n### 测试用例\n| 编号 | 测试项 | 输入 | 预期输出 | 结果 |\n|------|----------|------|----------|------|\n(列出具体测试用例)\n\n### 单元测试代码\n(提供可执行的测试代码)\n\n### 缺陷列表\n| 编号 | 严重程度 | 描述 | 复现步骤 |\n|------|----------|------|----------|\n(列出发现的缺陷)\n\n### 📊 测试总结\n- 通过率：XX%\n- 测试结论：通过 / 有条件通过 / 不通过\n- 风险评估\n\n保持猫咪口吻但内容必须专业严谹，测试用例要具体可执行。';
        },
        taskPrompt: function(req, devOutput, reviewOutput) {
            return '【原始需求】\n' + req + '\n\n【开发工程师提交的代码】\n' + devOutput + '\n\n【代码检视意见】\n' + reviewOutput + '\n\n请对以上代码进行全面测试，编写测试用例和测试代码，并出具详细的测试报告。';
        }
    }
};

// ====================== Init ======================
function init() {
    ttsInit();
    ttsUpdateSettingsUI();
    renderEmojiPicker();
    renderColorPicker();
    updateProviderUI('openai');
    renderMembers();
    addSystemMessage('欢迎来到喵星人聊天室！添加你的猫猫，开始聊天吧～ 🐾');
    pipelineUpdateRoleAssign();
    monitorInit();
    monitorSyncPlayerCountFromCats();
    loadCatsFromBackendEnvProfile();
}

function normalizeImportedCats(rawCats, startIndex) {
    var idxSeed = startIndex || 0;
    var list = [];
    (rawCats || []).forEach(function(c, i) {
        if (!c || !c.name || !c.provider) return;
        var cfg = PROVIDERS[c.provider] || PROVIDERS.openai;
        list.push({
            id: c.id || (Date.now().toString() + '_' + (idxSeed + i)),
            name: c.name,
            emoji: c.emoji || '🐱',
            avatarUrl: c.avatarUrl || '',
            breed: c.breed || '家猫',
            color: c.color || '#f582ae',
            personality: c.personality || '',
            provider: c.provider,
            apiUrl: c.apiUrl || cfg.defaultUrl,
            apiKey: c.apiKey || '',
            model: c.model || cfg.defaultModel,
            claudeVersion: c.claudeVersion || '2023-06-01',
            badgeClass: c.badgeClass || cfg.badgeClass
        });
    });
    return list;
}

function monitorProfilePayload() {
    return {
        cats: cats.map(function(c) {
            return {
                id: c.id,
                name: c.name,
                emoji: c.emoji,
                avatarUrl: c.avatarUrl,
                breed: c.breed,
                color: c.color,
                personality: c.personality,
                provider: c.provider,
                apiUrl: c.apiUrl,
                apiKey: c.apiKey,
                model: c.model,
                claudeVersion: c.claudeVersion,
                badgeClass: c.badgeClass
            };
        }),
        monitor_config: {
            apiBase: monitorState.apiBase,
            playerCount: monitorState.playerCount,
            agentHost: monitorState.agentHost,
            agentStartPort: monitorState.agentStartPort,
            modelApiUrl: monitorState.modelApiUrl,
            modelApiKey: monitorState.modelApiKey,
            modelName: monitorState.modelName,
            cliCommand: monitorState.cliCommand,
            aiGod: monitorState.aiGod || false,
            godCatId: monitorState.godCatId || '',
            hideNightRoleForAudience: !!wfState.hideNightRoleForAudience,
            showThoughtInMonitor: !!monitorState.showThoughtInMonitor
        }
    };
}

function persistCatsToBackendEnv(reason, options) {
    var opts = options || {};
    var strict = !!opts.strict;
    return monitorHttp('/api/frontend/profile', {
        timeoutMs: 20000,
        method: 'POST',
        body: JSON.stringify(monitorProfilePayload())
    }).then(function(resp) {
        if (reason) {
            monitorAddPhaseLog('配置已写入后端环境变量：' + reason);
        }
        var statusEl = document.getElementById('envSaveStatus');
        if (statusEl) {
            var ts = resp && resp.saved_at ? resp.saved_at : null;
            var d = ts ? new Date(ts) : new Date();
            statusEl.innerText = '已自动保存 ' + d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0') + ':' + d.getSeconds().toString().padStart(2, '0');
            statusEl.style.color = 'rgba(255,255,255,0.5)';
        }
        return resp;
    }).catch(function(err) {
        console.warn('persist frontend profile failed', err);
        if (reason) {
            monitorAddPhaseLog('写入后端环境变量失败：' + err.message);
        }
        var statusEl = document.getElementById('envSaveStatus');
        if (statusEl) {
            statusEl.innerText = '保存失败';
            statusEl.style.color = '#ff6b6b';
        }
        if (strict) {
            throw err;
        }
    });
}

function monitorSaveEnvProfile() {
    monitorCollectInvokeConfig();
    monitorPersistConfig();
    persistCatsToBackendEnv('手动保存', { strict: true }).then(function() {
        showToast('✅ 已保存到后端环境变量');
    }).catch(function(err) {
        showToast('❌ 保存失败：' + err.message);
    });
}

function monitorForceApplyEnvProfile() {
    if (monitorForceApplying) {
        showToast('⏳ 正在强制同步，请稍候...');
        return;
    }
    monitorForceApplying = true;
    var btn = document.getElementById('monitorForceApplyBtn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ 同步中...';
    }

    monitorCollectInvokeConfig();
    monitorPersistConfig();
    monitorAddPhaseLog('开始强制同步配置：写入环境变量并立即重建后端...');

    monitorHttp('/api/frontend/profile/apply', {
        timeoutMs: 86400000,
        method: 'POST',
        body: JSON.stringify(monitorProfilePayload())
    })
        .then(function(resp) {
            var saved = (resp && resp.saved) || {};
            var applied = (resp && resp.applied) || {};

            var statusEl = document.getElementById('envSaveStatus');
            if (statusEl) {
                var ts = saved && saved.saved_at ? saved.saved_at : null;
                var d = ts ? new Date(ts) : new Date();
                statusEl.innerText = '已自动保存 ' + d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0') + ':' + d.getSeconds().toString().padStart(2, '0');
                statusEl.style.color = 'rgba(255,255,255,0.5)';
            }

            monitorState.roomId = applied.room_id || monitorState.roomId;
            monitorState.ownerId = applied.owner_id || monitorState.ownerId;
            monitorState.players = applied.players || monitorState.players;
            monitorState.aiGod = !!applied.ai_god;
            if (applied.god_cat_id) monitorState.godCatId = applied.god_cat_id;
            wfState.linkedRoomId = monitorState.roomId;
            monitorState.playerBindings = monitorBuildBindingMap(monitorState.players || []);
            monitorApplyBootstrapRegistrationResult(applied);
            var roomIdInput = document.getElementById('monitorRoomId');
            if (roomIdInput && monitorState.roomId) roomIdInput.value = monitorState.roomId;
            monitorSyncViewOptions();
            renderMembers();
            updateOnlineCount();

            var boot = (applied && applied.bootstrap) || {};
            var reg = (boot && boot.registered_agents) || {};
            var agents = reg.agents || {};
            var count = Object.keys(agents).length;
            var judgeMode = monitorJudgeModeLabel(applied);
            monitorAddPhaseLog('强制同步完成：后端已按最新环境变量重建并应用（' + count + '只，' + judgeMode + '）');
            monitorRenderGlobal('同步完成 · room=' + (monitorState.roomId || '-') + ' · ' + judgeMode);

            var roomId = monitorRoomId();
            if (roomId) {
                monitorHttp('/api/rooms/' + encodeURIComponent(roomId), { timeoutMs: 12000 }).then(function(state) {
                    monitorApplyRoomState(state);
                }).catch(function() {});
            }
            if (monitorState.isConnected) {
                monitorConnectWs();
            }
            showToast('✅ 已强制同步并实时应用到后端');
        })
        .catch(function(err) {
            monitorSetAllCatsOnline(false);
            renderMembers();
            updateOnlineCount();
            monitorAddPhaseLog('强制同步失败：' + err.message);
            showToast('❌ 强制同步失败：' + err.message);
        })
        .finally(function() {
            monitorForceApplying = false;
            if (btn) {
                btn.disabled = false;
                btn.textContent = '🚀 强制同步并应用';
            }
        });
}

function applyMonitorConfigFromProfile(cfg) {
    if (!cfg || typeof cfg !== 'object') return;
    monitorState.apiBase = cfg.apiBase || monitorState.apiBase;
    monitorState.playerCount = parseInt(cfg.playerCount, 10) || monitorState.playerCount;
    monitorState.agentHost = cfg.agentHost || monitorState.agentHost;
    monitorState.agentStartPort = parseInt(cfg.agentStartPort, 10) || monitorState.agentStartPort;
    monitorState.modelApiUrl = cfg.modelApiUrl || '';
    monitorState.modelApiKey = cfg.modelApiKey || '';
    monitorState.modelName = cfg.modelName || '';
    monitorState.cliCommand = cfg.cliCommand || '';
    monitorState.aiGod = !!cfg.aiGod;
    monitorState.godCatId = cfg.godCatId || monitorState.godCatId || '';
    if (typeof cfg.showThoughtInMonitor === 'boolean') {
        monitorState.showThoughtInMonitor = cfg.showThoughtInMonitor;
    }

    var map = {
        monitorApiBase: monitorState.apiBase,
        monitorPlayerCount: String(monitorState.playerCount),
        monitorAgentHost: monitorState.agentHost,
        monitorAgentStartPort: String(monitorState.agentStartPort),
        monitorModelApiUrl: monitorState.modelApiUrl,
        monitorModelApiKey: monitorState.modelApiKey,
        monitorModelName: monitorState.modelName,
        monitorCliCommand: monitorState.cliCommand
    };
    Object.keys(map).forEach(function(id) {
        var el = document.getElementById(id);
        if (el) el.value = map[id];
    });
    var aiGodEl = document.getElementById('monitorAiGod');
    if (aiGodEl) aiGodEl.checked = !!monitorState.aiGod;
    var wpAiGod = document.getElementById('wpAiGodToggle');
    if (wpAiGod) wpAiGod.checked = !!monitorState.aiGod;
    var thoughtEl = document.getElementById('monitorShowThought');
    if (thoughtEl) thoughtEl.checked = !!monitorState.showThoughtInMonitor;
    var sec = document.getElementById('monitorGodConfig');
    if (sec) sec.style.display = monitorState.aiGod ? 'block' : 'none';
    var wpSec = document.getElementById('wpAiGodConfig');
    if (wpSec) wpSec.style.display = monitorState.aiGod ? 'block' : 'none';
    monitorRenderGodCatSelectors();
    monitorApplyThoughtVisibility();
}

function loadCatsFromBackendEnvProfile() {
    monitorHttp('/api/frontend/profile', { timeoutMs: 12000 }).then(function(profile) {
        if (!profile || !Array.isArray(profile.cats) || profile.cats.length === 0) {
            return;
        }
        cats = normalizeImportedCats(profile.cats, 0);
        applyMonitorConfigFromProfile(profile.monitor_config || {});
        renderMembers();
        updateOnlineCount();
        monitorSyncPlayerCountFromCats();
        if (gameMode === 'pipeline') pipelineUpdateRoleAssign();
        if (gameMode === 'debate') debateUpdateOrder();
        addSystemMessage('🧩 已从后端环境变量加载 ' + cats.length + ' 只猫猫配置');
        showToast('✅ 已自动加载后端配置');
        var statusEl = document.getElementById('envSaveStatus');
        if (statusEl) {
            var ts = profile && profile.saved_at ? profile.saved_at : null;
            var d = ts ? new Date(ts) : new Date();
            statusEl.innerText = '后端已保存于 ' + d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0') + ':' + d.getSeconds().toString().padStart(2, '0');
            statusEl.style.color = 'rgba(255,255,255,0.5)';
        }
    }).catch(function(err) {
        console.warn('load frontend profile failed', err);
    });
}

function monitorReloadEnvProfile() {
    loadCatsFromBackendEnvProfile();
    monitorAddPhaseLog('已请求从后端环境变量重载猫猫配置');
}

function monitorSyncPlayerCountFromCats() {
    var select = document.getElementById('monitorPlayerCount');
    if (!select) return;
    var n = monitorPlayableCats().length;
    if (n < 8) n = 8;
    if (n > 12) n = 12;
    monitorState.playerCount = n;
    select.value = String(n);
}

// ====================== Pickers ======================
function renderEmojiPicker() {
    document.getElementById('emojiPicker').innerHTML = CAT_BREED_AVATARS.map(function(item, i) {
        var selected = (item.breed === selectedBreed) ? 'selected' : '';
        return '<div class="emoji-option ' + selected + '" onclick="selectEmoji(' + i + ',this)"><div style="font-size:36px;line-height:1;">' + escapeHtml(item.icon) + '</div><div class="emoji-label">' + escapeHtml(item.breed) + '</div></div>';
    }).join('');
}
function selectEmoji(index, el) {
    var item = CAT_BREED_AVATARS[index] || CAT_BREED_AVATARS[0];
    document.querySelectorAll('.emoji-option').forEach(function(e) { e.classList.remove('selected'); });
    el.classList.add('selected');
    selectedEmoji = item.icon;
    selectedAvatarUrl = '';
    selectedBreed = item.breed;

    var nameInput = document.getElementById('catName');
    if (!nameInput) return;
    var current = (nameInput.value || '').trim();
    var autoFilled = nameInput.dataset.autoFilledName === '1';
    if (!current || autoFilled) {
        nameInput.value = item.breed;
        nameInput.dataset.autoFilledName = '1';
    }

    var customAvatarInput = document.getElementById('catAvatarUrl');
    if (!customAvatarInput || !(customAvatarInput.value || '').trim()) {
        updateAddAvatarPreview('');
    }
}

function updateAddAvatarPreview(url) {
    var preview = document.getElementById('catAvatarPreview');
    if (!preview) return;
    var finalUrl = (url || '').trim() || selectedAvatarUrl;
    if (finalUrl) {
        preview.innerHTML = '<img class="cat-avatar-img cat-face" src="' + escapeHtml(finalUrl) + '" alt="头像预览"/>';
    } else {
        preview.innerHTML = '<div style="font-size:38px;line-height:1;">' + escapeHtml(selectedEmoji || '🐱') + '</div>';
    }
}

function onCustomAvatarUrlInput() {
    var input = document.getElementById('catAvatarUrl');
    if (!input) return;
    updateAddAvatarPreview(input.value || '');
}

function uploadCatAvatarClick() {
    var fileInput = document.getElementById('catAvatarFile');
    if (!fileInput) return;
    fileInput.click();
}

function onCatAvatarFileChange(event) {
    var file = event && event.target && event.target.files ? event.target.files[0] : null;
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(e) {
        var dataUrl = e && e.target ? e.target.result : '';
        document.getElementById('catAvatarUrl').value = dataUrl;
        updateAddAvatarPreview(dataUrl);
    };
    reader.readAsDataURL(file);
}

function updateEditAvatarPreview(url) {
    var preview = document.getElementById('editCatAvatarPreview');
    if (!preview) return;
    var finalUrl = (url || '').trim();
    if (!finalUrl) {
        preview.innerHTML = '';
        return;
    }
    preview.innerHTML = '<img class="cat-avatar-img cat-face" src="' + escapeHtml(finalUrl) + '" alt="头像预览"/>';
}

function onEditCatAvatarUrlInput() {
    var input = document.getElementById('editCatAvatarUrl');
    if (!input) return;
    updateEditAvatarPreview(input.value || '');
}

function uploadEditCatAvatarClick() {
    var fileInput = document.getElementById('editCatAvatarFile');
    if (!fileInput) return;
    fileInput.click();
}

function onEditCatAvatarFileChange(event) {
    var file = event && event.target && event.target.files ? event.target.files[0] : null;
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(e) {
        var dataUrl = e && e.target ? e.target.result : '';
        document.getElementById('editCatAvatarUrl').value = dataUrl;
        updateEditAvatarPreview(dataUrl);
    };
    reader.readAsDataURL(file);
}

function catAvatarHtml(cat) {
    if (cat && cat.avatarUrl) {
        return '<img class="cat-avatar-img cat-face" src="' + escapeHtml(cat.avatarUrl) + '" alt="' + escapeHtml(cat.breed || cat.name || '猫猫') + '"/>';
    }
    return escapeHtml((cat && cat.emoji) || '🐱');
}
function renderColorPicker() {
    document.getElementById('colorPicker').innerHTML = catColors.map(function(c, i) {
        return '<div class="color-option ' + (i === 0 ? 'selected' : '') + '" style="background:' + c + '" onclick="selectColor(\'' + c + '\',this)"></div>';
    }).join('');
}
function selectColor(color, el) {
    document.querySelectorAll('.color-option').forEach(function(e) { e.classList.remove('selected'); });
    el.classList.add('selected');
    selectedColor = color;
}

// ====================== Provider ======================
function selectProvider(p) {
    selectedProvider = p;
    document.querySelectorAll('.provider-card').forEach(function(c) { c.classList.remove('selected'); });
    document.querySelector('.provider-card[data-provider="' + p + '"]').classList.add('selected');
    updateProviderUI(p);
}
function updateProviderUI(p) {
    var cfg = PROVIDERS[p];
    document.getElementById('apiPanelTitle').innerHTML = cfg.icon + ' ' + cfg.name + ' 接口配置';
    var u = document.getElementById('catApiUrl');
    u.placeholder = cfg.defaultUrl;
    u.value = '';
    document.getElementById('apiUrlHint').textContent = cfg.urlHint;
    var m = document.getElementById('catModel');
    m.placeholder = cfg.defaultModel;
    m.value = '';
    var pr = document.getElementById('modelPresets');
    pr.innerHTML = cfg.models.map(function(m) {
        return '<button class="model-preset-btn" onclick="document.getElementById(\'catModel\').value=\'' + m + '\'">' + m + '</button>';
    }).join('');
    pr.style.display = cfg.models.length ? 'flex' : 'none';
    document.getElementById('claudeVersionGroup').style.display = (p === 'claude') ? 'block' : 'none';
}

// ====================== Mode ======================
function switchMode(mode) {
    if (wfState.active && mode !== 'werewolf') {
        if (!confirm('狼人杀进行中，切换将结束游戏。确认？')) return;
        werewolfEnd();
    }
    if (plState.active && mode !== 'pipeline') {
        if (!confirm('流水线进行中，切换将重置。确认？')) return;
        pipelineReset();
    }
    if (dbState.active && mode !== 'debate') {
        if (!confirm('辩论赛进行中，切换将结束辩论。确认？')) return;
        debateEnd();
    }
    gameMode = mode;
    document.querySelectorAll('.mode-card').forEach(function(c) { c.classList.remove('active'); });
    document.querySelector('.mode-card[data-mode="' + mode + '"]').classList.add('active');
    var wp = document.getElementById('werewolfPanel');
    var pp = document.getElementById('pipelinePanel');
    var dp = document.getElementById('debatePanel');
    var mp = document.getElementById('monitorPanel');
    var jt = document.getElementById('judgeToggle');
    if (mode === 'debate') {
        dp.classList.add('active');
        wp.classList.remove('active');
        pp.classList.remove('active');
        mp.classList.remove('active');
        jt.style.display = 'none';
        document.getElementById('chatTitle').textContent = '🎯 猫猫大厅 · 辩论赛模式';
        document.getElementById('messageInput').placeholder = '输入辩题，猫猫们将轮流发言...';
        addSystemMessage('🎯 已切换到辩论赛模式！铲屎官出题，猫猫按顺序轮流发言。');
        debateUpdateOrder();
    } else if (mode === 'werewolf') {
        dp.classList.remove('active');
        wp.classList.add('active');
        pp.classList.remove('active');
        mp.classList.remove('active');
        jt.style.display = 'inline-flex';
        judgeView = true;
        jt.classList.add('active');
        document.getElementById('chatTitle').textContent = '🐺 猫猫大厅 · 狼人杀模式';
        document.getElementById('messageInput').placeholder = '以法官身份发言...';
        addSystemMessage('🐺 已切换到狼人杀模式！默认后端联动，铲屎官将担任法官。');
        werewolfSyncButtonsByState();
    } else if (mode === 'pipeline') {
        dp.classList.remove('active');
        wp.classList.remove('active');
        pp.classList.add('active');
        mp.classList.remove('active');
        jt.style.display = 'none';
        document.getElementById('chatTitle').textContent = '🏗️ 猫猫大厅 · 代码流水线模式';
        document.getElementById('messageInput').placeholder = '输入补充需求或反馈...';
        addSystemMessage('🏗️ 已切换到代码全栈流水线模式！铲屎官当产品经理下需求，猫猫们将依次完成开发、检视、测试。');
        pipelineUpdateRoleAssign();
    } else if (mode === 'monitor') {
        dp.classList.remove('active');
        wp.classList.remove('active');
        pp.classList.remove('active');
        mp.classList.add('active');
        jt.style.display = 'none';
        document.getElementById('chatTitle').textContent = '🛰️ 猫猫大厅 · 上帝监控模式';
        document.getElementById('messageInput').placeholder = '监控模式下请使用左侧控制台按钮...';
        monitorSyncPlayerCountFromCats();
        addSystemMessage('🛰️ 已切换到联动观测：与狼人杀共用同一后端流程（以前端猫猫配置为准）。');
    } else {
        dp.classList.remove('active');
        wp.classList.remove('active');
        pp.classList.remove('active');
        mp.classList.remove('active');
        jt.style.display = 'none';
        document.getElementById('chatTitle').textContent = '🏠 猫猫大厅 · 讨论模式';
        document.getElementById('messageInput').placeholder = '说点什么吧，猫猫们在等你喵～';
        addSystemMessage('💬 已切换到讨论模式，大家畅所欲言吧！');
    }
    monitorApplyThoughtVisibility();
}
function toggleJudgeView() {
    judgeView = !judgeView;
    document.getElementById('judgeToggle').classList.toggle('active', judgeView);
    refreshWerewolfVisibility();
}

// ====================== Werewolf ======================
function werewolfStart() {
    var startBtn = document.getElementById('wpStartBtn');
    if (startBtn) startBtn.disabled = true;
    monitorState.narrationSeenKeys = {};
    monitorState.pendingPhaseChangedPayload = null;
    monitorState.lastStateOrder = -1;
    monitorRenderGlobal('联动启动中：后端编排/开局...');
    monitorAddPhaseLog('联动启动中：后端编排/开局...');
    monitorRegisterAgentsFromFrontendCats().then(function() {
        var roomId = monitorState.roomId;
        wfState.linkedRoomId = roomId;
        addSystemMessage('🚀 已启动后端联动狼人杀：' + roomId, 'night-msg');
        if (!monitorState.isConnected || monitorState.roomId !== roomId) {
            monitorConnectWs();
        }
        return monitorStartGame().then(function() {
            werewolfStartAutoAdvance();
            setTimeout(function() {
                monitorHttp('/api/rooms/' + encodeURIComponent(roomId)).then(function(state) {
                    monitorApplyRoomState(state);
                }).catch(function() {});
            }, 500);
        });
    }).catch(function(err) {
        showToast('❌ 联动启动失败：' + err.message);
        monitorAddPhaseLog('联动启动失败：' + err.message);
    }).finally(function() {
        if (startBtn) startBtn.disabled = false;
    });
}
function buildRolePool(n) {
    var pool = [], wc = Math.max(1, Math.floor(n / 3));
    for (var i = 0; i < wc; i++) pool.push(Object.assign({}, WEREWOLF_ROLES[0]));
    var sp = [WEREWOLF_ROLES[2], WEREWOLF_ROLES[3], WEREWOLF_ROLES[4], WEREWOLF_ROLES[5]];
    var si = 0;
    while (pool.length < n && si < sp.length) pool.push(Object.assign({}, sp[si++]));
    while (pool.length < n) pool.push(Object.assign({}, WEREWOLF_ROLES[1]));
    return pool.sort(function() { return Math.random() - 0.5; });
}
function buildWerewolfSystemPrompt(cat, role) {
    var team = role.team === 'wolf' ? '你是狼人阵营，目标是隐藏身份并猎杀村民。' : '你是好人阵营，目标是找出狼人。';
    var vis = wfState.phase === 'night' ? '现在是夜晚，你的发言只有法官能看到。' : '现在是白天，所有人都能看到你的发言。';
    return cat.personality + '\n\n【狼人杀】\n角色：' + role.name + '（' + role.icon + '）\n' + role.desc + '\n' + team + '\n\n【规则】\n- 保持猫咪口吻\n- ' + vis + '\n- 不要直接暴露身份\n- 回复简短（30-80字）\n- 可以撒谎、伪装、推理';
}
function werewolfNextPhase(isAuto) {
    if (!wfState.active) return;
    monitorAdvance({ auto: !!isAuto }).catch(function() {});
}
function promptCatsForPhase(prompt) {
    var alive = cats.filter(function(c) { return !wfState.eliminated.includes(c.id); });
    alive.forEach(function(cat, idx) {
        setTimeout(function() {
            var role = wfState.roles[cat.id];
            var sys = buildWerewolfSystemPrompt(cat, role);
            triggerCatResponse(cat, { system:sys, messages:[{ role:'user', content:'[法官]: ' + prompt }] }, wfState.phase === 'night');
        }, idx * 1000 + Math.random() * 1500);
    });
}
function werewolfRevealAll() {
    showToast('ℹ️ 默认后端联动模式下不支持前端公开角色。');
}
function werewolfEnd() {
    werewolfStopAutoAdvance();
    wfState.active = false;
    wfState.phase = 'idle';
    wfState.eliminated = [];
    document.getElementById('wpStatus').style.display = 'none';
    werewolfSyncButtonsByState();
    addSystemMessage('⏹ 已结束本地联动视图（后端房间仍可在监控模式继续观察）。');
}
function updateWerewolfStatus() {
    var el = document.getElementById('wpStatus');
    el.style.display = 'block';
    var pm = { night:'wp-phase-night', day:'wp-phase-day', vote:'wp-phase-vote' };
    var pl = { night:'🌙 夜晚', day:'☀️ 白天', vote:'🗳️ 投票' };
    var alive;
    var wolves;
    if (wfState.backendLinked && monitorState.roomId) {
        var backendPlayers = monitorState.players || [];
        alive = backendPlayers.length - wfState.eliminated.length;
        var roleMap = monitorState.playerMap || {};
        wolves = Object.keys(roleMap).filter(function(pid) {
            var row = roleMap[pid] || {};
            return row.alive && row.role === 'werewolf';
        }).length;
    } else {
        alive = cats.filter(function(c) { return !wfState.eliminated.includes(c.id); }).length;
        wolves = cats.filter(function(c) {
            return !wfState.eliminated.includes(c.id) && wfState.roles[c.id] && wfState.roles[c.id].team === 'wolf';
        }).length;
    }
    var linkLabel = wfState.backendLinked ? ' · 🔗联动中' : '';
    el.innerHTML = '<div>第 <b>' + wfState.round + '</b> 轮 · <span class="wp-phase-badge ' + pm[wfState.phase] + '">' + pl[wfState.phase] + '</span>' + linkLabel + '</div><div style="margin-top:4px;">存活：' + alive + ' 只 · 狼人：' + wolves + '</div>';
}
function refreshWerewolfVisibility() {
    document.querySelectorAll('.wf-msg').forEach(function(el) {
        var isNightMsg = el.dataset.wfNight === 'true';
        if (judgeView) {
            el.classList.remove('message-hidden');
        } else if (el.dataset.wfHidden === 'true') {
            el.classList.add('message-hidden');
        }
        if (werewolfShouldHideNightRoleBadge(isNightMsg)) {
            el.classList.add('role-hidden');
        } else {
            el.classList.remove('role-hidden');
        }
    });
}

// ====================== Debate Mode ======================
function debateUpdateOrder() {
    var container = document.getElementById('debateOrder');
    if (!container) return;
    // Sync order with current cats
    dbState.order = cats.map(function(c) { return c.id; });
    if (cats.length < 2) {
        container.innerHTML = '<div style="font-size:12px;color:rgba(255,255,255,0.5);padding:8px 0;">至少需要 2 只猫猫参加辩论</div>';
        return;
    }
    container.innerHTML = dbState.order.map(function(catId, idx) {
        var cat = cats.find(function(c) { return c.id === catId; });
        if (!cat) return '';
        var cls = 'db-order-item';
        if (dbState.active && idx === dbState.turnIndex) cls += ' speaking';
        if (dbState.active && idx < dbState.turnIndex) cls += ' done';
        return '<div class="' + cls + '" draggable="true" data-cat-id="' + catId + '" ondragstart="debateDragStart(event)" ondragover="debateDragOver(event)" ondrop="debateDrop(event)">' +
            '<div class="db-order-num">' + (idx + 1) + '</div>' +
            '<span>' + cat.emoji + ' ' + escapeHtml(cat.name) + '</span>' +
            '</div>';
    }).join('');
}

// Drag & drop reorder
var debateDraggedId = null;
function debateDragStart(e) {
    if (dbState.active) { e.preventDefault(); return; }
    debateDraggedId = e.target.closest('.db-order-item').dataset.catId;
    e.dataTransfer.effectAllowed = 'move';
}
function debateDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}
function debateDrop(e) {
    e.preventDefault();
    if (dbState.active) return;
    var targetId = e.target.closest('.db-order-item').dataset.catId;
    if (!debateDraggedId || !targetId || debateDraggedId === targetId) return;
    var fromIdx = dbState.order.indexOf(debateDraggedId);
    var toIdx = dbState.order.indexOf(targetId);
    if (fromIdx === -1 || toIdx === -1) return;
    dbState.order.splice(fromIdx, 1);
    dbState.order.splice(toIdx, 0, debateDraggedId);
    debateUpdateOrder();
    debateDraggedId = null;
}

function debateStart() {
    if (cats.length < 2) { showToast('⚠️ 至少需要 2 只猫猫参加辩论！'); return; }
    var maxR = parseInt(document.getElementById('debateRounds').value, 10);
    dbState.maxRounds = maxR;
    dbState.active = true;
    dbState.round = 0;
    dbState.turnIndex = 0;
    dbState.speaking = false;
    dbState.queue = [];
    // Ensure order exists
    if (dbState.order.length === 0) dbState.order = cats.map(function(c) { return c.id; });
    document.getElementById('dbStartBtn').disabled = true;
    document.getElementById('dbNextBtn').disabled = false;
    document.getElementById('dbEndBtn').disabled = false;
    var names = dbState.order.map(function(id) {
        var c = cats.find(function(x) { return x.id === id; });
        return c ? c.emoji + c.name : '';
    }).join(' → ');
    addSystemMessage('🎯 辩论赛开始！发言顺序：' + names, 'debate-msg');
    addSystemMessage('💡 铲屎官请输入辩题，猫猫们将按顺序轮流发言。', 'debate-msg');
    var roundLabel = maxR === 0 ? '无限轮' : maxR + ' 轮';
    addSystemMessage('📋 辩论设置：' + cats.length + ' 位辩手 · ' + roundLabel, 'debate-msg');
    debateUpdateStatus();
    debateUpdateOrder();
}

function debateEnd() {
    if (dbState.active) {
        addSystemMessage('🏁 辩论赛结束！感谢各位猫猫精彩的发言！', 'debate-msg');
    }
    dbState.active = false;
    dbState.speaking = false;
    dbState.round = 0;
    dbState.turnIndex = 0;
    dbState.queue = [];
    document.getElementById('dbStartBtn').disabled = false;
    document.getElementById('dbNextBtn').disabled = true;
    document.getElementById('dbEndBtn').disabled = true;
    var st = document.getElementById('dbStatus');
    st.style.display = 'none';
    debateUpdateOrder();
}

function debateUpdateStatus() {
    var st = document.getElementById('dbStatus');
    st.style.display = 'block';
    var currentCat = null;
    if (dbState.turnIndex < dbState.order.length) {
        var cid = dbState.order[dbState.turnIndex];
        currentCat = cats.find(function(c) { return c.id === cid; });
    }
    var roundLabel = dbState.maxRounds === 0 ? '∞' : dbState.maxRounds;
    var html = '<span class="db-round-badge">第 ' + dbState.round + '/' + roundLabel + ' 轮</span>';
    if (currentCat) {
        html += '<div class="db-turn-indicator">' + currentCat.emoji + ' <strong>' + escapeHtml(currentCat.name) + '</strong> ';
        html += dbState.speaking ? '正在发言...' : '准备发言';
        html += '</div>';
    }
    // Progress bar
    var total = dbState.order.length;
    var done = dbState.turnIndex;
    html += '<div style="margin-top:8px;background:rgba(255,255,255,0.15);border-radius:4px;height:6px;overflow:hidden;">';
    html += '<div style="width:' + (total > 0 ? (done / total * 100) : 0) + '%;height:100%;background:#f59e0b;border-radius:4px;transition:width 0.3s;"></div></div>';
    html += '<div style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px;">本轮进度 ' + done + '/' + total + '</div>';
    st.innerHTML = html;
}

function debateTriggerNextSpeaker() {
    if (!dbState.active) return;
    // Check if current round is complete
    if (dbState.turnIndex >= dbState.order.length) {
        dbState.round++;
        // Check if max rounds reached
        if (dbState.maxRounds > 0 && dbState.round > dbState.maxRounds) {
            addSystemMessage('🏁 所有辩论轮次已结束！', 'debate-msg');
            debateEnd();
            return;
        }
        dbState.turnIndex = 0;
        addSystemMessage('🔄 第 ' + dbState.round + ' 轮辩论开始！', 'debate-turn-msg');
    }
    debateUpdateStatus();
    debateUpdateOrder();
    // Get current speaker
    var catId = dbState.order[dbState.turnIndex];
    var cat = cats.find(function(c) { return c.id === catId; });
    if (!cat) {
        // Cat removed, skip
        dbState.turnIndex++;
        debateTriggerNextSpeaker();
        return;
    }
    dbState.speaking = true;
    debateUpdateStatus();
    addSystemMessage('🎙️ 请 ' + cat.emoji + ' ' + escapeHtml(cat.name) + ' 发言（第 ' + dbState.round + ' 轮 · 第 ' + (dbState.turnIndex + 1) + ' 位）', 'debate-turn-msg');
    // Build debate-aware payload
    var debateSystem = cat.personality + '\n\n【辩论赛规则】\n- 你正在参加一场辩论赛，有 ' + cats.length + ' 位辩手参加。\n- 当前是第 ' + dbState.round + ' 轮辩论，你是第 ' + (dbState.turnIndex + 1) + ' 个发言。\n- 请针对辩题和前面辩手的发言，给出你的观点和论据。\n- 可以反驳前面辩手的观点，也可以补充新论点。\n- 发言控制在 80-200 字左右，逻辑清晰、观点鲜明。\n- 保持猫咪口吻，但论点要有说服力。';
    var history = messages.slice(-30).map(function(m) {
        return { role: m.name === cat.name ? 'assistant' : 'user', content: '[' + m.name + ']: ' + m.content };
    });
    var payload = { system: debateSystem, messages: history };
    // Trigger the single cat response with callback for next
    debateTriggerCatResponse(cat, payload);
}

function debateTriggerCatResponse(cat, chatPayload) {
    addThinkingIndicator(cat);
    var done = function(reply) {
        removeThinkingIndicator(cat.id);
        if (reply) {
            addCatMessage(cat, reply, false);
            messages.push({ role:'assistant', name:cat.name, content:reply });
        } else {
            addCatMessage(cat, '喵...（猫猫好像没想好说什么）', false);
        }
        // Advance to next speaker
        dbState.speaking = false;
        dbState.turnIndex++;
        debateUpdateStatus();
        debateUpdateOrder();
        // Auto-trigger next with a short delay
        if (dbState.active) {
            setTimeout(function() {
                debateTriggerNextSpeaker();
            }, 1200);
        }
    };
    var fail = function(err) {
        removeThinkingIndicator(cat.id);
        var msg = err.message;
        if (err instanceof TypeError && (msg === 'Failed to fetch' || msg.indexOf('NetworkError') !== -1 || msg.indexOf('fetch') !== -1)) {
            msg = '网络连接失败，可能是浏览器 CORS 跨域限制。请检查 API 地址或启用 CLI 代理。';
        }
        addCatMessage(cat, '😿 喵呜...连接出了问题：' + msg, false);
        console.error('[' + cat.name + '] Debate API Error:', err);
        // Still advance even on error
        dbState.speaking = false;
        dbState.turnIndex++;
        debateUpdateStatus();
        debateUpdateOrder();
        if (dbState.active) {
            setTimeout(function() { debateTriggerNextSpeaker(); }, 1500);
        }
    };
    if (cat.provider === 'claude') {
        callClaudeAPI(cat, chatPayload).then(done).catch(fail);
    } else {
        callOpenAIAPI(cat, chatPayload).then(done).catch(fail);
    }
}

function debateForceNext() {
    if (!dbState.active) return;
    if (dbState.speaking) {
        showToast('⏳ 当前猫猫正在发言，请等待...');
        return;
    }
    debateTriggerNextSpeaker();
}

// ====================== Pipeline Mode ======================
function pipelineUpdateRoleAssign() {
    var el = document.getElementById('ppRoleAssign');
    if (cats.length < 3) {
        el.innerHTML = '<div style="color:#f59e0b;margin-top:6px;">⚠️ 至少需要 3 只猫猫！当前：' + cats.length + ' 只</div>';
        return;
    }
    el.innerHTML = '<div style="margin-bottom:4px;font-weight:600;color:white;">角色自动分配：</div>' +
        '<div class="pp-step"><span class="pp-role-tag pp-role-dev">🛠️ 设计+开发</span> ' + cats[0].emoji + ' ' + escapeHtml(cats[0].name) + '</div>' +
        '<div class="pp-step"><span class="pp-role-tag pp-role-review">🔍 代码检视</span> ' + cats[1].emoji + ' ' + escapeHtml(cats[1].name) + '</div>' +
        '<div class="pp-step"><span class="pp-role-tag pp-role-test">🧪 测试报告</span> ' + cats[2].emoji + ' ' + escapeHtml(cats[2].name) + '</div>';
}
function pipelineStart() {
    if (cats.length < 3) { showToast('⚠️ 至少需要 3 只猫猫才能启动流水线！'); return; }
    var req = document.getElementById('pipelineRequirement').value.trim();
    if (!req) { showToast('⚠️ 请先输入需求描述！'); return; }
    plState = {
        active: true,
        phase: 'dev',
        requirement: req,
        roles: {
            developer: cats[0],
            reviewer: cats[1],
            tester: cats[2]
        },
        results: {}
    };
    document.getElementById('ppStartBtn').disabled = true;
    document.getElementById('ppResetBtn').disabled = false;
    renderMembers();
    pipelineUpdateStatus();
    addSystemMessage('🚀 流水线已启动！需求已下发。', 'pipeline-msg');
    addSystemMessage('📋 需求描述：' + req, 'pipeline-msg');
    addSystemMessage('🛠️ 阶段一：' + plState.roles.developer.emoji + ' ' + plState.roles.developer.name + ' 正在进行模块设计与代码开发...', 'pipeline-dev-msg');
    // Trigger developer cat
    var devCat = plState.roles.developer;
    var devRole = PIPELINE_ROLES.developer;
    var devPayload = {
        system: devCat.personality + '\n\n' + devRole.systemPrompt(req),
        messages: [{ role:'user', content: devRole.taskPrompt(req) }]
    };
    triggerPipelineCatResponse(devCat, devPayload, 'dev');
}
function triggerPipelineCatResponse(cat, chatPayload, phase) {
    addThinkingIndicator(cat);
    var done = function(reply) {
        removeThinkingIndicator(cat.id);
        if (reply) {
            addCatMessage(cat, reply, false);
            messages.push({ role:'assistant', name:cat.name, content:reply });
            plState.results[phase] = reply;
            pipelineAdvance(phase);
        } else {
            addCatMessage(cat, '喵...（猫猫好像没想好说什么）', false);
        }
    };
    var fail = function(err) {
        removeThinkingIndicator(cat.id);
        var msg = err.message;
        if (err instanceof TypeError && (msg === 'Failed to fetch' || msg.indexOf('NetworkError') !== -1 || msg.indexOf('fetch') !== -1)) {
            msg = '网络连接失败，可能是浏览器 CORS 跨域限制（该 API 不支持浏览器直接调用）。请检查 API 地址是否正确，或尝试使用支持 CORS 的 API 代理地址。';
        }
        addCatMessage(cat, '😿 喵呜...连接出了问题：' + msg, false);
        console.error('[' + cat.name + '] Pipeline API Error:', err);
    };
    if (cat.provider === 'claude') {
        callClaudeAPI(cat, chatPayload).then(done).catch(fail);
    } else {
        callOpenAIAPI(cat, chatPayload).then(done).catch(fail);
    }
}
function pipelineAdvance(completedPhase) {
    if (completedPhase === 'dev') {
        plState.phase = 'review';
        pipelineUpdateStatus();
        addSystemMessage('✅ 设计与开发完成！', 'pipeline-dev-msg');
        addSystemMessage('🔍 阶段二：' + plState.roles.reviewer.emoji + ' ' + plState.roles.reviewer.name + ' 正在进行代码检视...', 'pipeline-review-msg');
        var reviewCat = plState.roles.reviewer;
        var reviewRole = PIPELINE_ROLES.reviewer;
        setTimeout(function() {
            var reviewPayload = {
                system: reviewCat.personality + '\n\n' + reviewRole.systemPrompt(plState.requirement),
                messages: [{ role:'user', content: reviewRole.taskPrompt(plState.requirement, plState.results.dev) }]
            };
            triggerPipelineCatResponse(reviewCat, reviewPayload, 'review');
        }, 1500);
    } else if (completedPhase === 'review') {
        plState.phase = 'test';
        pipelineUpdateStatus();
        addSystemMessage('✅ 代码检视完成！', 'pipeline-review-msg');
        addSystemMessage('🧪 阶段三：' + plState.roles.tester.emoji + ' ' + plState.roles.tester.name + ' 正在编写测试与出具报告...', 'pipeline-test-msg');
        var testCat = plState.roles.tester;
        var testRole = PIPELINE_ROLES.tester;
        setTimeout(function() {
            var testPayload = {
                system: testCat.personality + '\n\n' + testRole.systemPrompt(plState.requirement),
                messages: [{ role:'user', content: testRole.taskPrompt(plState.requirement, plState.results.dev, plState.results.review) }]
            };
            triggerPipelineCatResponse(testCat, testPayload, 'test');
        }, 1500);
    } else if (completedPhase === 'test') {
        plState.phase = 'done';
        pipelineUpdateStatus();
        addSystemMessage('🎉 流水线全部完成！设计开发 → 代码检视 → 测试报告，全流程已走完喵～', 'pipeline-msg');
    }
}
function pipelineUpdateStatus() {
    var el = document.getElementById('ppStatus');
    el.style.display = 'block';
    var phases = [
        { key:'dev', label:'🛠️ 设计+开发', cat: plState.roles.developer },
        { key:'review', label:'🔍 代码检视', cat: plState.roles.reviewer },
        { key:'test', label:'🧪 测试报告', cat: plState.roles.tester }
    ];
    var order = ['dev','review','test','done'];
    var currentIdx = order.indexOf(plState.phase);
    var html = '<div style="margin-bottom:6px;font-weight:600;">流水线进度</div>';
    phases.forEach(function(p, i) {
        var phaseIdx = order.indexOf(p.key);
        var status, badgeClass;
        if (phaseIdx < currentIdx) {
            status = '✅ 完成';
            badgeClass = 'pp-step-done';
        } else if (phaseIdx === currentIdx) {
            status = '⏳ 进行中';
            badgeClass = 'pp-step-active';
        } else {
            status = '⏸ 等待中';
            badgeClass = 'pp-step-waiting';
        }
        html += '<div class="pp-step"><span class="pp-step-badge ' + badgeClass + '">' + p.label + '</span> ' + (p.cat ? p.cat.emoji + ' ' + escapeHtml(p.cat.name) : '') + ' — ' + status + '</div>';
    });
    el.innerHTML = html;
}
function pipelineReset() {
    plState = { active:false, phase:'idle', requirement:'', roles:{}, results:{} };
    document.getElementById('ppStartBtn').disabled = false;
    document.getElementById('ppResetBtn').disabled = true;
    document.getElementById('ppStatus').style.display = 'none';
    document.getElementById('pipelineRequirement').value = '';
    renderMembers();
    addSystemMessage('🔄 流水线已重置，可以开始新的需求。');
    pipelineUpdateRoleAssign();
}

// ====================== Modal ======================
function openAddCatModal() {
    document.getElementById('addCatModal').classList.add('active');
    var nameInput = document.getElementById('catName');
    if (nameInput && !nameInput.dataset.autoBindDone) {
        nameInput.addEventListener('input', function() {
            if ((nameInput.value || '').trim() !== selectedBreed) {
                nameInput.dataset.autoFilledName = '0';
            }
        });
        nameInput.dataset.autoBindDone = '1';
    }
    updateAddAvatarPreview((document.getElementById('catAvatarUrl').value || '').trim());
    setTimeout(function() { document.getElementById('catName').focus(); }, 100);
}
function closeAddCatModal() {
    document.getElementById('addCatModal').classList.remove('active');
    resetForm();
}
function resetForm() {
    ['catName','catApiUrl','catApiKey','catModel','catPersonality','catAvatarUrl'].forEach(function(id) {
        document.getElementById(id).value = '';
    });
    var avatarFileInput = document.getElementById('catAvatarFile');
    if (avatarFileInput) avatarFileInput.value = '';
    document.getElementById('claudeApiVersion').value = '2023-06-01';
    selectedEmoji = CAT_BREED_AVATARS[0].icon;
    selectedAvatarUrl = '';
    selectedBreed = CAT_BREED_AVATARS[0].breed;
    var nameInput = document.getElementById('catName');
    if (nameInput) {
        nameInput.dataset.autoFilledName = '0';
    }
    selectedColor = '#f582ae';
    selectedProvider = 'openai';
    renderEmojiPicker();
    renderColorPicker();
    selectProvider('openai');
    updateAddAvatarPreview('');
}

// ====================== Add / Remove Cat ======================
function normalizeApiUrl(url, provider) {
    if (!url) return '';
    // Remove trailing slash
    url = url.replace(/\/+$/, '');
    // If the URL already contains the expected path, return as-is
    if (provider === 'claude') {
        if (!/\/v1\/messages$/i.test(url)) {
            url += '/v1/messages';
        }
    } else {
        // OpenAI / GLM compatible
        if (!/\/v1\/chat\/completions$/i.test(url) && !/\/chat\/completions$/i.test(url)) {
            url += '/v1/chat/completions';
        }
    }
    return url;
}

function addCat() {
    var name = document.getElementById('catName').value.trim();
    if (!name) { showToast('⚠️ 请给猫猫取个名字！'); return; }
    var gKey = document.getElementById('globalApiKey').value.trim();
    var gModel = document.getElementById('globalModel').value.trim();
    var provider = selectedProvider;
    var cfg = PROVIDERS[provider];
    var rawUrl = document.getElementById('catApiUrl').value.trim();
    var apiUrl = rawUrl ? normalizeApiUrl(rawUrl, provider) : cfg.defaultUrl;
    var customAvatarUrl = document.getElementById('catAvatarUrl').value.trim();
    var cat = {
        id: Date.now().toString(),
        name: name,
        emoji: selectedEmoji,
        avatarUrl: customAvatarUrl || selectedAvatarUrl,
        breed: selectedBreed,
        color: selectedColor,
        personality: document.getElementById('catPersonality').value.trim() || '你是一只叫"' + name + '"的猫咪。用猫咪口吻说话，适当加入"喵"等语气词。你有自己的想法和情绪。',
        provider: provider,
        apiUrl: apiUrl,
        apiKey: document.getElementById('catApiKey').value.trim() || gKey || '',
        model: document.getElementById('catModel').value.trim() || gModel || cfg.defaultModel,
        claudeVersion: document.getElementById('claudeApiVersion').value.trim() || '2023-06-01',
        badgeClass: cfg.badgeClass
    };
    if (!cat.apiKey) { showToast('⚠️ 请填写 API Key（可在全局设置中配置）'); return; }
    cats.push(cat);
    monitorSyncPlayerCountFromCats();
    renderMembers();
    closeAddCatModal();
    updateOnlineCount();
    addSystemMessage('🎉 [' + cat.breed + '] ' + cat.name + ' 加入了聊天室！（' + cfg.icon + ' ' + cfg.name + ' · ' + cat.model + '）');
    showToast('🐱 ' + cat.name + ' 已加入！');
    if (gameMode === 'pipeline') pipelineUpdateRoleAssign();
    if (gameMode === 'debate') debateUpdateOrder();
    monitorCollectInvokeConfig();
    monitorPersistConfig();
    persistCatsToBackendEnv('新增猫猫');
    var intro = buildApiMessages(cat, [{ role:'user', name:'铲屎官', content:'你刚加入聊天室，请简短做一个可爱的自我介绍（不超过50字）。' }], true);
    triggerCatResponse(cat, intro, false);
}
function removeCat(catId) {
    var cat = cats.find(function(c) { return c.id === catId; });
    if (!cat) return;
    cats = cats.filter(function(c) { return c.id !== catId; });
    monitorSyncPlayerCountFromCats();
    renderMembers();
    updateOnlineCount();
    addSystemMessage('🐱 ' + cat.name + ' 离开了聊天室');
    if (gameMode === 'pipeline') pipelineUpdateRoleAssign();
    if (gameMode === 'debate') {
        dbState.order = dbState.order.filter(function(id) { return id !== catId; });
        debateUpdateOrder();
    }
    monitorCollectInvokeConfig();
    monitorPersistConfig();
    persistCatsToBackendEnv('删除猫猫');
}

// ====================== Members ======================
function renderMembers() {
    ttsEnsureSpeakerAssignments();
    monitorRenderGodCatSelectors();
    var list = document.getElementById('membersList');
    var judgeRole = (gameMode === 'werewolf') ? ' <span class="role-badge" style="background:#f39c12;color:white;">⚖️ 法官</span>' : '';
    var html = '<div class="member-card"><div class="member-avatar" style="background:linear-gradient(135deg,#ffd803,#ff8c42);">🧑</div><div class="member-status"></div><div class="member-info"><div class="member-name">铲屎官</div><div class="member-role">主人 · 在线' + judgeRole + '</div></div></div>';
    cats.forEach(function(cat) {
        var isOnline = catOnlineState(cat);
        var statusClass = isOnline ? '' : ' offline';
        var statusText = isOnline ? '在线' : '离线';
        var roleHtml = '';
        if (wfState.active && wfState.roles[cat.id]) {
            var r = wfState.roles[cat.id];
            var dead = wfState.eliminated.includes(cat.id);
            roleHtml = ' <span class="role-badge ' + r.id + '">' + r.icon + ' ' + r.name + '</span>';
            if (dead) {
                var deadCause = wfState.eliminatedCauseByCatId ? wfState.eliminatedCauseByCatId[cat.id] : '';
                var deadLabel = werewolfEliminatedCauseLabel(deadCause);
                roleHtml += ' <span style="color:#e74c3c;font-size:11px;">💀 已淘汰（' + escapeHtml(deadLabel) + '）</span>';
            }
        }
        if (monitorState.aiGod && monitorState.godCatId && monitorState.godCatId === cat.id) {
            roleHtml += ' <span class="role-badge" style="background:#ff6b6b;color:white;">🤖 AI法官</span>';
        }
        if (plState.active && plState.roles) {
            if (plState.roles.developer && plState.roles.developer.id === cat.id) roleHtml = ' <span class="pp-role-tag pp-role-dev">🛠️ 开发</span>';
            if (plState.roles.reviewer && plState.roles.reviewer.id === cat.id) roleHtml = ' <span class="pp-role-tag pp-role-review">🔍 检视</span>';
            if (plState.roles.tester && plState.roles.tester.id === cat.id) roleHtml = ' <span class="pp-role-tag pp-role-test">🧪 测试</span>';
        }
        html += '<div class="member-card"><div class="member-avatar" style="background:linear-gradient(135deg,' + cat.color + ',' + adjustColor(cat.color, -20) + ');" onmouseenter="showCatTooltip(\'' + cat.id + '\',event)" onmouseleave="hideCatTooltip()">' + catAvatarHtml(cat) + '</div><div class="member-status' + statusClass + '"></div><div class="member-info"><div class="member-name">' + escapeHtml(cat.name) + '</div><div class="member-role"><span class="provider-badge ' + cat.badgeClass + '">' + PROVIDERS[cat.provider].icon + ' ' + cat.model + '</span> <span style="font-size:11px;color:rgba(0,0,0,0.45);">' + escapeHtml(cat.breed || '家猫') + '</span> <span style="font-size:11px;color:' + (isOnline ? '#10b981' : '#9ca3af') + ';">' + statusText + '</span>' + roleHtml + '</div></div><button class="member-remove" onclick="removeCat(\'' + cat.id + '\')" title="移除">✕</button></div>';
    });
    list.innerHTML = html;
}
function updateOnlineCount() {
    var onlineCats = cats.filter(function(cat) { return catOnlineState(cat); }).length;
    document.getElementById('onlineCount').textContent = '1 位铲屎官 · ' + onlineCats + '/' + cats.length + ' 只猫猫在线';
    var mc = document.getElementById('memberCount');
    if (mc) mc.textContent = cats.length;
}

function catOnlineState(cat) {
    if (!cat) return true;
    if (monitorState && monitorState.catOnlineById && monitorState.catOnlineById.hasOwnProperty(cat.id)) {
        return !!monitorState.catOnlineById[cat.id];
    }
    return true;
}

function monitorSetAllCatsOnline(online) {
    var next = {};
    cats.forEach(function(cat) {
        next[cat.id] = !!online;
    });
    monitorState.catOnlineById = next;
}

function monitorApplyBootstrapRegistrationResult(data) {
    var boot = (data && data.bootstrap) || {};
    var reg = (boot && boot.registered_agents) || {};
    var agents = reg.agents || {};
    var next = {};
    (monitorState.players || []).forEach(function(pid) {
        var bind = monitorState.playerBindings[pid] || {};
        var catId = bind.catId;
        if (!catId) return;
        next[catId] = !!agents[pid];
    });
    if (!Object.keys(next).length && cats.length > 0) {
        monitorSetAllCatsOnline(false);
        return;
    }
    monitorState.catOnlineById = next;
}

// ====================== Messages ======================
function addSystemMessage(text, cls, options) {
    hideEmptyState();
    var d = document.createElement('div');
    d.className = 'message system-message ' + (cls || '');
    d.textContent = text;
    document.getElementById('chatMessages').appendChild(d);
    scrollToBottom();

    var opts = options || {};
    var speaker = opts.speaker || ttsInferSystemSpeaker(text, cls);
    if (speaker && speaker.key) {
        ttsSpeak(speaker.key, speaker.name || '法官', text);
    }
}
function addUserMessage(text) {
    hideEmptyState();
    var label = gameMode === 'werewolf' ? '铲屎官 (法官)' : '铲屎官';
    var d = document.createElement('div');
    d.className = 'message user-message';
    d.innerHTML = '<div class="message-avatar" style="background:linear-gradient(135deg,#ffd803,#ff8c42);">🧑</div><div class="message-content"><div class="message-sender">' + label + '</div><div class="message-bubble">' + escapeHtml(text) + '</div><div class="message-time">' + getTimeStr() + '</div></div>';
    document.getElementById('chatMessages').appendChild(d);
    scrollToBottom();
}
function addCatMessage(cat, text, isNight) {
    var d = document.createElement('div');
    d.className = 'message cat-message wf-msg';
    d.dataset.wfNight = isNight ? 'true' : 'false';
    if (isNight) d.classList.add('message-night');
    if (gameMode === 'werewolf' && isNight) {
        d.dataset.wfHidden = 'true';
        if (!judgeView) d.classList.add('message-hidden');
    }
    var displayText = d.classList.contains('message-hidden') ? '🔒 [发言已隐藏]' : escapeHtml(text);
    var nightLabel = isNight ? ' 🌙' : '';
    var senderRole = null;
    if (gameMode === 'werewolf') {
        if (cat.role) {
            senderRole = cat.role;
        } else if (wfState.roles && wfState.roles[cat.id]) {
            senderRole = wfState.roles[cat.id];
        }
    }
    var senderRoleHtml = '';
    if (senderRole && senderRole.name) {
        var senderRoleIcon = senderRole.icon || '🎭';
        var senderRoleClass = (senderRole.id || '').replace(/[^a-z0-9_-]/ig, '');
        senderRoleHtml = ' <span class="role-badge sender-role-badge ' + senderRoleClass + '">' + escapeHtml(senderRoleIcon) + ' ' + escapeHtml(senderRole.name) + '</span>';
    }
    d.innerHTML = '<div class="message-avatar" style="background:linear-gradient(135deg,' + cat.color + ',' + adjustColor(cat.color, -20) + ');" onmouseenter="showCatTooltip(\'' + cat.id + '\',event)" onmouseleave="hideCatTooltip()">' + catAvatarHtml(cat) + '</div><div class="message-content"><div class="message-sender">' + escapeHtml(cat.name) + nightLabel + senderRoleHtml + '</div><div class="message-bubble" data-real="' + escapeHtml(text) + '">' + displayText + '</div><div class="message-time">' + getTimeStr() + '</div></div>';
    document.getElementById('chatMessages').appendChild(d);
    if (werewolfShouldHideNightRoleBadge(isNight)) {
        d.classList.add('role-hidden');
    }
    scrollToBottom();
    if (!d.classList.contains('message-hidden')) {
        ttsSpeak(cat.id, cat.name, text);
    }
}
function addThinkingIndicator(cat) {
    var d = document.createElement('div');
    d.className = 'message cat-message';
    d.id = 'thinking-' + cat.id;
    d.innerHTML = '<div class="message-avatar" style="background:linear-gradient(135deg,' + cat.color + ',' + adjustColor(cat.color, -20) + ');" onmouseenter="showCatTooltip(\'' + cat.id + '\',event)" onmouseleave="hideCatTooltip()">' + catAvatarHtml(cat) + '</div><div class="message-content"><div class="message-sender">' + escapeHtml(cat.name) + '</div><div class="message-thinking"><span>' + escapeHtml(cat.name) + ' 正在思考</span><div class="thinking-dots"><span></span><span></span><span></span></div></div></div>';
    document.getElementById('chatMessages').appendChild(d);
    scrollToBottom();
}
function removeThinkingIndicator(catId) {
    var el = document.getElementById('thinking-' + catId);
    if (el) el.remove();
}

// ====================== Send Message ======================
function sendMessage() {
    var input = document.getElementById('messageInput');
    var text = input.value.trim();
    if (!text) return;
    if (gameMode === 'monitor') {
        showToast('🛰️ 监控模式请使用左侧控制台操作。');
        input.value = '';
        autoResize(input);
        return;
    }
    input.value = '';
    autoResize(input);
    addUserMessage(text);
    messages.push({ role:'user', name:'铲屎官', content:text });
    if (cats.length === 0) {
        addSystemMessage('💡 还没有猫猫加入呢～点击左侧「添加一只猫猫」按钮吧！');
        return;
    }
    // Debate mode: sequential speaking
    if (gameMode === 'debate') {
        if (dbState.speaking) {
            showToast('⏳ 猫猫正在发言中，请等待...');
            return;
        }
        if (!dbState.active) {
            // Auto-start debate on first message
            if (cats.length < 2) {
                addSystemMessage('⚠️ 至少需要 2 只猫猫才能辩论！');
                return;
            }
            var maxR = parseInt(document.getElementById('debateRounds').value, 10);
            dbState.maxRounds = maxR;
            dbState.active = true;
            dbState.round = 0;
            dbState.turnIndex = 0;
            dbState.speaking = false;
            if (dbState.order.length === 0) dbState.order = cats.map(function(c) { return c.id; });
            document.getElementById('dbStartBtn').disabled = true;
            document.getElementById('dbNextBtn').disabled = false;
            document.getElementById('dbEndBtn').disabled = false;
            var names = dbState.order.map(function(id) {
                var c = cats.find(function(x) { return x.id === id; });
                return c ? c.emoji + c.name : '';
            }).join(' → ');
            addSystemMessage('🎯 辩论赛自动开始！发言顺序：' + names, 'debate-msg');
        }
        // Start a new round of sequential responses
        dbState.turnIndex = 0;
        dbState.round++;
        addSystemMessage('📢 第 ' + dbState.round + ' 轮辩论开始 — 辩题：' + text, 'debate-turn-msg');
        debateUpdateStatus();
        debateUpdateOrder();
        setTimeout(function() { debateTriggerNextSpeaker(); }, 600);
        return;
    }
    var isNight = (gameMode === 'werewolf' && wfState.active && wfState.phase === 'night');
    // Parse @mentions — if any @catname found, only those cats respond
    var mentionedCats = parseMentions(text);
    var respondingCats = mentionedCats.length > 0 ? mentionedCats : cats;
    respondingCats.forEach(function(cat, idx) {
        if (wfState.active && wfState.eliminated.includes(cat.id)) return;
        setTimeout(function() {
            var payload;
            if (gameMode === 'werewolf' && wfState.active) {
                var role = wfState.roles[cat.id];
                var sys = buildWerewolfSystemPrompt(cat, role);
                payload = { system:sys, messages:[{ role:'user', content:'[法官]: ' + text }] };
            } else {
                payload = buildApiMessages(cat, messages, false);
            }
            triggerCatResponse(cat, payload, isNight);
        }, idx * 800 + Math.random() * 1200);
    });
}

// ====================== Build API Messages ======================
function parseMentions(text) {
    var mentioned = [];
    cats.forEach(function(cat) {
        if (text.indexOf('@' + cat.name) !== -1) {
            mentioned.push(cat);
        }
    });
    return mentioned;
}

function buildApiMessages(cat, msgHistory, isIntro) {
    var systemContent = cat.personality + '\n\n【聊天室规则】\n- 你在一个有多只猫猫和铲屎官的聊天室里。\n- 请用简短自然的口吻回复（30-100字左右）。\n- 可以用"喵"等语气词，但不要每句话都用。\n- 保持自己的性格特点。';
    var history = (isIntro ? msgHistory : msgHistory.slice(-20)).map(function(m) {
        return { role: m.name === cat.name ? 'assistant' : 'user', content: '[' + m.name + ']: ' + m.content };
    });
    return { system: systemContent, messages: history };
}

// ====================== API Call ======================
function triggerCatResponse(cat, chatPayload, isNight) {
    addThinkingIndicator(cat);
    var done = function(reply) {
        removeThinkingIndicator(cat.id);
        if (reply) {
            addCatMessage(cat, reply, isNight || false);
            messages.push({ role:'assistant', name:cat.name, content:reply });
        } else {
            addCatMessage(cat, '喵...（猫猫好像没想好说什么）', isNight || false);
        }
    };
    var fail = function(err) {
        removeThinkingIndicator(cat.id);
        var msg = err.message;
        if (err instanceof TypeError && (msg === 'Failed to fetch' || msg.indexOf('NetworkError') !== -1 || msg.indexOf('fetch') !== -1)) {
            msg = '网络连接失败，可能是浏览器 CORS 跨域限制（该 API 不支持浏览器直接调用）。请检查 API 地址是否正确，或尝试使用支持 CORS 的 API 代理地址。';
        }
        addCatMessage(cat, '😿 喵呜...连接出了问题：' + msg, false);
        console.error('[' + cat.name + '] API Error:', err);
    };
    if (cat.provider === 'claude') {
        callClaudeAPI(cat, chatPayload).then(done).catch(fail);
    } else {
        callOpenAIAPI(cat, chatPayload).then(done).catch(fail);
    }
}

// ---- OpenAI / GLM (both use OpenAI-compatible format) ----
function callOpenAIAPI(cat, payload) {
    var body = {
        model: cat.model,
        messages: [{ role:'system', content:payload.system }].concat(payload.messages),
        max_tokens: 300,
        temperature: 0.85
    };
    return proxyFetch(cat.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type':'application/json', 'Authorization':'Bearer ' + cat.apiKey },
        body: JSON.stringify(body)
    }).then(function(response) {
        if (!response.ok) {
            return response.text().then(function(t) { throw new Error('API (' + response.status + '): ' + t.substring(0, 120)); });
        }
        return response.json();
    }).then(function(data) {
        return (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) ? data.choices[0].message.content.trim() : '';
    });
}

// ---- Claude (Anthropic Messages API) ----
function callClaudeAPI(cat, payload) {
    var merged = [];
    payload.messages.forEach(function(m) {
        if (merged.length > 0 && merged[merged.length - 1].role === m.role) {
            merged[merged.length - 1].content += '\n' + m.content;
        } else {
            merged.push({ role:m.role, content:m.content });
        }
    });
    if (merged.length === 0 || merged[0].role !== 'user') {
        merged.unshift({ role:'user', content:'（对话开始）' });
    }
    var final = [];
    var lastRole = null;
    merged.forEach(function(m) {
        if (m.role === lastRole) {
            final.push({ role: lastRole === 'user' ? 'assistant' : 'user', content:'...' });
        }
        final.push(m);
        lastRole = m.role;
    });
    var body = { model:cat.model, max_tokens:300, system:payload.system, messages:final };
    return proxyFetch(cat.apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type':'application/json',
            'x-api-key': cat.apiKey,
            'anthropic-version': cat.claudeVersion || '2023-06-01',
            'anthropic-dangerous-direct-browser-access':'true'
        },
        body: JSON.stringify(body)
    }).then(function(response) {
        if (!response.ok) {
            return response.text().then(function(t) { throw new Error('Claude (' + response.status + '): ' + t.substring(0, 120)); });
        }
        return response.json();
    }).then(function(data) {
        if (data.content && Array.isArray(data.content)) {
            return data.content.filter(function(b) { return b.type === 'text'; }).map(function(b) { return b.text; }).join('\n').trim();
        }
        return '';
    });
}

// ====================== Helpers ======================
var mentionActive = false, mentionIndex = 0, mentionFiltered = [];

function handleInputKeydown(e) {
    if (mentionActive) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            mentionIndex = (mentionIndex + 1) % mentionFiltered.length;
            renderMentionPopup(mentionFiltered);
            return;
        }
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            mentionIndex = (mentionIndex - 1 + mentionFiltered.length) % mentionFiltered.length;
            renderMentionPopup(mentionFiltered);
            return;
        }
        if (e.key === 'Enter' || e.key === 'Tab') {
            e.preventDefault();
            if (mentionFiltered.length > 0) {
                selectMention(mentionFiltered[mentionIndex]);
            }
            return;
        }
        if (e.key === 'Escape') {
            e.preventDefault();
            closeMentionPopup();
            return;
        }
    }
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function handleInputChange(textarea) {
    autoResize(textarea);
    checkMention(textarea);
}

function checkMention(textarea) {
    var val = textarea.value;
    var pos = textarea.selectionStart;
    // Find the @ symbol before cursor
    var before = val.substring(0, pos);
    var atIdx = before.lastIndexOf('@');
    if (atIdx === -1 || (atIdx > 0 && before[atIdx - 1] !== ' ' && before[atIdx - 1] !== '\n')) {
        closeMentionPopup();
        return;
    }
    var query = before.substring(atIdx + 1).toLowerCase();
    // If there's a space after the query started, close
    if (query.indexOf(' ') !== -1 && query.indexOf(' ') < query.length - 1) {
        closeMentionPopup();
        return;
    }
    mentionFiltered = cats.filter(function(c) {
        return c.name.toLowerCase().indexOf(query) !== -1;
    });
    if (mentionFiltered.length === 0) {
        closeMentionPopup();
        return;
    }
    mentionActive = true;
    mentionIndex = 0;
    renderMentionPopup(mentionFiltered);
}

function renderMentionPopup(list) {
    var popup = document.getElementById('mentionPopup');
    popup.innerHTML = list.map(function(cat, idx) {
        return '<div class="mention-item' + (idx === mentionIndex ? ' active' : '') + '" onmousedown="selectMention(cats.find(function(c){return c.id===\'' + cat.id + '\'}))">'
            + '<div class="mention-avatar" style="background:linear-gradient(135deg,' + cat.color + ',' + adjustColor(cat.color, -20) + ');">' + catAvatarHtml(cat) + '</div>'
            + '<span class="mention-name">' + escapeHtml(cat.name) + '</span>'
            + '<span class="mention-model">' + escapeHtml(cat.model) + '</span>'
            + '</div>';
    }).join('');
    popup.classList.add('active');
}

function selectMention(cat) {
    if (!cat) return;
    var textarea = document.getElementById('messageInput');
    var val = textarea.value;
    var pos = textarea.selectionStart;
    var before = val.substring(0, pos);
    var atIdx = before.lastIndexOf('@');
    if (atIdx === -1) return;
    var after = val.substring(pos);
    var newVal = val.substring(0, atIdx) + '@' + cat.name + ' ' + after;
    textarea.value = newVal;
    var newPos = atIdx + 1 + cat.name.length + 1;
    textarea.selectionStart = newPos;
    textarea.selectionEnd = newPos;
    textarea.focus();
    closeMentionPopup();
}

function closeMentionPopup() {
    mentionActive = false;
    mentionIndex = 0;
    mentionFiltered = [];
    var popup = document.getElementById('mentionPopup');
    popup.classList.remove('active');
}
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}
function scrollToBottom() {
    var container = document.getElementById('chatMessages');
    requestAnimationFrame(function() { container.scrollTop = container.scrollHeight; });
}
function hideEmptyState() {
    var el = document.getElementById('emptyState');
    if (el) el.remove();
}
function getTimeStr() {
    return new Date().toLocaleTimeString('zh-CN', { hour:'2-digit', minute:'2-digit' });
}
function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
function adjustColor(hex, amount) {
    var r = parseInt(hex.slice(1, 3), 16);
    var g = parseInt(hex.slice(3, 5), 16);
    var b = parseInt(hex.slice(5, 7), 16);
    r = Math.max(0, Math.min(255, r + amount));
    g = Math.max(0, Math.min(255, g + amount));
    b = Math.max(0, Math.min(255, b + amount));
    return '#' + r.toString(16).padStart(2, '0') + g.toString(16).padStart(2, '0') + b.toString(16).padStart(2, '0');
}
function showToast(message) {
    var container = document.getElementById('toastContainer');
    var toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function() { toast.remove(); }, 3000);
}
function toggleGlobalSettings() {
    var el = document.getElementById('globalSettings');
    var arrow = document.getElementById('settingsArrow');
    if (el.style.display === 'none') { el.style.display = 'block'; arrow.textContent = '▼'; }
    else { el.style.display = 'none'; arrow.textContent = '▶'; }
}
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}
function toggleRightPanel() {
    var panel = document.getElementById('rightPanel');
    var btn = document.getElementById('memberToggle');
    panel.classList.toggle('collapsed');
    btn.classList.toggle('active', !panel.classList.contains('collapsed'));
}
function toggleCliProxy() {
    var el = document.getElementById('cliProxySettings');
    var arrow = document.getElementById('cliArrow');
    if (el.style.display === 'none') { el.style.display = 'block'; arrow.textContent = '▼'; }
    else { el.style.display = 'none'; arrow.textContent = '▶'; }
}
function toggleTtsSettings() {
    var el = document.getElementById('ttsSettings');
    var arrow = document.getElementById('ttsArrow');
    if (el.style.display === 'none') { el.style.display = 'block'; arrow.textContent = '▼'; }
    else { el.style.display = 'none'; arrow.textContent = '▶'; }
}
function onTtsEnabledToggle() {
    var cb = document.getElementById('ttsEnabled');
    ttsState.enabled = !!(cb && cb.checked);
    if (!ttsState.enabled && ttsState.supported) {
        try { window.speechSynthesis.cancel(); } catch (_) {}
    }
    ttsSaveSettings();
    ttsUpdateSettingsUI();
}
function onTtsRateInput() {
    var input = document.getElementById('ttsRate');
    var v = Number(input && input.value ? input.value : 1);
    if (!Number.isFinite(v)) v = 1;
    ttsState.rate = Math.max(0.6, Math.min(1.6, v));
    ttsSaveSettings();
    ttsUpdateSettingsUI();
}
function onTtsVolumeInput() {
    var input = document.getElementById('ttsVolume');
    var v = Number(input && input.value != null ? input.value : 1);
    if (!Number.isFinite(v)) v = 1;
    ttsState.volume = Math.max(0, Math.min(1, v));
    ttsSaveSettings();
    ttsUpdateSettingsUI();
}
function onCliProxyToggle() {
    var cb = document.getElementById('cliProxyEnabled');
    var label = document.getElementById('cliProxyLabel');
    cliProxy.enabled = cb.checked;
    if (cb.checked) {
        label.textContent = '已启用';
        label.style.color = '#16a34a';
        cliProxy.url = document.getElementById('cliProxyUrl').value.trim().replace(/\/+$/, '') || 'http://localhost:3456';
        testCliConnection();
    } else {
        label.textContent = '未启用';
        label.style.color = '';
        cliProxy.connected = false;
        updateCliStatusDot('off');
        var st = document.getElementById('cliConnStatus');
        st.style.display = 'none';
    }
}
function testCliConnection() {
    var proxyUrl = (document.getElementById('cliProxyUrl').value.trim().replace(/\/+$/, '') || 'http://localhost:3456');
    cliProxy.url = proxyUrl;
    var st = document.getElementById('cliConnStatus');
    st.style.display = 'block';
    st.className = 'cli-conn-status';
    st.textContent = '🔄 正在连接 ' + proxyUrl + ' ...';
    updateCliStatusDot('off');
    fetch(proxyUrl + '/health', { method: 'GET' })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.status === 'ok') {
                cliProxy.connected = true;
                st.className = 'cli-conn-status success';
                st.innerHTML = '✅ 连接成功！' + data.name + '<br>已处理 ' + data.requests + ' 个请求 · 运行 ' + Math.floor(data.uptime) + 's';
                updateCliStatusDot('connected');
                showToast('🟢 CLI 代理连接成功！');
            } else {
                throw new Error('意外的响应');
            }
        })
        .catch(function(err) {
            cliProxy.connected = false;
            st.className = 'cli-conn-status error';
            st.innerHTML = '❌ 连接失败！请确认 CLI 已启动<br><code>node cat_chat_cli.js</code>';
            updateCliStatusDot('error');
        });
}
function updateCliStatusDot(state) {
    var dot = document.getElementById('cliStatusDot');
    dot.className = 'cli-status' + (state === 'connected' ? ' connected' : state === 'error' ? ' error' : '');
}
function proxyFetch(url, options) {
    if (!cliProxy.enabled || !cliProxy.connected) {
        return fetch(url, options);
    }
    var proxyBody = {
        targetUrl: url,
        method: options.method || 'POST',
        headers: options.headers || {},
        body: options.body ? JSON.parse(options.body) : undefined
    };
    return fetch(cliProxy.url + '/proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(proxyBody)
    });
}

// ====================== Monitor Mode (Werewolf Backend) ======================
function monitorInit() {
    monitorLoadPersistedConfig();
    var apiInput = document.getElementById('monitorApiBase');
    var countInput = document.getElementById('monitorPlayerCount');
    var hostInput = document.getElementById('monitorAgentHost');
    var portInput = document.getElementById('monitorAgentStartPort');
    var apiUrlInput = document.getElementById('monitorModelApiUrl');
    var apiKeyInput = document.getElementById('monitorModelApiKey');
    var modelInput = document.getElementById('monitorModelName');
    var cliInput = document.getElementById('monitorCliCommand');
    if (!apiInput || !countInput) return;
    apiInput.value = monitorState.apiBase;
    countInput.value = String(monitorState.playerCount);
    if (hostInput) hostInput.value = monitorState.agentHost;
    if (portInput) portInput.value = String(monitorState.agentStartPort);
    if (apiUrlInput) apiUrlInput.value = monitorState.modelApiUrl;
    if (apiKeyInput) apiKeyInput.value = monitorState.modelApiKey;
    if (modelInput) modelInput.value = monitorState.modelName;
    if (cliInput) cliInput.value = monitorState.cliCommand;
    // Restore AI god config
    var aiGodEl = document.getElementById('monitorAiGod');
    if (aiGodEl) {
        aiGodEl.checked = !!monitorState.aiGod;
        aiGodEl.addEventListener('change', function() {
            if (wfState.active) {
                aiGodEl.checked = !!monitorState.aiGod;
                showToast('⚠️ 游戏已开始，不能再切换 AI 法官模式');
                return;
            }
            var show = aiGodEl.checked;
            var sec = document.getElementById('monitorGodConfig');
            if (sec) sec.style.display = show ? 'block' : 'none';
            // Sync to werewolf panel
            var wpCb = document.getElementById('wpAiGodToggle');
            if (wpCb) wpCb.checked = show;
            var wpSec = document.getElementById('wpAiGodConfig');
            if (wpSec) wpSec.style.display = show ? 'block' : 'none';
            monitorCollectInvokeConfig();
            monitorPersistConfig();
        });
        var sec = document.getElementById('monitorGodConfig');
        if (sec) sec.style.display = aiGodEl.checked ? 'block' : 'none';
    }
    // Also restore werewolf panel AI god toggle
    var wpGodEl = document.getElementById('wpAiGodToggle');
    if (wpGodEl) {
        wpGodEl.checked = !!monitorState.aiGod;
        var wpSec = document.getElementById('wpAiGodConfig');
        if (wpSec) wpSec.style.display = wpGodEl.checked ? 'block' : 'none';
    }
    var wpHideRoleEl = document.getElementById('wpHideNightRole');
    if (wpHideRoleEl) {
        wpHideRoleEl.checked = !!wfState.hideNightRoleForAudience;
    }
    var monitorThoughtEl = document.getElementById('monitorShowThought');
    if (monitorThoughtEl) {
        monitorThoughtEl.checked = !!monitorState.showThoughtInMonitor;
    }
    monitorRenderGodCatSelectors();
    monitorLockGodConfigIfStarted();
    monitorBindConfigPersistence();
    monitorRenderGlobal('未连接');
    monitorApplyThoughtVisibility();
}

function monitorLoadPersistedConfig() {
    try {
        var raw = localStorage.getItem(MONITOR_CONFIG_STORAGE_KEY);
        if (!raw) return;
        var saved = JSON.parse(raw);
        if (!saved || typeof saved !== 'object') return;
        monitorState.apiBase = saved.apiBase || monitorState.apiBase;
        monitorState.playerCount = parseInt(saved.playerCount, 10) || monitorState.playerCount;
        monitorState.agentHost = saved.agentHost || monitorState.agentHost;
        monitorState.agentStartPort = parseInt(saved.agentStartPort, 10) || monitorState.agentStartPort;
        monitorState.modelApiUrl = saved.modelApiUrl || '';
        monitorState.modelApiKey = saved.modelApiKey || '';
        monitorState.modelName = saved.modelName || '';
        monitorState.cliCommand = saved.cliCommand || '';
        monitorState.aiGod = !!saved.aiGod;
        monitorState.godCatId = saved.godCatId || '';
        if (typeof saved.hideNightRoleForAudience === 'boolean') {
            monitorState.hideNightRoleForAudience = saved.hideNightRoleForAudience;
            wfState.hideNightRoleForAudience = saved.hideNightRoleForAudience;
        }
        if (typeof saved.showThoughtInMonitor === 'boolean') {
            monitorState.showThoughtInMonitor = saved.showThoughtInMonitor;
        }
    } catch (e) {
        console.warn('monitor config load failed', e);
    }
}

function monitorPersistConfig() {
    try {
        var payload = {
            apiBase: monitorState.apiBase,
            playerCount: monitorState.playerCount,
            agentHost: monitorState.agentHost,
            agentStartPort: monitorState.agentStartPort,
            modelApiUrl: monitorState.modelApiUrl,
            modelApiKey: monitorState.modelApiKey,
            modelName: monitorState.modelName,
            cliCommand: monitorState.cliCommand,
            aiGod: monitorState.aiGod || false,
            godCatId: monitorState.godCatId || '',
            hideNightRoleForAudience: !!wfState.hideNightRoleForAudience,
            showThoughtInMonitor: !!monitorState.showThoughtInMonitor
        };
        localStorage.setItem(MONITOR_CONFIG_STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {
        console.warn('monitor config save failed', e);
    }
}

function monitorBindConfigPersistence() {
    var ids = [
        'monitorApiBase',
        'monitorPlayerCount',
        'monitorAgentHost',
        'monitorAgentStartPort',
        'monitorModelApiUrl',
        'monitorModelApiKey',
        'monitorModelName',
        'monitorCliCommand',
        'monitorAiGod',
        'monitorShowThought',
        'monitorGodCatId',
        'wpGodCatId',
        'wpHideNightRole'
    ];
    ids.forEach(function(id) {
        var el = document.getElementById(id);
        if (!el || el.dataset.persistBound === '1') return;
        var handler = function() {
            monitorCollectInvokeConfig();
            monitorPersistConfig();
        };
        el.addEventListener('change', handler);
        el.addEventListener('blur', handler);
        el.dataset.persistBound = '1';
    });
}

function monitorCollectInvokeConfig() {
    monitorState.apiBase = monitorNormalizeBase(document.getElementById('monitorApiBase').value) || monitorState.apiBase;
    monitorState.playerCount = parseInt(document.getElementById('monitorPlayerCount').value, 10) || monitorState.playerCount;
    var host = (document.getElementById('monitorAgentHost').value || '').trim() || 'http://127.0.0.1';
    var startPort = parseInt(document.getElementById('monitorAgentStartPort').value, 10) || 9101;
    var apiUrl = (document.getElementById('monitorModelApiUrl').value || '').trim();
    var apiKey = (document.getElementById('monitorModelApiKey').value || '').trim();
    var modelName = (document.getElementById('monitorModelName').value || '').trim();
    var cliCommand = (document.getElementById('monitorCliCommand').value || '').trim();

    var aiGodEl = document.getElementById('monitorAiGod');
    var wpAiGodEl = document.getElementById('wpAiGodToggle');
    var aiGod = (aiGodEl && aiGodEl.checked) || (wpAiGodEl && wpAiGodEl.checked) || false;
    var godCatId = (document.getElementById('monitorGodCatId') && document.getElementById('monitorGodCatId').value || '').trim()
        || (document.getElementById('wpGodCatId') && document.getElementById('wpGodCatId').value || '').trim()
        || monitorState.godCatId
        || (cats[0] ? cats[0].id : '');

    monitorState.agentHost = host;
    monitorState.agentStartPort = startPort;
    monitorState.modelApiUrl = apiUrl;
    monitorState.modelApiKey = apiKey;
    monitorState.modelName = modelName;
    monitorState.cliCommand = cliCommand;
    monitorState.aiGod = aiGod;
    monitorState.godCatId = godCatId;
    var thoughtEl = document.getElementById('monitorShowThought');
    monitorState.showThoughtInMonitor = !(thoughtEl && thoughtEl.checked === false);
    var hideRoleEl = document.getElementById('wpHideNightRole');
    var hideNightRole = !(hideRoleEl && hideRoleEl.checked === false);
    wfState.hideNightRoleForAudience = hideNightRole;
    monitorState.hideNightRoleForAudience = hideNightRole;
    monitorPersistConfig();

    return {
        host: host,
        startPort: startPort,
        apiUrl: apiUrl,
        apiKey: apiKey,
        modelName: modelName,
        cliCommand: cliCommand,
        aiGod: aiGod,
        godCatId: godCatId
    };
}

function monitorRegisterAgents() {
    monitorRegisterAgentsFromFrontendCats().then(function(results) {
        showToast('✅ Agent注册完成：' + Object.keys(results || {}).length + '只猫猫');
    }).catch(function(err) {
        monitorSetAllCatsOnline(false);
        renderMembers();
        updateOnlineCount();
        showToast('❌ Agent注册失败：' + err.message);
        monitorAddPhaseLog('Agent注册失败：' + err.message);
    });
}

function monitorNormalizeBase(url) {
    return (url || '').trim().replace(/\/+$/, '');
}

function monitorHttp(path, options) {
    monitorState.apiBase = monitorNormalizeBase(document.getElementById('monitorApiBase').value) || 'http://127.0.0.1:8000';
    document.getElementById('monitorApiBase').value = monitorState.apiBase;
    monitorPersistConfig();
    var req = Object.assign({ method: 'GET', headers: { 'Content-Type': 'application/json' } }, options || {});
    var timeoutMs = (options && typeof options.timeoutMs === 'number') ? options.timeoutMs : 25000;
    delete req.timeoutMs;
    var controller = new AbortController();
    req.signal = controller.signal;
    var timer = setTimeout(function() { controller.abort(); }, timeoutMs);
    return fetch(monitorState.apiBase + path, req).then(function(res) {
        if (!res.ok) {
            return res.text().then(function(t) { throw new Error('HTTP ' + res.status + ': ' + t.substring(0, 140)); });
        }
        return res.json();
    }).catch(function(err) {
        if (err && err.name === 'AbortError') {
            throw new Error('请求超时(' + timeoutMs + 'ms): ' + path);
        }
        throw err;
    }).finally(function() {
        clearTimeout(timer);
    });
}

function monitorCreateRoom() {
    monitorHttp('/api/ai/bootstrap-from-env', {
        timeoutMs: 86400000,
        method: 'POST',
        body: JSON.stringify({})
    }).then(function(data) {
        monitorState.speechSeenKeys = {};
        monitorState.speechRenderedKeys = {};
        monitorState.narrationSeenKeys = {};
        monitorState.lastStateOrder = -1;
        monitorState.speechTimeline = [];
        monitorState.roomId = data.room_id;
        monitorState.ownerId = data.owner_id || 'cat_01';
        monitorState.players = data.players || [];
        monitorState.aiGod = !!data.ai_god;
        if (data.god_cat_id) monitorState.godCatId = data.god_cat_id;
        wfState.linkedRoomId = monitorState.roomId;
        monitorState.playerBindings = monitorBuildBindingMap(monitorState.players);
        monitorApplyBootstrapRegistrationResult(data);
        document.getElementById('monitorRoomId').value = monitorState.roomId;
        monitorSyncViewOptions();
        renderMembers();
        updateOnlineCount();
        var judgeMode = monitorJudgeModeLabel(data);
        monitorRenderGlobal('后端已完成建房与拉起：' + monitorState.roomId + '（' + (data.player_count || monitorState.players.length) + '人） · ' + judgeMode);
        addSystemMessage('🛰️ 后端已完成建房+拉起+注册：' + monitorState.roomId + '（来源：环境变量，' + judgeMode + '）', 'pipeline-msg');
        showToast('✅ 后端拉起成功');
    }).catch(function(err) {
        monitorSetAllCatsOnline(false);
        renderMembers();
        updateOnlineCount();
        showToast('❌ 创建房间失败：' + err.message);
        monitorRenderGlobal('创建失败：' + err.message);
    });
}

function monitorRoomId() {
    var id = (document.getElementById('monitorRoomId').value || '').trim();
    if (!id) id = monitorState.roomId;
    monitorState.roomId = id;
    return id;
}

function monitorWsUrl(roomId, playerId) {
    var base = monitorState.apiBase || 'http://127.0.0.1:8000';
    var wsBase = base.replace(/^http:/i, 'ws:').replace(/^https:/i, 'wss:');
    return wsBase + '/ws/' + encodeURIComponent(roomId) + '/' + encodeURIComponent(playerId);
}

function monitorConnectWs() {
    var roomId = monitorRoomId();
    if (!roomId) { showToast('⚠️ 请先创建或填写房间 ID'); return; }
    if (monitorState.ws) {
        try { monitorState.ws.close(); } catch (e) {}
        monitorState.ws = null;
    }
    var playerId = monitorState.ownerId || 'cat_01';
    var wsUrl = monitorWsUrl(roomId, playerId);
    var ws = new WebSocket(wsUrl);
    monitorState.wsLastEventId = 0;
    monitorState.pendingRoomState = null;
    monitorState.roomStateFlushScheduled = false;
    if (monitorState.phaseStatePullTimer) {
        clearTimeout(monitorState.phaseStatePullTimer);
        monitorState.phaseStatePullTimer = null;
    }
    monitorState.ws = ws;
    monitorRenderGlobal('正在连接：' + wsUrl);

    ws.onopen = function() {
        monitorState.isConnected = true;
        ws.send(JSON.stringify({ type: 'subscribe', room_id: roomId, view_mode: monitorState.viewMode || 'god' }));
        monitorRenderGlobal('WS已连接 · room=' + roomId + ' · view=' + (monitorState.viewMode || 'god'));
        showToast('🔌 WS 连接成功');
    };

    ws.onmessage = function(event) {
        try {
            var msg = JSON.parse(event.data);
            monitorHandleWsEvent(msg);
        } catch (e) {
            console.error('monitor ws parse error', e);
        }
    };

    ws.onclose = function() {
        monitorState.isConnected = false;
        monitorRenderGlobal('WS已断开');
    };

    ws.onerror = function() {
        monitorState.isConnected = false;
        monitorRenderGlobal('WS连接异常');
    };
}

function monitorHandleWsEvent(msg) {
    var eventId = Number(msg && msg.event_id);
    if (Number.isFinite(eventId) && eventId > 0) {
        if (eventId <= (monitorState.wsLastEventId || 0)) {
            return;
        }
        monitorState.wsLastEventId = eventId;
    }
    var evt = msg.event;
    var payload = msg.payload || {};
    if (evt === 'subscribed') {
        monitorState.viewMode = payload.view_mode || monitorState.viewMode;
        document.getElementById('monitorViewMode').value = monitorState.viewMode;
        monitorRenderGlobal('订阅成功 · view=' + monitorState.viewMode);
        return;
    }
    if (evt === 'view_changed') {
        monitorState.viewMode = payload.view_mode || monitorState.viewMode;
        monitorRenderGlobal('视角已切换：' + monitorState.viewMode);
        return;
    }
    if (evt === 'room_state') {
        monitorQueueRoomState(payload);
        return;
    }
    if (evt === 'phase_changed') {
        monitorAddPhaseLog('[' + getTimeStr() + '] ' + (payload.phase || 'unknown') + ' · active=' + ((payload.active_players || []).join(',') || '-'));
        if (payload.god_view && monitorState.viewMode === 'god') {
            monitorAddPhaseLog('🐺 狼队目标: ' + JSON.stringify(payload.god_view));
        }
        monitorState.pendingPhaseChangedPayload = payload;
        monitorSchedulePhaseStatePull();
        return;
    }
    if (evt === 'agent_status_update') {
        monitorApplyAgentStatusPayload(payload);
        return;
    }
}

function monitorApplyRoomState(state) {
    var stateOrder = monitorStateOrderValue(state);
    if (stateOrder < (monitorState.lastStateOrder || -1)) {
        return;
    }
    monitorState.lastStateOrder = stateOrder;

    monitorState.roomId = state.room_id || monitorState.roomId;
    if (state.owner_id) monitorState.ownerId = state.owner_id;
    var rid = document.getElementById('monitorRoomId');
    if (rid && monitorState.roomId) rid.value = monitorState.roomId;
    var players = state.players || [];
    var playableCats = monitorPlayableCats();
    monitorState.players = players.map(function(p) { return p.player_id; });
    var map = {};
    players.forEach(function(p, idx) {
        var bound = monitorState.playerBindings[p.player_id] || {};
        if (!bound.catId && p && p.nickname) {
            var foundByName = cats.find(function(cat) { return (cat.name || '').trim() === (p.nickname || '').trim(); });
            if (foundByName) {
                bound = {
                    catId: foundByName.id,
                    nickname: foundByName.name,
                    breed: foundByName.breed,
                    color: foundByName.color,
                    emoji: foundByName.emoji,
                    avatarUrl: foundByName.avatarUrl || ''
                };
                monitorState.playerBindings[p.player_id] = bound;
            }
        }
        if (!bound.catId) {
            var catByIndex = playableCats[idx];
            if (catByIndex) {
                bound = {
                    catId: catByIndex.id,
                    nickname: catByIndex.name,
                    breed: catByIndex.breed,
                    color: catByIndex.color,
                    emoji: catByIndex.emoji,
                    avatarUrl: catByIndex.avatarUrl || ''
                };
                monitorState.playerBindings[p.player_id] = bound;
            }
        }
        map[p.player_id] = {
            nickname: bound.nickname || p.nickname || p.player_id,
            breed: bound.breed || '',
            role: p.role || '',
            alive: !!p.alive,
            online: !!p.online
        };
        if (bound.catId) {
            monitorState.catOnlineById[bound.catId] = !!p.online;
        }
    });
    monitorState.playerMap = map;
    monitorSyncViewOptions();
    var alive = players.filter(function(p) { return p.alive; }).length;
    var total = players.length;
    monitorRenderGlobal('phase=' + state.phase + ' · round=' + (state.round_no || 0) + ' · alive=' + alive + '/' + total + ' · game_over=' + (!!state.game_over));
    monitorRenderGodBoard(state);
    renderMembers();
    updateOnlineCount();
    if (Array.isArray(state.speech_history)) {
        monitorSortSpeechHistory(state.speech_history).forEach(function(s) {
            var key = [
                s.timestamp || '',
                s.player_id || '',
                s.phase || '',
                s.role || '',
                s.content || '',
                s.thought_content || ''
            ].join('|');
            if (!monitorState.speechSeenKeys[key]) {
                monitorState.speechSeenKeys[key] = true;
                monitorState.speechTimeline.push(s);
                if (!monitorState.speechRenderedKeys[key]) {
                    monitorState.speechRenderedKeys[key] = true;
                    werewolfRenderLinkedSpeech(s);
                }
            }
        });
        if (monitorState.speechTimeline.length > 240) {
            monitorState.speechTimeline = monitorState.speechTimeline.slice(-240);
        }
        monitorRenderSpeech();
    }
    monitorNarrateFromRoomState(state);
    var pendingPhase = monitorState.pendingPhaseChangedPayload;
    if (pendingPhase && (!pendingPhase.phase || pendingPhase.phase === state.phase)) {
        monitorNarrateFromPhaseChanged(pendingPhase);
        monitorState.pendingPhaseChangedPayload = null;
    }
    werewolfSyncFromBackendState(state);
    monitorLockGodConfigIfStarted();
}

function monitorApplyAgentStatusPayload(payload) {
    var row = {
        player_id: payload.player_id,
        online: payload.status === 'online',
        status: payload.status,
        error_msg: payload.error_msg || '',
        last_heartbeat: payload.last_heartbeat || ''
    };
    var container = document.getElementById('monitorHealth');
    var lines = container.getAttribute('data-lines') ? JSON.parse(container.getAttribute('data-lines')) : [];
    var text = row.player_id + ' · ' + row.status + (row.error_msg ? (' · ' + row.error_msg) : '');
    lines.unshift(text);
    lines = lines.slice(0, 24);
    container.setAttribute('data-lines', JSON.stringify(lines));
    container.innerHTML = lines.map(function(l) { return '<div class="mn-list-item">' + escapeHtml(l) + '</div>'; }).join('') || '<div class="mn-list-item">暂无</div>';
}

function monitorStartGame() {
    var roomId = monitorRoomId();
    if (!roomId) { showToast('⚠️ 请先创建房间'); return Promise.reject(new Error('房间 ID 为空')); }
    var owner = monitorState.ownerId || 'cat_01';
    return monitorHttp('/api/rooms/' + encodeURIComponent(roomId) + '/start?owner_id=' + encodeURIComponent(owner), {
        timeoutMs: 15000,
        method: 'POST'
    }).then(function(data) {
        wfState.active = true;
        monitorRenderGlobal('游戏已启动 · phase=' + data.phase);
        monitorHttp('/api/rooms/' + encodeURIComponent(roomId), { timeoutMs: 10000 }).then(function(state) {
            monitorApplyRoomState(state);
            monitorAddPhaseLog('开局成功 -> ' + (state.phase || data.phase || 'unknown'));
        }).catch(function(err) {
            monitorAddPhaseLog('开局后拉取状态失败：' + err.message);
        });
        showToast('▶️ 游戏已启动（自动推进中）');
    }).catch(function(err) {
        showToast('❌ 启动失败：' + err.message);
        monitorAddPhaseLog('启动失败：' + err.message);
    });
}

function monitorAdvance(options) {
    var opts = options || {};
    var roomId = monitorRoomId();
    if (!roomId) {
        if (!opts.auto) showToast('⚠️ 请先创建房间');
        return Promise.reject(new Error('房间 ID 为空'));
    }
    return monitorHttp('/api/ai/rooms/' + encodeURIComponent(roomId) + '/run-phase', {
        timeoutMs: 120000,
        method: 'POST'
    }).then(function(data) {
        var state = data && data.state ? data.state : null;
        if (!state) {
            throw new Error('run-phase 返回缺少 state');
        }
        monitorApplyRoomState(state);
        monitorAddPhaseLog('上帝推进 -> ' + (state.phase || 'unknown'));
        if (wfState.active && !state.game_over) {
            werewolfScheduleAutoAdvance();
        } else {
            werewolfStopAutoAdvance();
        }
        return data;
    }).catch(function(err) {
        if (!opts.auto) {
            showToast('❌ 推进失败：' + err.message);
        }
        monitorAddPhaseLog('推进失败：' + err.message);
        if (opts.auto && wfState.active) {
            werewolfScheduleAutoAdvance(3000);
        }
        throw err;
    });
}

function monitorLoadConfig() {
    var roomId = monitorRoomId();
    if (!roomId) { showToast('⚠️ 请先创建房间'); return; }
    monitorHttp('/api/rooms/' + encodeURIComponent(roomId) + '/config').then(function(data) {
        document.getElementById('monitorConfig').textContent = JSON.stringify(data, null, 2);
    }).catch(function(err) {
        showToast('❌ 获取配置失败：' + err.message);
    });
}

function monitorLoadAgents() {
    var roomId = monitorRoomId();
    if (!roomId) { showToast('⚠️ 请先创建房间'); return; }
    monitorHttp('/api/agents/status?room_id=' + encodeURIComponent(roomId)).then(function(data) {
        var agents = data.agents || {};
        var rows = Object.keys(agents).sort().map(function(pid) {
            var item = agents[pid] || {};
            var status = item.online ? 'online' : 'offline';
            if (item.error_msg) status = 'error';
            return pid + ' · ' + status + ' · failed=' + (item.failed_count || 0);
        });
        var container = document.getElementById('monitorHealth');
        container.innerHTML = rows.map(function(r) { return '<div class="mn-list-item">' + escapeHtml(r) + '</div>'; }).join('') || '<div class="mn-list-item">暂无</div>';
        container.setAttribute('data-lines', JSON.stringify(rows));
    }).catch(function(err) {
        showToast('❌ 获取状态失败：' + err.message);
    });
}

function monitorLoadChildProcesses() {
    var roomId = monitorRoomId();
    if (!roomId) { showToast('⚠️ 请先创建房间'); return; }
    monitorHttp('/api/ai/rooms/' + encodeURIComponent(roomId) + '/agents/processes').then(function(data) {
        var procs = data.child_processes || {};
        var keys = Object.keys(procs).sort();
        var rows = keys.map(function(pid) {
            var item = procs[pid] || {};
            var running = item.running ? 'running' : 'stopped';
            return pid + ' · ' + running + ' · pid=' + (item.pid || '-') + ' · ' + (item.endpoint || '-');
        });
        document.getElementById('monitorConfig').textContent = JSON.stringify(data, null, 2);
        monitorAddPhaseLog('子进程状态已刷新：' + (rows.length || 0) + ' 个');
        showToast('🧩 子进程状态已加载');
        if (!rows.length) return;
        var container = document.getElementById('monitorHealth');
        container.innerHTML = rows.map(function(r) { return '<div class="mn-list-item">' + escapeHtml(r) + '</div>'; }).join('');
        container.setAttribute('data-lines', JSON.stringify(rows));
    }).catch(function(err) {
        showToast('❌ 获取子进程状态失败：' + err.message);
    });
}

function monitorChangeView() {
    var mode = document.getElementById('monitorViewMode').value;
    monitorState.viewMode = mode;
    if (!monitorState.ws || monitorState.ws.readyState !== WebSocket.OPEN) {
        monitorRenderGlobal('视角已设置（待连接后生效）：' + mode);
        return;
    }
    monitorState.ws.send(JSON.stringify({ type: 'change_view', mode: mode }));
}

function monitorSyncViewOptions() {
    var sel = document.getElementById('monitorViewMode');
    if (!sel) return;
    var options = ['god'].concat((monitorState.players || []).map(function(pid) { return 'player:' + pid; }));
    var current = monitorState.viewMode || 'god';
    sel.innerHTML = options.map(function(v) { return '<option value="' + v + '">' + v + '</option>'; }).join('');
    if (options.indexOf(current) === -1) current = 'god';
    sel.value = current;
    monitorState.viewMode = current;
}

function monitorAddPhaseLog(text) {
    monitorState.phaseLog.unshift(text);
    monitorState.phaseLog = monitorState.phaseLog.slice(0, 40);
    var el = document.getElementById('monitorPhaseLog');
    el.innerHTML = monitorState.phaseLog.map(function(row) { return '<div class="mn-list-item">' + escapeHtml(row) + '</div>'; }).join('') || '<div class="mn-list-item">暂无</div>';
}

function monitorRenderSpeech() {
    var el = document.getElementById('monitorSpeech');
    var rows = monitorState.speechTimeline.slice(-30).reverse().map(function(s) {
        var phase = s.phase ? ('[' + s.phase + '] ') : '';
        var fallback = s.is_fallback ? (' (fallback' + (s.fallback_reason ? ':' + s.fallback_reason : '') + ')') : '';
        var thought = (s.thought_content || '').trim();
        var thoughtPart = (thought && monitorState.showThoughtInMonitor) ? (' | 思考(仅法官): ' + thought) : '';
        return '<div class="mn-list-item">' + escapeHtml((s.timestamp || '').replace('T', ' ').slice(0, 19) + ' ' + phase + (s.player_id || '?') + ': ' + (s.content || '') + thoughtPart + fallback) + '</div>';
    });
    el.innerHTML = rows.join('') || '<div class="mn-list-item">暂无</div>';
}

function monitorRenderGlobal(text) {
    document.getElementById('monitorGlobal').textContent = text;
}

// ====================== Boot ======================
init();

// ====================== Export / Import Cats ======================
function exportCats() {
    if (cats.length === 0) { showToast('⚠️ 没有猫猫可以导出！'); return; }
    var data = {
        version: 1,
        exportTime: new Date().toISOString(),
        cats: cats.map(function(c) {
            return {
                name: c.name,
                emoji: c.emoji,
                avatarUrl: c.avatarUrl,
                breed: c.breed,
                color: c.color,
                personality: c.personality,
                provider: c.provider,
                apiUrl: c.apiUrl,
                apiKey: c.apiKey,
                model: c.model,
                claudeVersion: c.claudeVersion,
                badgeClass: c.badgeClass
            };
        })
    };
    var json = JSON.stringify(data, null, 2);
    var blob = new Blob([json], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'catchat_cats_' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('✅ 已导出 ' + cats.length + ' 只猫猫的配置！');
}

function importCatsClick() {
    document.getElementById('importCatsFile').click();
}

function importCatsFile(event) {
    var file = event.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(e) {
        try {
            var data = JSON.parse(e.target.result);
            if (!data.cats || !Array.isArray(data.cats) || data.cats.length === 0) {
                showToast('❌ 文件格式错误或没有猫猫数据！');
                return;
            }
            var imported = normalizeImportedCats(data.cats, cats.length);
            imported.forEach(function(c) { cats.push(c); });
            var count = imported.length;
            renderMembers();
            updateOnlineCount();
            if (gameMode === 'pipeline') pipelineUpdateRoleAssign();
            if (gameMode === 'debate') debateUpdateOrder();
            addSystemMessage('📥 已导入 ' + count + ' 只猫猫的配置！');
            showToast('✅ 成功导入 ' + count + ' 只猫猫！');
            monitorCollectInvokeConfig();
            monitorPersistConfig();
            persistCatsToBackendEnv('导入猫猫配置');
        } catch (err) {
            showToast('❌ 解析文件失败：' + err.message);
        }
    };
    reader.readAsText(file);
    event.target.value = '';
}

// ====================== Cat Tooltip ======================
var catTooltipEl = null;
var catTooltipTimer = null;
function showCatTooltip(catId, event) {
    var cat = cats.find(function(c) { return c.id === catId; });
    if (!cat) return;
    if (catTooltipTimer) { clearTimeout(catTooltipTimer); catTooltipTimer = null; }
    hideCatTooltipNow();
    var tip = document.createElement('div');
    tip.className = 'cat-tooltip';
    tip.setAttribute('data-tooltip-cat', catId);
    tip.onmouseenter = function() { if (catTooltipTimer) { clearTimeout(catTooltipTimer); catTooltipTimer = null; } };
    tip.onmouseleave = function() { scheduleCatTooltipHide(); };
    var cfg = PROVIDERS[cat.provider] || {};
    var rows = '';
    rows += '<div class="tt-row"><span class="tt-label">提供商</span><span class="tt-value">' + (cfg.icon || '') + ' ' + (cfg.name || cat.provider) + '</span></div>';
    rows += '<div class="tt-row"><span class="tt-label">模型</span><span class="tt-value">' + escapeHtml(cat.model) + '</span></div>';
    rows += '<div class="tt-row"><span class="tt-label">API 地址</span><span class="tt-value">' + escapeHtml(cat.apiUrl) + '</span></div>';
    if (cat.provider === 'claude') {
        rows += '<div class="tt-row"><span class="tt-label">API 版本</span><span class="tt-value">' + escapeHtml(cat.claudeVersion || '2023-06-01') + '</span></div>';
    }
    var personalityPreview = cat.personality.length > 120 ? cat.personality.substring(0, 120) + '…' : cat.personality;
    tip.innerHTML = '<div class="tt-header"><div class="tt-avatar" style="background:linear-gradient(135deg,' + cat.color + ',' + adjustColor(cat.color, -20) + ');">' + catAvatarHtml(cat) + '</div><div class="tt-name">' + escapeHtml(cat.name) + '</div><button class="tt-edit-btn" onclick="openEditCatModal(\'' + cat.id + '\')">✏️ 编辑</button></div>' + rows + '<div class="tt-row"><span class="tt-label">品种</span><span class="tt-value">' + escapeHtml(cat.breed || '家猫') + '</span></div><div class="tt-personality">🐾 ' + escapeHtml(personalityPreview) + '</div>';
    document.body.appendChild(tip);
    catTooltipEl = tip;
    // Position tooltip near the avatar
    var rect = event.target.closest('.member-avatar, .message-avatar').getBoundingClientRect();
    var tipW = tip.offsetWidth, tipH = tip.offsetHeight;
    var left = rect.right + 10;
    var top = rect.top;
    if (left + tipW > window.innerWidth - 10) left = rect.left - tipW - 10;
    if (top + tipH > window.innerHeight - 10) top = window.innerHeight - tipH - 10;
    if (top < 10) top = 10;
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
}
function scheduleCatTooltipHide() {
    if (catTooltipTimer) clearTimeout(catTooltipTimer);
    catTooltipTimer = setTimeout(function() { hideCatTooltipNow(); catTooltipTimer = null; }, 200);
}
function hideCatTooltip() {
    scheduleCatTooltipHide();
}
function hideCatTooltipNow() {
    if (catTooltipEl) { catTooltipEl.remove(); catTooltipEl = null; }
}

// ====================== Edit Cat Modal ======================
var editCatProvider = 'openai';
function openEditCatModal(catId) {
    hideCatTooltipNow();
    var cat = cats.find(function(c) { return c.id === catId; });
    if (!cat) return;
    document.getElementById('editCatId').value = catId;
    document.getElementById('editCatName').value = cat.name;
    document.getElementById('editCatBreed').value = cat.breed || '';
    document.getElementById('editCatAvatarUrl').value = cat.avatarUrl || '';
    var editAvatarFileInput = document.getElementById('editCatAvatarFile');
    if (editAvatarFileInput) editAvatarFileInput.value = '';
    updateEditAvatarPreview(cat.avatarUrl || '');
    document.getElementById('editCatPersonality').value = cat.personality;
    document.getElementById('editCatApiUrl').value = cat.apiUrl;
    document.getElementById('editCatApiKey').value = cat.apiKey;
    document.getElementById('editCatModel').value = cat.model;
    document.getElementById('editClaudeApiVersion').value = cat.claudeVersion || '2023-06-01';
    editCatProvider = cat.provider;
    // Render provider buttons
    var provHtml = '';
    Object.keys(PROVIDERS).forEach(function(k) {
        var p = PROVIDERS[k];
        provHtml += '<button class="edit-prov-btn ' + (k === cat.provider ? 'selected' : '') + '" data-prov="' + k + '" onclick="editSelectProvider(\'' + k + '\')">' + p.icon + ' ' + p.name + '</button>';
    });
    document.getElementById('editProviderCards').innerHTML = provHtml;
    updateEditProviderUI(cat.provider);
    document.getElementById('editCatModal').classList.add('active');
}
function editSelectProvider(p) {
    editCatProvider = p;
    document.querySelectorAll('#editProviderCards .edit-prov-btn').forEach(function(b) { b.classList.remove('selected'); });
    document.querySelector('#editProviderCards .edit-prov-btn[data-prov="' + p + '"]').classList.add('selected');
    updateEditProviderUI(p);
}
function updateEditProviderUI(p) {
    var cfg = PROVIDERS[p];
    document.getElementById('editCatApiUrl').placeholder = cfg.defaultUrl;
    document.getElementById('editApiUrlHint').textContent = cfg.urlHint;
    document.getElementById('editCatModel').placeholder = cfg.defaultModel;
    var pr = document.getElementById('editModelPresets');
    pr.innerHTML = cfg.models.map(function(m) {
        return '<button class="edit-preset-btn" onclick="document.getElementById(\'editCatModel\').value=\'' + m + '\';">' + m + '</button>';
    }).join('');
    pr.style.display = cfg.models.length ? 'flex' : 'none';
    document.getElementById('editClaudeVersionGroup').style.display = (p === 'claude') ? 'block' : 'none';
}
function closeEditCatModal() {
    document.getElementById('editCatModal').classList.remove('active');
}
function saveEditCat() {
    var catId = document.getElementById('editCatId').value;
    var cat = cats.find(function(c) { return c.id === catId; });
    if (!cat) { showToast('❌ 猫猫不存在'); return; }
    var name = document.getElementById('editCatName').value.trim();
    if (!name) { showToast('⚠️ 名字不能为空！'); return; }
    var provider = editCatProvider;
    var cfg = PROVIDERS[provider];
    var rawUrl = document.getElementById('editCatApiUrl').value.trim();
    var apiUrl = rawUrl ? normalizeApiUrl(rawUrl, provider) : cfg.defaultUrl;
    var apiKey = document.getElementById('editCatApiKey').value.trim();
    if (!apiKey) {
        var gKey = document.getElementById('globalApiKey').value.trim();
        apiKey = gKey || '';
    }
    if (!apiKey) { showToast('⚠️ 请填写 API Key'); return; }
    var editedBreed = document.getElementById('editCatBreed').value.trim();
    var editedAvatarUrl = document.getElementById('editCatAvatarUrl').value.trim();
    cat.name = name;
    if (editedBreed) {
        cat.breed = editedBreed;
    }
    if (editedAvatarUrl) {
        cat.avatarUrl = editedAvatarUrl;
    } else {
        cat.avatarUrl = '';
    }
    cat.personality = document.getElementById('editCatPersonality').value.trim() || cat.personality;
    cat.provider = provider;
    cat.apiUrl = apiUrl;
    cat.apiKey = document.getElementById('editCatApiKey').value.trim() || document.getElementById('globalApiKey').value.trim() || '';
    cat.model = document.getElementById('editCatModel').value.trim() || cfg.defaultModel;
    cat.claudeVersion = document.getElementById('editClaudeApiVersion').value.trim() || '2023-06-01';
    cat.badgeClass = cfg.badgeClass;
    monitorSyncPlayerCountFromCats();
    renderMembers();
    closeEditCatModal();
    showToast('✅ ' + cat.name + ' 的档案已更新！');
    addSystemMessage('✏️ ' + cat.name + ' 的配置已被修改（' + cfg.icon + ' ' + cfg.name + ' · ' + cat.model + '）');
    monitorCollectInvokeConfig();
    monitorPersistConfig();
    persistCatsToBackendEnv('编辑猫猫');
}

function monitorBuildBindingMap(players) {
    var bindings = {};
    var playableCats = monitorPlayableCats();
    (players || []).forEach(function(pid, idx) {
        var cat = playableCats[idx];
        if (!cat) return;
        bindings[pid] = {
            catId: cat.id,
            nickname: cat.name,
            breed: cat.breed,
            color: cat.color,
            emoji: cat.emoji,
            avatarUrl: cat.avatarUrl || ''
        };
    });
    return bindings;
}

function monitorValidateCatsForBackend(cfg) {
    var playableCount = monitorPlayableCats().length;
    if (cfg.aiGod && cats.length < 9) {
        throw new Error('启用AI法官时，至少需要 9 只猫猫（含1只法官猫 + 8只参赛猫）');
    }
    if (playableCount < 8 || playableCount > 12) {
        throw new Error('联动模式要求参赛猫猫数量为 8~12，当前为 ' + playableCount);
    }
    if (cfg.cliCommand) return;
    var missing = monitorPlayableCats().filter(function(cat) {
        var key = (cat.apiKey || '').trim() || (document.getElementById('globalApiKey').value || '').trim();
        return !key;
    });
    if (missing.length > 0) {
        throw new Error('以下猫猫缺少 API Key：' + missing.map(function(c) { return c.name; }).join('、'));
    }
}

function monitorEnsureAiRoomFromCats() {
    var cfg = monitorCollectInvokeConfig();
    monitorValidateCatsForBackend(cfg);
    var wantedCount = cats.length;
    var existingRoomId = monitorRoomId();

    var createRoom = function() {
        var body = { owner_nickname: cats[0].name || 'cat_01', player_count: wantedCount };
        if (cfg.aiGod) {
            body.ai_god = true;
            body.god_api_url = cfg.godApiUrl;
            body.god_api_key = cfg.godApiKey;
            body.god_model_name = cfg.godModelName;
            body.god_provider = cfg.godProvider;
            body.god_temperature = cfg.godTemperature;
        }
        return monitorHttp('/api/ai/rooms', {
            method: 'POST',
            body: JSON.stringify(body)
        }).then(function(data) {
            monitorState.roomId = data.room_id;
            monitorState.ownerId = data.owner_id || 'cat_01';
            monitorState.players = data.players || [];
            monitorState.playerBindings = monitorBuildBindingMap(monitorState.players);
            wfState.linkedRoomId = monitorState.roomId;
            document.getElementById('monitorRoomId').value = monitorState.roomId;
            monitorSyncViewOptions();
            var aiGodLabel = data.ai_god ? ' · 🤖AI法官' : '';
            monitorAddPhaseLog('已按前端猫猫创建 AI 房间：' + monitorState.roomId + '（' + wantedCount + '人' + aiGodLabel + '）');
            return data;
        });
    };

    if (!existingRoomId) {
        return createRoom();
    }

    return monitorHttp('/api/rooms/' + encodeURIComponent(existingRoomId)).then(function(state) {
        var count = (state.players || []).length;
        monitorState.roomId = state.room_id || existingRoomId;
        monitorState.ownerId = state.owner_id || monitorState.ownerId;
        monitorState.players = (state.players || []).map(function(p) { return p.player_id; });
        if (count !== wantedCount) {
            monitorAddPhaseLog('现有房间人数(' + count + ')与前端猫猫数(' + wantedCount + ')不一致，自动新建房间。');
            return createRoom();
        }
        monitorState.playerBindings = monitorBuildBindingMap(monitorState.players);
        wfState.linkedRoomId = monitorState.roomId;
        return {
            room_id: monitorState.roomId,
            owner_id: monitorState.ownerId,
            players: monitorState.players
        };
    }).catch(function() {
        return createRoom();
    });
}

function monitorRegisterAgentsFromFrontendCats() {
    return monitorHttp('/api/ai/bootstrap-from-env', {
        timeoutMs: 86400000,
        method: 'POST',
        body: JSON.stringify({})
    }).then(function(data) {
        monitorState.roomId = data.room_id;
        monitorState.ownerId = data.owner_id || 'cat_01';
        monitorState.players = data.players || [];
        monitorState.aiGod = !!data.ai_god;
        if (data.god_cat_id) monitorState.godCatId = data.god_cat_id;
        wfState.linkedRoomId = monitorState.roomId;
        monitorState.playerBindings = monitorBuildBindingMap(monitorState.players);
        monitorApplyBootstrapRegistrationResult(data);
        document.getElementById('monitorRoomId').value = monitorState.roomId;
        monitorSyncViewOptions();
        renderMembers();
        updateOnlineCount();

        var boot = (data && data.bootstrap) || {};
        var reg = (boot && boot.registered_agents) || {};
        var successCount = Number(reg.count || 0);
        if (!successCount) {
            successCount = Number((data.players || []).length || monitorState.players.length || 0);
        }
        var retriesTotal = Number(reg.retries_total || 0);
        var retriedAgents = Number(reg.retried_agents || 0);
        var agents = reg.agents || {};
        var firstPid = Object.keys(agents)[0];
        var mode = (firstPid && agents[firstPid] && agents[firstPid].invoke_mode) || 'api';
        var judgeMode = monitorJudgeModeLabel(data);
        monitorRenderGlobal('后端编排完成：' + successCount + ' 个Agent · mode=' + mode + ' · room=' + monitorState.roomId + ' · ' + judgeMode);
        monitorAddPhaseLog('后端拉起并注册完成：' + successCount + ' 个 · 重试次数=' + retriesTotal + '（涉及' + retriedAgents + '只） · ' + judgeMode);
        Object.keys(agents).forEach(function(pid) {
            var item = agents[pid] || {};
            var attempts = Number(item.attempts || 1);
            if (attempts <= 1) return;
            var mapped = monitorState.playerMap[pid] || {};
            var name = mapped.nickname || item.player_id || pid;
            var lastErr = item.last_retry_error ? ('；最近错误：' + item.last_retry_error) : '';
            monitorAddPhaseLog('♻️ ' + name + ' 注册重试 ' + (attempts - 1) + ' 次后成功' + lastErr);
        });
        addSystemMessage('🤖 后端已完成全流程拉起与注册（' + successCount + '只）', 'pipeline-msg');
        return agents;
    }).catch(function(err) {
        monitorSetAllCatsOnline(false);
        renderMembers();
        updateOnlineCount();
        throw err;
    });
}

function monitorRoleLabel(role) {
    var map = {
        werewolf: '狼人',
        villager: '村民',
        seer: '预言家',
        witch: '女巫',
        hunter: '猎人',
        guard: '守卫',
        fool: '白痴'
    };
    return map[role] || (role || '未知');
}

function monitorRenderGodBoard(state) {
    var el = document.getElementById('monitorGodBoard');
    if (!el) return;
    var players = (state && state.players) || [];
    if (!players.length) {
        el.innerHTML = '<div class="mn-list-item">暂无</div>';
        return;
    }
    var rows = players.map(function(p) {
        var mapped = monitorState.playerMap[p.player_id] || {};
        var name = mapped.nickname || p.nickname || p.player_id;
        var role = monitorRoleLabel(p.role || mapped.role);
        var alive = p.alive ? '存活' : '出局';
        var status = p.online ? '在线' : '离线';
        return name + ' · ' + role + ' · ' + alive + ' · ' + status;
    });
    el.innerHTML = rows.map(function(r) { return '<div class="mn-list-item">' + escapeHtml(r) + '</div>'; }).join('');
}

function monitorQueueRoomState(state) {
    monitorState.pendingRoomState = state || null;
    if (monitorState.phaseStatePullTimer) {
        clearTimeout(monitorState.phaseStatePullTimer);
        monitorState.phaseStatePullTimer = null;
    }
    if (monitorState.roomStateFlushScheduled) return;
    monitorState.roomStateFlushScheduled = true;
    requestAnimationFrame(function() {
        monitorState.roomStateFlushScheduled = false;
        var latest = monitorState.pendingRoomState;
        monitorState.pendingRoomState = null;
        if (!latest) return;
        monitorApplyRoomState(latest);
    });
}

function monitorSchedulePhaseStatePull() {
    if (monitorState.phaseStatePullTimer) {
        clearTimeout(monitorState.phaseStatePullTimer);
        monitorState.phaseStatePullTimer = null;
    }
    monitorState.phaseStatePullTimer = setTimeout(function() {
        monitorState.phaseStatePullTimer = null;
        if (monitorState.pendingRoomState) return;
        var roomId = monitorRoomId();
        if (!roomId) return;
        monitorHttp('/api/rooms/' + encodeURIComponent(roomId)).then(function(state) {
            monitorQueueRoomState(state);
        }).catch(function() {});
    }, 260);
}