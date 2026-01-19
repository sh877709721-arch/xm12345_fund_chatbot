# -*- coding:utf-8 -*-
"""
讯飞语音听写流式 WebAPI 客户端封装
接口文档: https://doc.xfyun.cn/rest_api/语音听写（流式版）.html
"""
import websocket
import datetime
import hashlib
import base64
import hmac
import json
import ssl
import time
import logging
from io import BytesIO
from typing import Optional, Callable
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import threading

from app.config.settings import settings


logger = logging.getLogger(__name__)


# 音频帧状态标识
STATUS_FIRST_FRAME = 0  # 第一帧标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧标识


class SpeechRecognitionError(Exception):
    """语音识别异常"""
    pass


class XfyunSpeechClient:
    """讯飞语音听写流式 WebAPI 客户端"""

    def __init__(
        self,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        """
        初始化讯飞语音识别客户端

        Args:
            app_id: 讯飞应用ID，默认从 settings.SPEECH_APP_ID 获取
            api_key: 讯飞API Key，默认从 settings.SPEECH_API_KEY 获取
            api_secret: 讯飞API Secret，默认从 settings.SPEECH_API_SECRET 获取
        """
        self.APPID = app_id or settings.SPEECH_APP_ID
        self.APIKey = api_key or settings.SPEECH_API_KEY
        self.APISecret = api_secret or settings.SPEECH_API_SECRET

        if not all([self.APPID, self.APIKey, self.APISecret]):
            raise SpeechRecognitionError(
                "讯飞语音识别配置不完整，请检查 SPEECH_APP_ID、SPEECH_API_KEY、SPEECH_API_SECRET"
            )

        # 公共参数
        self.common_args = {"app_id": self.APPID}
        # 业务参数
        self.business_args = {
            "domain": "iat",
            "language": "zh_cn",
            "accent": "mandarin",
            "vinfo": 1,
            "vad_eos": 10000
        }

    def create_url(self) -> str:
        """
        生成 WebSocket 连接 URL

        Returns:
            完整的 WebSocket 连接 URL
        """
        url = 'wss://ws-api.xfyun.cn/v2/iat'

        # 生成 RFC1123 格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接签名字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"

        # 使用 hmac-sha256 进行加密
        signature_sha = hmac.new(
            self.APISecret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        # 生成 authorization
        authorization_origin = 'api_key="%s", algorithm="%s", headers="%s", signature="%s"' % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha
        )
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 拼接鉴权参数
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }

        # 生成最终 URL
        url = url + '?' + urlencode(v)
        return url

    def recognize_from_file(
        self,
        audio_file: str,
        on_result: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> dict:
        """
        从音频文件识别语音

        Args:
            audio_file: 音频文件路径
            on_result: 结果回调函数，接收识别文本
            on_error: 错误回调函数，接收错误信息

        Returns:
            包含识别结果的字典: {"text": "识别的文本", "success": True/False}
        """
        result = {"text": "", "success": False, "error": None}

        def on_message(ws, message):
            nonlocal result
            try:
                data = json.loads(message)
                code = data.get("code")
                sid = data.get("sid")

                if code != 0:
                    error_msg = data.get("message", "未知错误")
                    print(f"[讯飞语音] sid:{sid} call error:{error_msg} code is:{code}")
                    result["error"] = f"code:{code}, message:{error_msg}"
                    if on_error:
                        on_error(error_msg)
                else:
                    ws_items = data.get("data", {}).get("result", {}).get("ws", [])
                    text = ""
                    for i in ws_items:
                        for w in i.get("cw", []):
                            text += w.get("w", "")

                    if text:
                        result["text"] += text
                        if on_result:
                            on_result(text)

            except Exception as e:
                print(f"[讯飞语音] 消息解析异常: {e}")
                result["error"] = str(e)

        def on_error(ws, error):
            nonlocal result
            print(f"[讯飞语音] WebSocket 错误: {error}")
            result["error"] = str(error)

        def on_close(ws, *args):
            if result["text"]:
                result["success"] = True
            print(f"[讯飞语音] 连接关闭，识别结果: {result['text']}")

        def on_open(ws):
            def send_audio():
                frame_size = 8000  # 每一帧的音频大小
                interval = 0.04  # 发送音频间隔(单位:s)
                status = STATUS_FIRST_FRAME

                try:
                    with open(audio_file, "rb") as fp:
                        while True:
                            buf = fp.read(frame_size)

                            # 文件结束
                            if not buf:
                                status = STATUS_LAST_FRAME

                            # 第一帧处理
                            if status == STATUS_FIRST_FRAME:
                                d = {
                                    "common": self.common_args,
                                    "business": self.business_args,
                                    "data": {
                                        "status": 0,
                                        "format": "audio/L16;rate=16000",
                                        "audio": str(base64.b64encode(buf), 'utf-8'),
                                        "encoding": "raw"
                                    }
                                }
                                ws.send(json.dumps(d))
                                status = STATUS_CONTINUE_FRAME

                            # 中间帧处理
                            elif status == STATUS_CONTINUE_FRAME:
                                d = {
                                    "data": {
                                        "status": 1,
                                        "format": "audio/L16;rate=16000",
                                        "audio": str(base64.b64encode(buf), 'utf-8'),
                                        "encoding": "raw"
                                    }
                                }
                                ws.send(json.dumps(d))

                            # 最后一帧处理
                            elif status == STATUS_LAST_FRAME:
                                d = {
                                    "data": {
                                        "status": 2,
                                        "format": "audio/L16;rate=16000",
                                        "audio": str(base64.b64encode(buf), 'utf-8'),
                                        "encoding": "raw"
                                    }
                                }
                                ws.send(json.dumps(d))
                                time.sleep(1)
                                break

                            time.sleep(interval)
                except Exception as e:
                    print(f"[讯飞语音] 发送音频异常: {e}")
                    result["error"] = str(e)
                finally:
                    ws.close()

            thread = threading.Thread(target=send_audio)
            thread.daemon = True
            thread.start()

        # 创建 WebSocket 连接
        ws_url = self.create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open

        # 运行 WebSocket（阻塞模式）
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        return result

    def recognize_from_bytes(
        self,
        audio_data: bytes,
        on_result: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> dict:
        """
        从字节流识别语音

        Args:
            audio_data: 音频字节流
            on_result: 结果回调函数，接收识别文本
            on_error: 错误回调函数，接收错误信息

        Returns:
            包含识别结果的字典: {"text": "识别的文本", "success": True/False}
        """
        result = {"text": "", "success": False, "error": None}

        def on_message(ws, message):
            nonlocal result
            try:
                data = json.loads(message)
                code = data.get("code")
                sid = data.get("sid")

                if code != 0:
                    error_msg = data.get("message", "未知错误")
                    print(f"[讯飞语音] sid:{sid} call error:{error_msg} code is:{code}")
                    result["error"] = f"code:{code}, message:{error_msg}"
                    if on_error:
                        on_error(error_msg)
                else:
                    ws_items = data.get("data", {}).get("result", {}).get("ws", [])
                    text = ""
                    for i in ws_items:
                        for w in i.get("cw", []):
                            text += w.get("w", "")

                    if text:
                        result["text"] += text
                        if on_result:
                            on_result(text)

            except Exception as e:
                print(f"[讯飞语音] 消息解析异常: {e}")
                result["error"] = str(e)

        def on_error(ws, error):
            nonlocal result
            print(f"[讯飞语音] WebSocket 错误: {error}")
            result["error"] = str(error)

        def on_close(ws, *args):
            if result["text"]:
                result["success"] = True
            print(f"[讯飞语音] 连接关闭，识别结果: {result['text']}")

        def on_open(ws):
            def send_audio():
                frame_size = 8000  # 每一帧的音频大小
                interval = 0.04  # 发送音频间隔(单位:s)
                status = STATUS_FIRST_FRAME
                offset = 0

                try:
                    audio_length = len(audio_data)

                    while offset < audio_length:
                        buf = audio_data[offset:offset + frame_size]
                        offset += len(buf)

                        # 文件结束
                        if offset >= audio_length:
                            status = STATUS_LAST_FRAME

                        # 第一帧处理
                        if status == STATUS_FIRST_FRAME:
                            d = {
                                "common": self.common_args,
                                "business": self.business_args,
                                "data": {
                                    "status": 0,
                                    "format": "audio/L16;rate=16000",
                                    "audio": str(base64.b64encode(buf), 'utf-8'),
                                    "encoding": "raw"
                                }
                            }
                            ws.send(json.dumps(d))
                            status = STATUS_CONTINUE_FRAME

                        # 中间帧处理
                        elif status == STATUS_CONTINUE_FRAME:
                            d = {
                                "data": {
                                    "status": 1,
                                    "format": "audio/L16;rate=16000",
                                    "audio": str(base64.b64encode(buf), 'utf-8'),
                                    "encoding": "raw"
                                }
                            }
                            ws.send(json.dumps(d))

                        # 最后一帧处理
                        elif status == STATUS_LAST_FRAME:
                            d = {
                                "data": {
                                    "status": 2,
                                    "format": "audio/L16;rate=16000",
                                    "audio": str(base64.b64encode(buf), 'utf-8'),
                                    "encoding": "raw"
                                }
                            }
                            ws.send(json.dumps(d))
                            time.sleep(1)
                            break

                        time.sleep(interval)
                except Exception as e:
                    print(f"[讯飞语音] 发送音频异常: {e}")
                    result["error"] = str(e)
                finally:
                    ws.close()

            thread = threading.Thread(target=send_audio)
            thread.daemon = True
            thread.start()

        # 创建 WebSocket 连接
        ws_url = self.create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open

        # 运行 WebSocket（阻塞模式）
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        return result


class StreamSpeechRecognizer:
    """流式语音识别器，用于 WebSocket 代理"""

    def __init__(self, client: XfyunSpeechClient, on_result: Callable, on_error: Optional[Callable] = None, on_close: Optional[Callable] = None, on_open: Optional[Callable] = None):
        """
        初始化流式识别器

        Args:
            client: 讯飞语音客户端
            on_result: 结果回调函数
            on_error: 错误回调函数
            on_close: 关闭回调函数
            on_open: 连接成功回调函数
        """
        self.client = client
        self.on_result = on_result
        self.on_error = on_error
        self.on_close = on_close
        self.on_open = on_open
        self.ws = None
        self.is_first_frame = True
        self.connected = False  # 连接状态标志

    def connect(self):
        """建立 WebSocket 连接"""
        ws_url = self.client.create_url()
        logger.info(f"[讯飞WS] 正在连接: {ws_url[:60]}...")

        def on_message(ws, message):
            try:
                data = json.loads(message)
                code = data.get("code")
                sid = data.get("sid")

                # 记录所有原始响应（前300字符）
                logger.info(f"[讯飞WS] 收到响应: {message[:300]}...")

                if code != 0:
                    error_msg = data.get("message", "未知错误")
                    logger.error(f"[讯飞WS] 错误响应: code={code}, message={error_msg}, sid={sid}")
                    if self.on_error:
                        self.on_error({"code": code, "message": error_msg, "sid": sid})
                else:
                    # 解析识别结果
                    result_data = data.get("data", {})
                    result = result_data.get("result", {})
                    status = result_data.get("status", 0)

                    # 空结果警告
                    if not result:
                        logger.warning(f"[讯飞WS] 空结果: status={status}, data={result_data}")

                    ws_items = result.get("ws", [])
                    text = ""
                    for item in ws_items:
                        for w in item.get("cw", []):
                            text += w.get("w", "")

                    if text:
                        logger.info(f"[讯飞WS] 识别结果: text='{text}', status={status}, is_final={status==2}")

                    if self.on_result:
                        self.on_result({
                            "text": text,
                            "status": status,  # 0: 首帧, 1: 中间, 2: 结束
                            "sid": sid,
                            "is_final": status == 2
                        })

            except Exception as e:
                logger.error(f"[讯飞WS] 消息解析异常: {e}, raw_message={message}")
                if self.on_error:
                    self.on_error({"error": str(e), "raw": message})

        def on_error_callback(ws, error):
            logger.error(f"[讯飞WS] WebSocket 错误: {error}")
            self.connected = False
            if self.on_error:
                self.on_error({"error": str(error)})

        def on_close_callback(ws, *args):
            logger.info(f"[讯飞WS] 连接已关闭: {args}")
            self.connected = False
            if self.on_close:
                self.on_close()

        def on_open_callback(ws):
            logger.info(f"[讯飞WS] 连接已建立")
            self.connected = True
            if self.on_open:
                self.on_open()

        # 创建 WebSocket 连接
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error_callback,
            on_close=on_close_callback,
            on_open=on_open_callback
        )

        return self.ws

    def send_audio(self, audio_data: str, is_last: bool = False):
        """
        发送音频数据

        Args:
            audio_data: base64 编码后的音频数据（字符串）
            is_last: 是否是最后一帧
        """
        if not self.ws:
            raise SpeechRecognitionError("WebSocket 连接未建立")

        if self.is_first_frame:
            # 第一帧：发送 common + business + data
            d = {
                "common": self.client.common_args,
                "business": self.client.business_args,
                "data": {
                    "status": 0,  # 首帧固定为 0
                    "format": "audio/L16;rate=16000",
                    "audio": audio_data,
                    "encoding": "raw"
                }
            }
            self.is_first_frame = False
            logger.info(f"[流式识别] 发送首帧，音频数据长度: {len(audio_data)} chars")
        else:
            # 后续帧：只发送 data
            d = {
                "data": {
                    "status": 2 if is_last else 1,
                    "format": "audio/L16;rate=16000",
                    "audio": audio_data,
                    "encoding": "raw"
                }
            }
            logger.debug(f"[流式识别] 发送中间帧，音频数据长度: {len(audio_data)} chars, is_last: {is_last}")

        self.ws.send(json.dumps(d))

    def close(self):
        """关闭连接"""
        if self.ws:
            self.ws.close()


# 创建全局客户端实例
def get_speech_client() -> XfyunSpeechClient:
    """获取语音识别客户端实例"""
    return XfyunSpeechClient()
