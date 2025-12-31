# 讯飞语音识别接口使用手册

## 概述

本系统集成了讯飞语音听写流式 WebAPI，提供语音转文字服务，支持：
- **HTTP 接口**: 上传完整音频文件进行识别
- **WebSocket 接口**: 实时流式语音识别，边录边转

**接口文档**: https://doc.xfyun.cn/rest_api/语音听写（流式版）.html

---

## 快速开始

### 1. 环境配置

在项目根目录的 `.env` 文件中添加讯飞语音识别配置：

```env
# 讯飞语音识别配置
SPEECH_APP_ID=your_app_id_here
SPEECH_API_KEY=your_api_key_here
SPEECH_API_SECRET=your_api_secret_here
```

### 2. 获取讯飞 API 密钥

1. 访问 [讯飞开放平台](https://www.xfyun.cn/)
2. 注册/登录账号
3. 进入控制台 → 创建应用 → 添加 **语音听写（流式版）** 服务
4. 在应用详情页获取：
   - `APPID`
   - `API Secret`
   - `API Key`

---

## API 接口说明

### 基础路径

```
http://your-domain:8000/v1/speech
```

---

### 1. 语音识别接口

**接口地址**: `POST /v1/speech/recognize`

**请求方式**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 是否必填 | 说明 |
|--------|------|----------|------|
| audio_file | File | 是 | 音频文件 |

**音频格式要求**:

| 属性 | 要求 |
|------|------|
| 编码格式 | PCM |
| 采样率 | 16000Hz |
| 位深 | 16bit |
| 声道 | 单声道 |
| 支持格式 | .wav, .pcm, .mp3, .ogg, .flac |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "识别成功",
    "data": {
        "text": "你好，世界"
    }
}
```

**失败响应示例**:

```json
{
    "code": 500,
    "message": "识别失败: 错误详情",
    "data": null
}
```

---

### 2. 健康检查接口

**接口地址**: `GET /v1/speech/health`

**响应示例**:

```json
{
    "status": "ok",
    "message": "语音识别服务运行正常",
    "configured": true
}
```

---

### 3. 配置信息接口

**接口地址**: `GET /v1/speech/config/info`

**响应示例**:

```json
{
    "app_id": "xxxx****",
    "configured": true,
    "language": "zh_cn",
    "accent": "mandarin",
    "domain": "iat"
}
```

---

### 4. 流式语音识别接口（WebSocket）

**接口地址**: `ws://localhost:8000/v1/speech/stream`

**适用场景**: 实时语音识别，如录音转写、语音输入等

#### 客户端发送消息格式

```json
{
    "type": "audio",      // 消息类型: audio(音频数据), close(结束)
    "data": "base64...",  // base64 编码的音频数据
    "is_last": false      // 是否是最后一帧
}
```

#### 服务端返回消息格式

```json
{
    "type": "result",     // 消息类型: result(识别结果), error(错误), connected(连接成功)
    "text": "识别的文字",  // 识别结果文本
    "is_final": false,    // 是否是最终结果
    "status": 1,          // 0: 首帧, 1: 中间, 2: 结束
    "sid": "iatxxxxxx"    // 会话ID
}
```

#### JavaScript 流式识别示例

```javascript
const ws = new WebSocket('ws://localhost:8000/v1/speech/stream');

ws.onopen = () => {
    console.log('WebSocket 连接已建立');
};

ws.onmessage = (event) => {
    const response = JSON.parse(event.data);

    switch (response.type) {
        case 'connected':
            console.log(response.message);
            break;
        case 'result':
            console.log('识别结果:', response.text);
            if (response.is_final) {
                console.log('识别完成');
            }
            break;
        case 'error':
            console.error('识别错误:', response.message);
            break;
    }
};

// 发送音频数据
function sendAudioData(base64AudioData) {
    ws.send(JSON.stringify({
        type: 'audio',
        data: base64AudioData,
        is_last: false
    }));
}

// 结束识别
function endRecognition() {
    ws.send(JSON.stringify({
        type: 'audio',
        data: '',  // 空数据
        is_last: true
    }));
}

// 或者直接关闭连接
ws.send(JSON.stringify({ type: 'close' }));
```

#### 浏览器录音 + 流式识别示例

```javascript
// 1. 获取麦克风权限
navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const base64Audio = await blobToBase64(audioBlob);

            // 发送到识别服务
            ws.send(JSON.stringify({
                type: 'audio',
                data: base64Audio,
                is_last: true
            }));
        };

        // 开始录音
        mediaRecorder.start();

        // 5秒后停止
        setTimeout(() => mediaRecorder.stop(), 5000);
    });

function blobToBase64(blob) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(blob);
    });
}
```

#### Python 流式识别示例

```python
import asyncio
import websockets
import json
import base64

async def stream_recognize(audio_file_path):
    uri = "ws://localhost:8000/v1/speech/stream"

    async with websockets.connect(uri) as websocket:
        # 等待连接确认
        response = await websocket.recv()
        print(f"服务端: {response}")

        # 读取音频文件并分块发送
        chunk_size = 3200  # 每次发送的字节数
        with open(audio_file_path, 'rb') as f:
            chunk_index = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    # 发送最后一帧
                    await websocket.send(json.dumps({
                        "type": "audio",
                        "data": "",
                        "is_last": True
                    }))
                    break

                # 发送音频数据
                base64_data = base64.b64encode(chunk).decode('utf-8')
                await websocket.send(json.dumps({
                    "type": "audio",
                    "data": base64_data,
                    "is_last": False
                }))

                # 接收识别结果
                try:
                    result = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    response = json.loads(result)
                    if response.get('type') == 'result':
                        print(f"识别: {response.get('text', '')}")
                except asyncio.TimeoutError:
                    pass

                chunk_index += 1
                # 模拟实时发送，间隔40ms
                await asyncio.sleep(0.04)

        # 接收最终结果
        while True:
            result = await websocket.recv()
            response = json.loads(result)
            if response.get('type') == 'result':
                print(f"最终: {response.get('text', '')}")
                if response.get('is_final'):
                    break

# 运行
asyncio.run(stream_recognize("audio.wav"))
```

---

## 调用示例

### cURL 示例

```bash
curl -X POST "http://localhost:8000/v1/speech/recognize" \
  -H "accept: application/json" \
  -F "audio_file=@/path/to/audio.wav"
```

### Python 示例

```python
import requests

url = "http://localhost:8000/v1/speech/recognize"
files = {"audio_file": open("audio.wav", "rb")}

response = requests.post(url, files=files)
print(response.json())
# 输出: {'code': 200, 'message': '识别成功', 'data': {'text': '识别的文字'}}
```

### JavaScript/TypeScript 示例

```typescript
async function recognizeAudio(audioFile: File) {
    const formData = new FormData();
    formData.append('audio_file', audioFile);

    const response = await fetch('http://localhost:8000/v1/speech/recognize', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    console.log(result.data.text);
}

// 使用示例
const fileInput = document.querySelector('#audioInput');
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    recognizeAudio(file);
});
```

### Axios 示例

```javascript
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

async function recognizeAudio(filePath) {
    const form = new FormData();
    form.append('audio_file', fs.createReadStream(filePath));

    const response = await axios.post(
        'http://localhost:8000/v1/speech/recognize',
        form,
        { headers: form.getHeaders() }
    );

    console.log(response.data);
}

recognizeAudio('./audio.wav');
```

---

## 音频处理建议

### 推荐的音频参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 采样率 | 16000Hz | 讯飞推荐采样率 |
| 编码 | PCM | 无损编码 |
| 位深 | 16bit | 标准位深 |
| 声道 | 1 (单声道) | 语音识别标准 |

### FFmpeg 转换命令示例

```bash
# 转换为讯飞推荐格式
ffmpeg -i input.mp3 -f s16le -ar 16000 -ac 1 -acodec pcm_s16le output.pcm

# 转换 WAV 格式
ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav

# 从录音设备直接录制（Linux）
ffmpeg -f alsa -i default -f s16le -ar 16000 -ac 1 output.pcm
```

---

## 错误码说明

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 识别成功 |
| 400 | 请求参数错误（文件格式不支持、未提供文件等） |
| 500 | 语音识别服务异常 |

**讯飞错误码参考**: https://www.xfyun.cn/document/error-code

---

## 目录结构

```
ai_app/
├── app/
│   ├── config/
│   │   ├── settings.py          # 环境变量配置
│   │   └── speech_client.py     # 讯飞语音客户端封装
│   └── router/
│       └── speech.py            # 语音识别路由接口
├── main.py                      # FastAPI 主程序（已注册路由）
└── .env                         # 环境变量配置文件
```

---

## 常见问题

### 1. 配置不完整错误

**错误信息**: `讯飞语音识别配置不完整，请检查 SPEECH_APP_ID、SPEECH_API_KEY、SPEECH_API_SECRET`

**解决方案**: 检查 `.env` 文件中三个配置项是否正确填写。

### 2. 音频格式不支持

**错误信息**: `不支持的音频格式: xxx`

**解决方案**: 使用 FFmpeg 将音频转换为推荐格式。

### 3. 识别结果为空

**可能原因**:
- 音频文件无声音内容
- 音频质量过低
- 采样率不匹配

**解决方案**: 确保音频符合格式要求。

---

## 进阶配置

### 修改识别语言

编辑 [app/config/speech_client.py](app/config/speech_client.py#L39) 中的 `business_args`：

```python
self.business_args = {
    "domain": "iat",
    "language": "zh_cn",    # 语言：zh_cn(中文)、en_us(英文)等
    "accent": "mandarin",   # 方言：mandarin(普通话)、cantonese(粤语)等
    "vinfo": 1,
    "vad_eos": 10000
}
```

### 启用热词

1. 登录讯飞开放平台
2. 控制台 → 我的应用 → 语音听写（流式版）→ 服务管理 → 个性化热词
3. 设置热词（识别时会增加热词权重）

---

## 许可与参考

- 讯飞开放平台: https://www.xfyun.cn/
- 语音听写 API 文档: https://doc.xfyun.cn/rest_api/语音听写（流式版）.html
- 技术论坛: http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=38947
