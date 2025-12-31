# 消息投票功能

这个模块提供了对助手消息进行投票评价的功能，支持好评、中评和差评三种评价方式。

## 组件结构

### 1. MessageActions 组件
位置：`src/components/ai-elements/message-actions.tsx`

显示投票按钮的UI组件，包含三个按钮：
- 👍 好评 (绿色)
- ➖ 中评 (黄色)
- 👎 差评 (红色)

**Props:**
```typescript
interface MessageActionsProps {
  messageId: number;                                    // 消息ID
  feedback?: 'good' | 'medium' | 'bad' | null;         // 当前投票状态
  onFeedbackChange?: (messageId: number, feedback: 'good' | 'medium' | 'bad' | null) => void; // 投票变化回调
  disabled?: boolean;                                   // 是否禁用
  className?: string;                                   // 自定义样式类
}
```

**自动状态加载:**
- 组件挂载时会自动获取该消息的投票状态
- 如果已提供 `feedback` 属性，则不会重复请求
- 通过 `onFeedbackChange` 回调更新父组件状态

### 2. useVote Hook
位置：`src/hooks/use-vote.ts`

处理投票逻辑的自定义Hook，提供投票状态管理和API调用。

**Hook返回值:**
```typescript
{
  toggleVote: (messageId: string, currentFeedback: string | null, newFeedback: string | null) => Promise<boolean>;
  getMessageVoteStatus: (messageId: string) => Promise<string | null>;
  loading: boolean;
}
```

### 3. MessageWithVoting 组件
位置：`src/components/ai-elements/message-with-voting.tsx`

完整消息组件，集成了投票功能。只有assistant角色的消息会显示投票按钮。

## 使用方法

### 基本用法

```tsx
import { MessageActions } from "@/components/ai-elements/message-actions";

function MyMessageComponent({ message }) {
  const [feedback, setFeedback] = useState(null);

  const handleFeedbackChange = (messageId, newFeedback) => {
    setFeedback(newFeedback);
  };

  if (message.role !== 'assistant') {
    // 用户消息，不显示投票
    return <div>{message.content}</div>;
  }

  return (
    <div>
      <p>{message.content}</p>
      <MessageActions
        messageId={message.id}
        feedback={feedback}
        onFeedbackChange={handleFeedbackChange}
      />
    </div>
  );
}
```

### 完整示例

```tsx
import { MessageWithVoting, VotingExample } from "@/components/ai-elements/message-with-voting";

// 使用完整组件
function ChatInterface() {
  return (
    <div>
      <MessageWithVoting
        message={{
          id: "msg_123",
          content: "这是助手的回答...",
          role: "assistant",
          created_at: new Date().toISOString()
        }}
      />
    </div>
  );
}

// 查看演示示例
function ExamplePage() {
  return <VotingExample />;
}
```

## API 集成

### 投票API调用

投票功能会自动调用以下API端点：

- `POST /v1/vote/message/toggle` - 切换投票状态
- `DELETE /v1/vote/message/{messageId}` - 取消投票
- `GET /v1/vote/message/{messageId}` - 获取投票状态

### 请求格式

```typescript
// 切换投票
POST /v1/vote/message/toggle
{
  "message_id": "msg_123",
  "vote_type": "good",  // "good" | "medium" | "bad"
  "comment": "可选的评论"
}
```

## 样式定制

### 默认样式
- 投票按钮在鼠标悬停时显示，平时透明度为0
- 投票状态用不同颜色区分
- 按钮大小为 32x32px

### 自定义样式
可以通过 `className` prop 自定义样式：

```tsx
<MessageActions
  messageId="msg_123"
  feedback={feedback}
  onFeedbackChange={handleFeedbackChange}
  className="custom-voting-style"
/>
```

## 注意事项

1. **只对assistant消息生效**: 用户消息不会显示投票按钮
2. **防止重复提交**: 组件有loading状态，防止重复点击
3. **类型安全**: 使用TypeScript确保类型安全
4. **错误处理**: 包含完整的错误处理和用户提示
5. **响应式设计**: 支持移动端和桌面端显示