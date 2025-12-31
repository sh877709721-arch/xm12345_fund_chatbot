# -*- coding:utf-8 -*-
"""
讯飞语音识别路由接口
提供语音转文字的 HTTP 接口和 WebSocket 流式接口
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import logging
import tempfile
import os
import json
import base64
import ssl
import asyncio
import threading

from app.config.speech_client import get_speech_client, SpeechRecognitionError, StreamSpeechRecognizer
from app.schema.base import BaseResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/speech")


class SpeechRecognitionRequest(BaseModel):
    """语音识别请求参数"""
    language: Optional[str] = "zh_cn"  # 识别语言
    accent: Optional[str] = "mandarin"  # 方言类型
    format: Optional[str] = "audio/L16;rate=16000"  # 音频格式


class SpeechRecognitionResponse(BaseResponse):
    """语音识别响应"""
    text: Optional[str] = None  # 识别结果文本
    confidence: Optional[float] = None  # 置信度（如支持）


@router.post("/recognize", response_model=SpeechRecognitionResponse)
async def recognize_speech(
    audio_file: UploadFile = File(..., description="音频文件，支持 wav、pcm 等格式")
):
    """
    语音识别接口 - 将音频文件转换为文字

    ## 功能说明
    上传音频文件，返回识别出的文字内容。

    ## 音频格式要求
    - 编码格式: PCM
    - 采样率: 16000Hz
    - 位深: 16bit
    - 声道: 单声道
    - 文件格式: .wav, .pcm

    ## 请求方式
    - Content-Type: multipart/form-data
    - 参数名: audio_file

    ## 返回示例
    ```json
    {
        "code": 200,
        "message": "识别成功",
        "data": {
            "text": "你好，世界"
        }
    }
    ```

    ## 错误码
    - 400: 请求参数错误
    - 500: 语音识别服务异常
    """
    # 验证文件类型
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="未提供音频文件")

    # 检查文件扩展名
    allowed_extensions = {'.wav', '.pcm', '.mp3', '.ogg', '.flac'}
    file_ext = os.path.splitext(audio_file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式: {file_ext}，支持的格式: {', '.join(allowed_extensions)}"
        )

    # 保存临时文件
    temp_file_path = None
    try:
        # 读取音频内容
        content = await audio_file.read()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        logger.info(f"[语音识别] 接收到音频文件: {audio_file.filename}, 大小: {len(content)} bytes")

        # 调用语音识别客户端
        result = get_speech_client().recognize_from_file(temp_file_path)

        if result["success"]:
            logger.info(f"[语音识别] 识别成功: {result['text']}")
            return SpeechRecognitionResponse(
                code=200,
                message="识别成功",
                data={"text": result["text"]}
            )
        else:
            error_msg = result.get("error", "未知错误")
            logger.error(f"[语音识别] 识别失败: {error_msg}")
            return SpeechRecognitionResponse(
                code=500,
                message=f"识别失败: {error_msg}",
                data=None
            )

    except SpeechRecognitionError as e:
        logger.error(f"[语音识别] 配置错误: {e}")
        return SpeechRecognitionResponse(
            code=500,
            message=f"语音识别服务配置错误: {str(e)}",
            data=None
        )
    except Exception as e:
        logger.exception(f"[语音识别] 处理异常: {e}")
        return SpeechRecognitionResponse(
            code=500,
            message=f"处理异常: {str(e)}",
            data=None
        )
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"[语音识别] 已清理临时文件: {temp_file_path}")
            except Exception as e:
                logger.warning(f"[语音识别] 清理临时文件失败: {e}")


@router.get("/health")
async def health_check():
    """
    健康检查接口 - 检查语音识别服务是否可用

    ## 返回示例
    ```json
    {
        "status": "ok",
        "message": "语音识别服务运行正常"
    }
    ```
    """
    try:
        # 尝试创建客户端，验证配置是否正确
        get_speech_client()
        return {
            "status": "ok",
            "message": "语音识别服务运行正常",
            "configured": True
        }
    except SpeechRecognitionError as e:
        return {
            "status": "error",
            "message": f"语音识别服务配置错误: {str(e)}",
            "configured": False
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"语音识别服务异常: {str(e)}",
            "configured": False
        }


@router.get("/config/info")
async def get_config_info():
    """
    获取配置信息接口 - 返回当前语音识别配置状态（不暴露敏感信息）

    ## 返回示例
    ```json
    {
        "app_id": "xxx****",
        "configured": true,
        "language": "zh_cn",
        "accent": "mandarin"
    }
    ```
    """
    try:
        client = get_speech_client()
        app_id = client.APPID
        # 脱敏处理
        masked_app_id = f"{app_id[:4]}****" if app_id and len(app_id) > 4 else "****"

        return {
            "app_id": masked_app_id,
            "configured": bool(client.APPID and client.APIKey and client.APISecret),
            "language": client.business_args.get("language"),
            "accent": client.business_args.get("accent"),
            "domain": client.business_args.get("domain")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream")
async def stream_recognize(websocket: WebSocket):
    """
    流式语音识别 WebSocket 接口

    ## 连接地址
    ws://localhost:8000/v1/speech/stream

    ## 消息格式

    客户端发送消息格式:
    ```json
    {
        "type": "audio",      // 消息类型: audio(音频数据), close(结束)
        "data": "base64...",  // base64 编码的音频数据
        "is_last": false      // 是否是最后一帧
    }
    ```

    服务端返回消息格式:
    ```json
    {
        "type": "result",     // 消息类型: result(识别结果), error(错误)
        "text": "识别的文字",  // 识别结果文本
        "is_final": false,    // 是否是最终结果
        "status": 1           // 0: 首帧, 1: 中间, 2: 结束
    }
    ```

    ## 使用示例

    ```javascript
    const ws = new WebSocket('ws://localhost:8000/v1/speech/stream');

    ws.onopen = () => {
        // 发送音频数据
        ws.send(JSON.stringify({
            type: 'audio',
            data: base64AudioData,
            is_last: false
        }));
    };

    ws.onmessage = (event) => {
        const response = JSON.parse(event.data);
        if (response.type === 'result') {
            console.log('识别结果:', response.text);
            if (response.is_final) {
                console.log('识别完成');
            }
        }
    };

    // 结束识别
    ws.send(JSON.stringify({ type: 'close' }));
    ```
    """
    await websocket.accept()
    logger.info("[流式语音] WebSocket 连接已建立")

    client = get_speech_client()
    recognizer = None
    xfyun_ws = None
    xfyun_thread = None

    def on_result(result: dict):
        """讯飞返回识别结果时回调"""
        try:
            # 异步发送结果到客户端，使用预先捕获的 loop
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({
                    "type": "result",
                    "text": result.get("text", ""),
                    "is_final": result.get("is_final", False),
                    "status": result.get("status", 0),
                    "sid": result.get("sid", "")
                }),
                loop
            )
            logger.debug(f"[流式语音] 识别结果: {result.get('text', '')}")
        except Exception as e:
            logger.error(f"[流式语音] 发送结果失败: {e}")

    def on_error(error: dict):
        """讯飞返回错误时回调"""
        try:
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({
                    "type": "error",
                    "code": error.get("code", 500),
                    "message": error.get("message", str(error))
                }),
                loop
            )
        except Exception as e:
            logger.error(f"[流式语音] 发送错误失败: {e}")

    def on_close():
        """讯飞连接关闭时回调"""
        logger.info("[流式语音] 讯飞连接已关闭")

    # 用于等待讯飞 WebSocket 连接建立
    xfyun_connected = threading.Event()

    def on_xfyun_open():
        """讯飞连接成功时回调"""
        logger.info("[流式语音] 讯飞 WebSocket 连接成功")
        xfyun_connected.set()

    try:
        # 获取当前运行的事件循环（必须在创建线程前获取）
        loop = asyncio.get_running_loop()

        # 创建流式识别器（传入 on_open 回调）
        recognizer = StreamSpeechRecognizer(client, on_result, on_error, on_close, on_xfyun_open)
        xfyun_ws = recognizer.connect()

        # 在新线程中运行讯飞 WebSocket
        def run_xfyun_ws():
            xfyun_ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        xfyun_thread = threading.Thread(target=run_xfyun_ws, daemon=True)
        xfyun_thread.start()

        # 等待讯飞 WebSocket 连接建立（最多等待 5 秒）
        await asyncio.wait_for(
            asyncio.to_thread(xfyun_connected.wait),
            timeout=5.0
        )

        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "message": "流式识别连接已建立，请发送音频数据"
        })

        # 接收客户端消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "audio":
                # 处理音频数据
                audio_data = message.get("data", "")
                is_last = message.get("is_last", False)

                if audio_data:
                    recognizer.send_audio(audio_data, is_last)

                if is_last:
                    logger.info("[流式语音] 客户端发送了最后一帧")

            elif msg_type == "close":
                # 客户端请求关闭
                logger.info("[流式语音] 客户端请求关闭连接")
                break

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"未知的消息类型: {msg_type}"
                })

    except asyncio.TimeoutError:
        logger.error("[流式语音] 讯飞 WebSocket 连接超时")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "讯飞语音服务连接超时"
            })
        except:
            pass
    except WebSocketDisconnect:
        logger.info("[流式语音] 客户端断开连接")
    except SpeechRecognitionError as e:
        logger.error(f"[流式语音] 配置错误: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"语音识别服务配置错误: {str(e)}"
            })
        except:
            pass
    except Exception as e:
        logger.exception(f"[流式语音] 处理异常: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"处理异常: {str(e)}"
            })
        except:
            pass
    finally:
        # 清理资源
        if recognizer:
            recognizer.close()
        logger.info("[流式语音] 连接已关闭")
