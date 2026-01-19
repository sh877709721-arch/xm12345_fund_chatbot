// import React, { useState, useEffect } from "react";
// import { Card } from "@/components/ui/card";
// import { MessageActions } from "./message-actions";
// import { useVote } from "@/hooks/use-vote";

// // 消息类型定义
// interface Message {
//   id: number;  // 修改为数字类型
//   content: string;
//   role: "user" | "assistant";
//   created_at: string;
// }

// interface MessageWithVotingProps {
//   message: Message;
//   className?: string;
// }

// export const MessageWithVoting: React.FC<MessageWithVotingProps> = ({
//   message,
//   className
// }) => {
//   // 本地状态管理投票状态
//   const [feedback, setFeedback] = useState<'good' | 'medium' | 'bad' | null>(null);
//   const { getMessageVoteStatus } = useVote();

//   // 组件初始化时加载投票状态
//   useEffect(() => {
//     const loadInitialVoteStatus = async () => {
//       try {
//         const voteStatus = await getMessageVoteStatus(message.id);
//         if (voteStatus) {
//           setFeedback(voteStatus);
//         }
//       } catch (error) {
//         console.error('加载投票状态失败:', error);
//       }
//     };

//     if (message.role === "assistant") {
//       loadInitialVoteStatus();
//     }
//   }, [message.id, message.role, getMessageVoteStatus]);

//   // 处理投票状态变化
//   const handleFeedbackChange = (
//     newFeedback: 'good' | 'medium' | 'bad' | null
//   ) => {
//     setFeedback(newFeedback);
//   };

//   // 只对 assistant 角色的消息显示投票按钮
//   if (message.role !== "assistant") {
//     return (
//       <Card className={`p-4 ${className}`}>
//         <div className="flex justify-between items-start">
//           <div className="flex-1">
//             <p className="text-sm font-medium text-muted-foreground mb-2">用户</p>
//             <p className="text-sm">{message.content}</p>
//           </div>
//           <div className="text-xs text-muted-foreground ml-2">
//             {new Date(message.created_at).toLocaleTimeString()}
//           </div>
//         </div>
//       </Card>
//     );
//   }

//   return (
//     <Card className={`p-4 ${className}`}>
//       <div className="flex justify-between items-start">
//         <div className="flex-1">
//           <div className="flex items-center gap-2 mb-2">
//             <p className="text-sm font-medium text-blue-600">助手</p>
//             {feedback && (
//               <span className={`
//                 text-xs px-2 py-1 rounded-full
//                 ${feedback === 'good' ? 'bg-green-100 text-green-700' : ''}
//                 ${feedback === 'medium' ? 'bg-yellow-100 text-yellow-700' : ''}
//                 ${feedback === 'bad' ? 'bg-red-100 text-red-700' : ''}
//               `}>
//                 {feedback === 'good' ? '好评' :
//                   feedback === 'medium' ? '中评' : '差评'}
//               </span>
//             )}
//           </div>
//           <p className="text-sm whitespace-pre-wrap">{message.content}</p>
//         </div>
//         <div className="flex flex-col items-end gap-2 ml-2">
//           <div className="text-xs text-muted-foreground">
//             {new Date(message.created_at).toLocaleTimeString()}
//           </div>
//           <MessageActions
//             messageId={message.id}
//             feedback={feedback}
//             onFeedbackChange={handleFeedbackChange}
//             className="mt-1"
//           />
//         </div>
//       </div>
//     </Card>
//   );
// };

// // 使用示例组件
// export const VotingExample: React.FC = () => {
//   const [messages] = useState<Message[]>([
//     {
//       id: 1,
//       content: "你好！有什么可以帮助你的吗？",
//       role: "assistant",
//       created_at: new Date().toISOString()
//     },
//     {
//       id: 2,
//       content: "请帮我解释一下React中的useEffect hook",
//       role: "user",
//       created_at: new Date().toISOString()
//     },
//     {
//       id: 3,
//       content: "useEffect是React中的一个Hook，用于处理副作用操作。它可以在函数组件中执行副作用操作，比如数据获取、订阅、DOM操作等。\n\n基本语法：\n```javascript\nuseEffect(() => {\n  // 副作用逻辑\n  return () => {\n    // 清理函数（可选）\n  };\n}, [dependencies]); // 依赖项数组\n```\n\n主要特点：\n1. 在组件渲染后执行\n2. 可以返回清理函数\n3. 通过依赖项控制执行时机\n4. 可以模拟生命周期方法",
//       role: "assistant",
//       created_at: new Date().toISOString()
//     }
//   ]);

//   return (
//     <div className="max-w-2xl mx-auto p-4 space-y-4">
//       <h2 className="text-xl font-bold mb-4">消息投票功能演示</h2>
//       <p className="text-sm text-muted-foreground mb-4">
//         下面的对话展示了消息投票功能。只有助手角色的消息右侧会显示投票按钮，
//         用户可以对回答质量进行好评、中评或差评。
//       </p>

//       {messages.map((message) => (
//         <MessageWithVoting
//           key={message.id}
//           message={message}
//         />
//       ))}
//     </div>
//   );
// };