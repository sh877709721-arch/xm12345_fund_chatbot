# Source引用功能

## 功能概述

Source引用功能允许AI助手在回答问题时显示信息来源，用户可以点击source标签查看详细的引用信息，包括链接、描述和内容片段。

## 组件结构

### 1. Source 类型定义

```typescript
export type Source = {
  id?: string;
  title: string;
  url?: string;
  description?: string;
  snippet?: string;
};
```

### 2. 主要组件

#### SourceReference
- 单个source引用的显示组件
- 以Badge形式显示，点击后弹出详情弹窗
- 支持显示标题、链接、描述和内容片段

#### SourceList
- 多个source引用的容器组件
- 支持水平排列多个source标签
- 自动处理空状态

## 使用方法

### 1. 在Message组件中使用

```typescript
<Message
  from="assistant"
  messageId={1}
  sources={message.sources}
>
  <MessageContent isUser={false}>
    {message.content}
  </MessageContent>
</Message>
```

### 2. 后端数据格式

后端在流式响应中应该发送以下格式的数据：

```json
{
  "object": "chat.completion.sources",
  "sources": [
    {
      "id": "1",
      "title": "文档标题",
      "url": "https://example.com",
      "description": "文档描述",
      "snippet": "相关内容片段"
    }
  ]
}
```

## 样式特点

- **蓝色标签设计**：采用蓝色背景，符合引用的视觉特征
- **弹窗交互**：点击标签显示详细信息，包含外部链接
- **响应式布局**：支持多个source的水平排列
- **无障碍设计**：包含适当的图标和颜色对比

## 交互流程

1. AI助手返回包含sources的消息
2. 在消息底部显示source标签列表
3. 用户点击任意source标签
4. 弹出详情对话框，显示完整的source信息
5. 用户可以点击外部链接访问原始文档

## 技术实现

- 使用Radix UI Dialog组件实现弹窗功能
- 使用Tailwind CSS进行样式设计
- 支持TypeScript类型安全
- 兼容现有的消息流处理机制