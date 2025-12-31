import { useState } from "react";
import { createOrUpdateVote, getMessageVote, VoteType } from "@/utils/request/vote";

interface UseVoteOptions {
  onSuccess?: (vote: any) => void;
  onError?: (error: any) => void;
}

export const useVote = (options: UseVoteOptions = {}) => {
  const [loading, setLoading] = useState(false);

  // 简化的投票函数
  const handleToggleVote = async (
    messageId: number,
    currentFeedback: 'good' | 'medium' | 'bad' | null,
    newFeedback: 'good' | 'medium' | 'bad' | null,
    feedbackContent: string | null
  ): Promise<boolean> => {
    if (loading) return false;

    console.log('开始投票操作:', { messageId, currentFeedback, newFeedback });

    setLoading(true);

    try {
      if (newFeedback === null) {
        // 取消投票 - 暂时跳过，先实现基本的投票功能
        console.log('取消投票功能暂未实现');
        return false;
      } else {
        // 创建投票
        const voteType = newFeedback === 'good' ? VoteType.GOOD :
                        newFeedback === 'medium' ? VoteType.MEDIUM : VoteType.BAD;

        console.log('发送投票请求:', { messageId, voteType, feedbackContent});

        const result = await createOrUpdateVote(messageId, voteType, feedbackContent);

        options.onSuccess?.(result);

        return true;
      }

    } catch (error) {
      console.error('投票操作失败:', error);
      options.onError?.(error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // 获取消息的投票状态
  const getMessageVoteStatus = async (messageId: number) => {
    try {
      console.log('获取消息投票状态:', messageId);
      const result = await getMessageVote(messageId);

      if (result && result.data) {
        const voteType = result.data.vote_type;
        const feedback = voteType === 'good' ? 'good' :
                        voteType === 'medium' ? 'medium' : 'bad';
        console.log('找到投票状态:', feedback);
        return feedback;
      }

      console.log('没有找到投票记录');
      return null;
    } catch (error) {
      console.error('获取投票状态失败:', error);
      return null;
    }
  };

  return {
    toggleVote: handleToggleVote,
    getMessageVoteStatus,
    loading
  };
};