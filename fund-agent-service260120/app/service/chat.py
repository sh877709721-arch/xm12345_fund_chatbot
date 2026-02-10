from app.model.message import Message,MessageRead
from app.model.chat import Chat, ChatStatusEnum
from app.model.message_context import ChatContext, ContextType,ChatContextRead
from app.config.database import get_db, SessionLocal
from typing import List, Optional
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from qwen_agent.llm.schema import Message as QwenMessage
import json
import logging

import time
import random
import string
def get_new_chat_instance(user_id: str, db: Session = Depends(get_db)) -> Chat:
    try:
        if not user_id:
            timestamp = int(time.time() * 1000)  # 毫秒级时间戳
            random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user_id = f"guest-{random_str}-{timestamp}"
        chat = Chat(user_id=user_id, status=ChatStatusEnum.active)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat
    except Exception as e:
        db.rollback()
        raise e


def append_chat_message(chat_id: str, 
                        message: QwenMessage,
                        db: Session = Depends(get_db),
                        meta_data:Optional[dict] = {"client":"web"} ,
                        ):
    try:
        message = Message(chat_id=chat_id, 
                          role=message.role, 
                          content=message.content,
                          metadata_=meta_data
                          )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    except Exception as e:
        db.rollback()
        raise e

def update_chat_message(chat_id: str, message_id: str, content: str, db: Session = Depends(get_db)):
    try:
        # 先查询消息是否存在
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError(f"Message with id {message_id} not found in chat {chat_id}")

        # 更新消息内容
        message.set_content(content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    except ValueError:
        # 重新抛出验证错误，不需要回滚（没有修改数据库）
        raise
    except Exception as e:
        db.rollback()
        raise e

def update_chat_message_background(chat_id: str, message_id: str, content: str):
    """
    后台任务版本的消息更新 - 自管理数据库连接

    专门用于 FastAPI BackgroundTask，在后台执行消息内容更新

    Args:
        chat_id: 聊天ID
        message_id: 消息ID
        content: 消息内容
    """
    db = SessionLocal()
    try:
        # 先查询消息是否存在
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            logging.error(f"Background task: Message {message_id} not found in chat {chat_id}")
            return

        # 更新消息内容
        message.set_content(content)
        db.add(message)
        db.commit()
        # logging.info(f"Background task: Successfully updated message {message_id} in chat {chat_id}")

    except ValueError as e:
        # 验证错误，记录但不回滚（没有修改数据库）
        logging.error(f"Background task: Validation error for message {message_id}: {str(e)}")
    except Exception as e:
        # 数据库错误，需要回滚
        try:
            db.rollback()
            logging.error(f"Background task: Database error for message {message_id}, rolled back: {str(e)}")
        except Exception as rollback_error:
            logging.error(f"Background task: Failed to rollback for message {message_id}: {str(rollback_error)}")
    finally:
        # 确保数据库连接被关闭
        try:
            db.close()
        except Exception as close_error:
            logging.error(f"Background task: Failed to close database connection: {str(close_error)}")

def get_chat_messages(chat_id: str, db: Session = Depends(get_db)) -> List[MessageRead]:
    """
        获取聊天记录
        :param chat_id: 聊天ID
        :param db: 数据库连接
        :return: 聊天记录
    """
    result = db.execute(select(Message).where(Message.chat_id == chat_id).order_by(Message.id.asc()))
    messages = [MessageRead.model_validate(msg) for msg in result.scalars().all()]

    return  messages


def get_recent_similary_qa(chat_id: str, db: Session = Depends(get_db)):
    """
        获取最近一条相似QA
        :param chat_id: 聊天ID
        :param db: 数据库连接
        :return: 聊天记录
    """
    result = db.execute(select(ChatContext).where(ChatContext.chat_id == chat_id,
                                                  ChatContext.context_type == ContextType.question).order_by(ChatContext.id.desc()).limit(1))
    
    all_qa = result.scalars().all()
    res_qa = []
    if all_qa:
        for first in all_qa:
            if first:
                qa_pair =  ChatContextRead.model_validate(first)
                context_str = qa_pair.context  # 获取context字段
                if context_str:
                    try:
                        # 解析JSON字符串为Python对象
                        qa_list = json.loads(context_str)
                        res_qa.extend([
                            {"id":qa_item["id"],"question":qa_item["question"]} 
                            for qa_item in qa_list
                            ])
                    except json.JSONDecodeError:
                        # 如果解析失败，返回空列表
                        logging.info(f"qa 结果解析失败")
        return res_qa
                
    return [
        {
            "id": 2557,
            "question": "我打算在本市购买预售一手房，提取公积金抵首付的材料是什么？"
        },
        {
            "id": 1872,
            "question": "我的子女/父母在本市购房，我办理购房代际互助提取公积金的材料是什么？"
        },
        {
            "id": 2151,
            "question": "我是单位经办，想了解单位公积金账户如何开户？"
        }
    ]



def save_observation_message(chat_id: str, chunk: str, db: Session = Depends(get_db)):
    """
        保存观察消息
        :param chat_id: 聊天ID
        :param message: 观察消息
        :param db: 数据库连接
        :return: None

        ReAct 框架返回的结果如下
        obs_chunk  = {
            "id": chunk_id,
            "object": "chat.completion.observation",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": observation_text},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(obs_chunk, ensure_ascii=False)}\n\n"
    """
    try:
        if chunk.startswith("data: "):
            json_str = chunk[5:].strip()
            data = json.loads(json_str)
            # 检查object字段是否为chat.completion.observation
            if data.get("object") == "chat.completion.observation":
                # 提取content内容
                content = ""
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")

                if content:  # 只有当有实际内容时才保存
                    context = ChatContext(
                        chat_id=chat_id,
                        context=content,
                        context_type=ContextType.observation
                    )
                    db.add(context)
                    db.commit()
                    db.refresh(context)
                    return context
    except json.JSONDecodeError as e:
        # 处理解码错误 - 不需要回滚，因为没有数据库操作
        # 可以记录日志但忽略错误，因为观察消息解析失败不应影响主流程
        print(f"JSON decode error in observation message: {e}")
        pass
    except Exception as e:
        # 处理其他异常 - 需要回滚可能的数据库操作
        try:
            db.rollback()
        except:
            pass  # 如果连接已关闭，忽略回滚错误
        pass

    return None


def save_observation_message_background(chat_id: str, 
                                        assistant_message_id:int,
                                        chunk: str, 
                                        context_type:ContextType,
                                        ):
    """
    🔧 **后台任务版本的观察消息保存**

    专门用于 FastAPI BackgroundTask，在后台异步保存观察消息

    Args:
        chat_id: 聊天ID
        chunk: 观察消息数据块
    """
    from app.config.database import SessionLocal

    #logging.info(f"Background task: save_observation_message_background for {chunk}")

    db = SessionLocal()
    try:
        if chunk.startswith("data: "):
            json_str = chunk[5:].strip()
            data = json.loads(json_str)
            # 检查object字段是否为chat.completion.observation
            if data.get("object") == "chat.completion.observation":
                # 提取content内容
                content = ""
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")

                if content:  # 只有当有实际内容时才保存
                    context = ChatContext(
                        chat_id=chat_id,
                        message_id = assistant_message_id,
                        context=content,
                        context_type=context_type #ContextType.observation
                    )
                    db.add(context)
                    db.commit()
                    #logging.info(f"Background task: Successfully saved observation message for chat {chat_id}")
            if data.get("object") == "chat.completion.question":
                # 提取content内容
                content = ""
                choices = data.get("content", [])                
                if choices and len(choices) > 0:
                    content = choices

                if content:  # 只有当有实际内容时才保存
                    context = ChatContext(
                        chat_id=chat_id,
                        message_id = assistant_message_id,
                        context=json.dumps(content, ensure_ascii=False),
                        context_type=context_type #ContextType.observation
                    )
                    db.add(context)
                    db.commit()
                    #logging.info(f"Background task: Successfully saved observation message for chat {chat_id}")

    except json.JSONDecodeError as e:
        # 处理解码错误 - 不需要回滚，因为没有数据库操作
        logging.warning(f"Background task: JSON decode error in observation message: {e}")
    except Exception as e:
        # 处理其他异常 - 需要回滚可能的数据库操作
        try:
            db.rollback()
            logging.error(f"Background task: Database error for observation message in chat {chat_id}, rolled back: {str(e)}")
        except Exception as rollback_error:
            logging.error(f"Background task: Failed to rollback for observation message in chat {chat_id}: {str(rollback_error)}")
    finally:
        # 确保数据库连接被关闭
        try:
            db.close()
        except Exception as close_error:
            logging.error(f"Background task: Failed to close database connection for observation message: {str(close_error)}")





def get_observation_message_context(
        message_id:int,
        db: Session = Depends(get_db)):
    result = db.execute(select(ChatContext).where(ChatContext.message_id == message_id,
                                                  ChatContext.context_type == ContextType.observation))
    
    first = result.scalars().first()
    row = ChatContextRead.model_validate(first)
    # "[文件](doc_1709)"  key值其实是"[文件](refer_id)"
    try:
        context = json.loads(row.context)
    except:
        logging.error('JSON解析错误')
        context = row.context
    return context
