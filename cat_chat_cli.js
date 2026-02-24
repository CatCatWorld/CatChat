#!/usr/bin/env node
// ============================================================
//  🐱 CatChat CLI — 本地代理服务器
//  解决浏览器 CORS 跨域限制，代理转发 API 请求
//  启动方式：node cat_chat_cli.js [--port 3456]
// ============================================================

const http = require('http');
const https = require('https');
const url = require('url');

// ====================== Config ======================
const DEFAULT_PORT = 3456;
let PORT = DEFAULT_PORT;

// Parse CLI arguments
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
    if ((args[i] === '--port' || args[i] === '-p') && args[i + 1]) {
        PORT = parseInt(args[i + 1], 10) || DEFAULT_PORT;
        i++;
    }
    if (args[i] === '--help' || args[i] === '-h') {
        console.log(`
  🐱 CatChat CLI — 本地代理服务器

  用法: node cat_chat_cli.js [选项]

  选项:
    -p, --port <端口>    指定服务端口 (默认: ${DEFAULT_PORT})
    -h, --help           显示帮助信息

  说明:
    启动后，在 CatChat 网页的「本地 CLI 代理」设置中
    填入 http://localhost:<端口> 并开启开关即可。
    所有 API 请求将通过本地代理转发，绕过浏览器 CORS 限制。
`);
        process.exit(0);
    }
}

// ====================== Color Helpers ======================
const C = {
    reset:   '\x1b[0m',
    bold:    '\x1b[1m',
    dim:     '\x1b[2m',
    red:     '\x1b[31m',
    green:   '\x1b[32m',
    yellow:  '\x1b[33m',
    blue:    '\x1b[34m',
    magenta: '\x1b[35m',
    cyan:    '\x1b[36m',
    white:   '\x1b[37m',
    bgBlue:  '\x1b[44m',
    bgGreen: '\x1b[42m',
    bgRed:   '\x1b[41m',
};

function log(icon, color, label, msg) {
    const ts = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    console.log(`${C.dim}[${ts}]${C.reset} ${icon} ${color}${C.bold}${label}${C.reset} ${msg || ''}`);
}

// ====================== CORS Headers ======================
function setCorsHeaders(res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', '*');
    res.setHeader('Access-Control-Max-Age', '86400');
}

// ====================== Proxy Logic ======================
function proxyRequest(targetUrl, method, headers, body) {
    return new Promise(function(resolve, reject) {
        const parsed = new URL(targetUrl);
        const transport = parsed.protocol === 'https:' ? https : http;

        // Forward headers, remove host-related ones
        const proxyHeaders = Object.assign({}, headers);
        delete proxyHeaders['host'];
        delete proxyHeaders['origin'];
        delete proxyHeaders['referer'];
        delete proxyHeaders['connection'];
        delete proxyHeaders['accept-encoding']; // avoid compressed responses

        const options = {
            hostname: parsed.hostname,
            port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
            path: parsed.pathname + parsed.search,
            method: method,
            headers: proxyHeaders,
            timeout: 120000
        };

        const proxyReq = transport.request(options, function(proxyRes) {
            let chunks = [];
            proxyRes.on('data', function(chunk) { chunks.push(chunk); });
            proxyRes.on('end', function() {
                const responseBody = Buffer.concat(chunks).toString('utf-8');
                resolve({
                    statusCode: proxyRes.statusCode,
                    headers: proxyRes.headers,
                    body: responseBody
                });
            });
        });

        proxyReq.on('error', function(err) {
            reject(err);
        });

        proxyReq.on('timeout', function() {
            proxyReq.destroy();
            reject(new Error('代理请求超时 (120s)'));
        });

        if (body) {
            proxyReq.write(body);
        }
        proxyReq.end();
    });
}

// ====================== Request Counter ======================
let requestCount = 0;

// ====================== HTTP Server ======================
const server = http.createServer(function(req, res) {
    setCorsHeaders(res);

    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    // Health check endpoint
    if (req.url === '/health' || req.url === '/ping') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', name: 'CatChat CLI Proxy', version: '1.0.0', uptime: process.uptime(), requests: requestCount }));
        return;
    }

    // Proxy endpoint: /proxy
    if (req.url === '/proxy' && req.method === 'POST') {
        let body = '';
        req.on('data', function(chunk) { body += chunk; });
        req.on('end', function() {
            requestCount++;
            const reqId = requestCount;

            let payload;
            try {
                payload = JSON.parse(body);
            } catch (e) {
                log('❌', C.red, 'PARSE ERROR', '无法解析请求体');
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: '无法解析请求体 JSON' }));
                return;
            }

            const targetUrl = payload.targetUrl;
            const targetMethod = payload.method || 'POST';
            const targetHeaders = payload.headers || {};
            const targetBody = payload.body ? (typeof payload.body === 'string' ? payload.body : JSON.stringify(payload.body)) : '';

            if (!targetUrl) {
                log('❌', C.red, 'ERROR', '缺少 targetUrl');
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: '缺少 targetUrl 参数' }));
                return;
            }

            // Extract model & cat name from body for logging
            let modelName = '';
            let msgPreview = '';
            try {
                const b = typeof payload.body === 'string' ? JSON.parse(payload.body) : payload.body;
                modelName = b.model || '';
                if (b.messages && b.messages.length > 0) {
                    const lastMsg = b.messages[b.messages.length - 1];
                    msgPreview = (lastMsg.content || '').substring(0, 60);
                    if ((lastMsg.content || '').length > 60) msgPreview += '...';
                }
            } catch(e) {}

            log('📤', C.cyan, `REQUEST #${reqId}`, `→ ${C.bold}${targetUrl}${C.reset}`);
            if (modelName) log('  ', C.dim, '  模型', modelName);
            if (msgPreview) log('  ', C.dim, '  消息', msgPreview);

            const startTime = Date.now();

            proxyRequest(targetUrl, targetMethod, targetHeaders, targetBody)
                .then(function(proxyRes) {
                    const elapsed = Date.now() - startTime;
                    const statusColor = proxyRes.statusCode < 400 ? C.green : C.red;

                    // Extract reply preview
                    let replyPreview = '';
                    try {
                        const rd = JSON.parse(proxyRes.body);
                        if (rd.choices && rd.choices[0] && rd.choices[0].message) {
                            replyPreview = (rd.choices[0].message.content || '').substring(0, 80);
                            if ((rd.choices[0].message.content || '').length > 80) replyPreview += '...';
                        } else if (rd.content && Array.isArray(rd.content)) {
                            const txt = rd.content.filter(function(b) { return b.type === 'text'; }).map(function(b) { return b.text; }).join('');
                            replyPreview = txt.substring(0, 80);
                            if (txt.length > 80) replyPreview += '...';
                        }
                    } catch(e) {}

                    log('📥', statusColor, `RESPONSE #${reqId}`, `← ${C.bold}${proxyRes.statusCode}${C.reset} (${elapsed}ms)`);
                    if (replyPreview) log('  ', C.dim, '  回复', replyPreview);
                    console.log('');

                    // Forward response headers selectively
                    const fwdHeaders = { 'Content-Type': proxyRes.headers['content-type'] || 'application/json' };
                    res.writeHead(proxyRes.statusCode, fwdHeaders);
                    res.end(proxyRes.body);
                })
                .catch(function(err) {
                    const elapsed = Date.now() - startTime;
                    log('❌', C.red, `ERROR #${reqId}`, `${err.message} (${elapsed}ms)`);
                    console.log('');
                    res.writeHead(502, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: '代理请求失败: ' + err.message }));
                });
        });
        return;
    }

    // 404 for everything else
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found. 请使用 POST /proxy 端点。' }));
});

// ====================== Start ======================
server.listen(PORT, function() {
    console.log('');
    console.log(`${C.bgBlue}${C.white}${C.bold}                                        ${C.reset}`);
    console.log(`${C.bgBlue}${C.white}${C.bold}   🐱 CatChat CLI 代理服务器 v1.0.0     ${C.reset}`);
    console.log(`${C.bgBlue}${C.white}${C.bold}                                        ${C.reset}`);
    console.log('');
    console.log(`  ${C.green}✓${C.reset} 服务已启动: ${C.bold}${C.cyan}http://localhost:${PORT}${C.reset}`);
    console.log(`  ${C.green}✓${C.reset} 代理端点:   ${C.bold}POST http://localhost:${PORT}/proxy${C.reset}`);
    console.log(`  ${C.green}✓${C.reset} 健康检查:   ${C.bold}GET  http://localhost:${PORT}/health${C.reset}`);
    console.log('');
    console.log(`  ${C.yellow}📋 使用方法:${C.reset}`);
    console.log(`     1. 打开 CatChat 网页`);
    console.log(`     2. 在侧边栏找到「本地 CLI 代理」设置`);
    console.log(`     3. 填入地址: ${C.cyan}http://localhost:${PORT}${C.reset}`);
    console.log(`     4. 开启代理开关`);
    console.log(`     5. 所有请求将通过本地代理转发，无 CORS 限制`);
    console.log('');
    console.log(`  ${C.dim}按 Ctrl+C 停止服务${C.reset}`);
    console.log(`${C.dim}${'─'.repeat(50)}${C.reset}`);
    console.log('');
});

server.on('error', function(err) {
    if (err.code === 'EADDRINUSE') {
        console.error(`\n${C.red}❌ 端口 ${PORT} 已被占用！请使用 --port 指定其他端口。${C.reset}\n`);
    } else {
        console.error(`\n${C.red}❌ 服务器错误: ${err.message}${C.reset}\n`);
    }
    process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', function() {
    console.log(`\n\n${C.yellow}👋 CatChat CLI 代理已停止。再见喵～${C.reset}\n`);
    process.exit(0);
});
