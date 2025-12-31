# 投票功能集成文档

## 概述

本项目已成功集成基于后端 API 的投票功能，替换了原有的简单前端反馈系统。新的投票系统支持与后端数据库的完整交互，包括创建、更新、删除和统计投票。

## 功能特性

### 支持的投票类型
- **好 (good)** - 使用 ThumbsUp 图标，绿色显示
- **中 (average)** - 使用 Minus 图标，黄色显示
- **差 (poor)** - 使用 ThumbsDown 图标，红色显示

### 核心功能
- ✅ 投票创建和更新
- ✅ 投票取消
- ✅ 投票统计
- ✅ 用户投票记录
- ✅ 错误处理和用户反馈
- ✅ 响应式 UI 更新

## 文件结构

```
src/
├── types/
│   └── vote.ts                    # 投票相关类型定义
├── services/
│   └── vote-api.ts               # 投票 API 服务
├── hooks/
│   ├── use-vote.ts               # 投票功能自定义 Hook
│   └── use-qwen-chat.ts          # 聊天 Hook（已集成投票）
├── components/ai-elements/
│   └── message-actions.tsx       # 消息操作组件（投票按钮）
├── test/
│   └── vote-test.tsx             # 投票功能测试组件
└── docs/
    └── voting-system.md          # 本文档
```

## 使用方法

### 1. 在 MessageActions 组件中

投票功能已集成到 MessageActions 组件中，自动处理用户点击投票按钮的交互：

```tsx
<MessageActions
  messageId={messageId}
  feedback={feedback}
  onFeedbackChange={onFeedbackChange}
  onToggleChainOfThought={onToggleChainOfThought}
  showChainOfThought={showChainOfThought}
/>
```

### 2. 直接使用投票 Hook

如果需要在其他组件中使用投票功能：

```tsx
import { useVote } from '@/hooks/use-vote';

const MyComponent = () => {
  const { submitVote, cancelVote, getUserVote, getVoteStats } = useVote({
    userId: 'user123', // 可选用户ID
    onSuccess: (vote) => console.log('投票成功:', vote),
    onError: (error) => console.error('投票失败:', error)
  });

  const handleVote = async () => {
    await submitVote(messageId, 'good');
  };

  return <button onClick={handleVote}>投票</button>;
};
```

### 3. 直接使用 API 服务

对于更高级的用例，可以直接使用 API 服务：

```tsx
import { voteApi } from '@/services/vote-api';
import { VoteType } from '@/types/vote';

// 创建投票
const vote = await voteApi.createVote({
  message_id: 123,
  vote_type: VoteType.GOOD
});

// 获取投票统计
const stats = await voteApi.getVoteStatsByMessage(123);

// 获取用户投票
const userVote = await voteApi.getUserVoteForMessage(123, 'user123');
```

## API 接口

新的投票系统与后端 API 的完整集成：

| 方法 | 接口 | 描述 |
|------|------|------|
| POST | `/vote/` | 创建投票 |
| GET | `/vote/{vote_id}` | 获取投票详情 |
| GET | `/vote/message/{message_id}` | 获取消息的所有投票 |
| PUT | `/vote/{vote_id}` | 更新投票 |
| DELETE | `/vote/{vote_id}` | 删除投票 |
| GET | `/vote/stats/message/{message_id}` | 获取消息投票统计 |
| GET | `/vote/stats/overview` | 获取总体投票统计 |
| GET | `/vote/user/message/{message_id}` | 获取用户对消息的投票 |

## 错误处理

系统包含完善的错误处理机制：

1. **网络错误处理**: 自动捕获和显示网络相关错误
2. **服务器错误处理**: 处理后端返回的错误信息
3. **用户反馈**: 通过 toast 通知显示操作结果
4. **降级处理**: API 失败时仍保持 UI 响应性

## 调试功能

### 控制台日志
系统包含详细的调试日志，可在浏览器控制台中查看：

```javascript
// 投票操作日志
console.log('投票成功，更新UI状态:', vote);
console.log('投票失败:', error);

// API 调用日志
console.log('处理好投票:', { messageId, currentFeedback: feedback });
console.log('投票结果:', { success, newFeedback, loading });
```

### 测试组件
使用 `VoteTestComponent` 可以完整测试投票功能：

```tsx
import { VoteTestComponent } from '@/test/vote-test';

// 在开发环境中添加到页面
<VoteTestComponent />
```

## 配置选项

### useVote Hook 配置

```typescript
const { ... } = useVote({
  userId?: string,        // 用户ID（可选）
  onSuccess?: (vote: Vote) => void,    // 成功回调
  onError?: (error: Error) => void     // 错误回调
});
```

## 类型定义

```typescript
// 投票类型
enum VoteType {
  GOOD = 'good',
  AVERAGE = 'average',
  POOR = 'poor'
}

// 前端反馈类型（向后兼容）
type VoteFeedback = 'good' | 'medium' | 'bad' | null;

// 投票数据结构
interface Vote {
  vote_id: number;
  message_id: number;
  vote_type: VoteType;
  created_at: string;
  updated_at: string;
}
```

## 注意事项

1. **向后兼容**: 系统保持与原有 `feedback` 类型的兼容性
2. **响应式设计**: 投票按钮在鼠标悬停时显示，避免界面杂乱
3. **加载状态**: 投票过程中按钮会被禁用，防止重复操作
4. **错误恢复**: API 失败时仍保持 UI 功能，确保用户体验

## 部署要求

确保后端投票 API 服务正常运行，并且前端能够访问到 `/vote` 相关接口。API 基础路径应为 `/vote`，与前端配置保持一致。