/**
 * 测试 GraphRAG Local Search 流式 API 的 Node.js 客户端
 */

const https = require('https');
const http = require('http');

function testLocalSearchStream() {
    const url = 'http://127.0.0.1:8000/v1/graphrag/local-search/stream';
    const payload = {
        query: '怎么交医保',
        community_level: 2,
        response_type: 'Multiple Paragraphs'
    };

    const postData = JSON.stringify(payload);

    const options = {
        hostname: '127.0.0.1',
        port: 8000,
        path: '/v1/graphrag/local-search/stream',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData),
            'Accept': 'text/plain',
            'Cache-Control': 'no-cache'
        }
    };

    console.log('🚀 开始测试 GraphRAG Local Search 流式 API');
    console.log(`📝 查询: ${payload.query}`);
    console.log(`🌐 URL: ${url}`);
    console.log('-'.repeat(50));

    const req = http.request(options, (res) => {
        console.log(`✅ 状态码: ${res.statusCode}`);
        console.log('-'.repeat(50));

        let buffer = '';

        res.on('data', (chunk) => {
            buffer += chunk.toString();

            // 处理完整的行
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 保留最后一个不完整的行

            for (const line of lines) {
                if (line.trim() && line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6)); // 移除 "data: "
                        const msgType = data.type;
                        const content = data.content || '';

                        switch (msgType) {
                            case 'start':
                                console.log(`🔍 开始搜索: ${data.query}`);
                                console.log(`📊 搜索类型: ${data.search_type}`);
                                break;
                            case 'chunk':
                                console.log(`📦 ${content}`);
                                break;
                            case 'done':
                                console.log('✅ 搜索完成!');
                                break;
                            case 'error':
                                console.log(`❌ 错误: ${content}`);
                                break;
                        }
                    } catch (error) {
                        console.log(`⚠️ JSON 解析错误: ${error.message}`);
                    }
                }
            }
        });

        res.on('end', () => {
            if (buffer.trim()) {
                console.log(`📝 剩余数据: ${buffer}`);
            }
            console.log('-'.repeat(50));
            console.log('🎉 流式测试完成!');
        });

        res.on('error', (error) => {
            console.error(`❌ 响应错误: ${error.message}`);
        });
    });

    req.on('error', (error) => {
        console.error(`❌ 请求错误: ${error.message}`);
    });

    // 发送请求体
    req.write(postData);
    req.end();
}

// 使用 fetch 的现代版本 (Node.js 18+)
async function testLocalSearchStreamFetch() {
    const url = 'http://127.0.0.1:8000/v1/graphrag/local-search/stream';
    const payload = {
        query: '怎么交医保',
        community_level: 2,
        response_type: 'Multiple Paragraphs'
    };

    console.log('🚀 使用 fetch API 测试...');

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/plain',
                'Cache-Control': 'no-cache'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        console.log('✅ 连接成功，开始接收流式数据...');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // 处理完整的行
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.trim() && line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        const msgType = data.type;
                        const content = data.content || '';

                        switch (msgType) {
                            case 'start':
                                console.log(`🔍 开始搜索: ${data.query}`);
                                break;
                            case 'chunk':
                                console.log(`📦 ${content}`);
                                break;
                            case 'done':
                                console.log('✅ 搜索完成!');
                                return; // 完成后退出
                            case 'error':
                                console.log(`❌ 错误: ${content}`);
                                return;
                        }
                    } catch (error) {
                        console.log(`⚠️ JSON 解析错误: ${error.message}`);
                    }
                }
            }
        }

    } catch (error) {
        console.error(`❌ 请求失败: ${error.message}`);
    }
}

if (require.main === module) {
    console.log('选择测试方式:');
    console.log('1. 原生 http 模块');
    console.log('2. fetch API (Node.js 18+)');

    const choice = process.argv[2] || '1';

    if (choice === '2') {
        testLocalSearchStreamFetch();
    } else {
        testLocalSearchStream();
    }
}