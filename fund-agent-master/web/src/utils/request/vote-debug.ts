import instance from "./instance";

// 简化的调试版本 - 只保留最基本的功能
export async function simpleVote(messageId: number, voteType: string) {
  try {
    console.log('发送投票请求:', { messageId, voteType });

    const response = await instance.post("/v1/vote/", {
      message_id: messageId,
      vote_type: voteType
    });

    console.log('投票响应:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('投票失败:', error);
    throw error;
  }
}

// 测试不同的投票类型
export async function testVote(messageId: number) {
  console.log('=== 测试投票功能 ===');

  const testCases = ['good', 'average', 'poor'];

  for (const voteType of testCases) {
    try {
      console.log(`测试 ${voteType} 投票...`);
      const result = await simpleVote(messageId, voteType);
      console.log(`${voteType} 投票成功:`, result);

      // 等待一下再测试下一个
      await new Promise(resolve => setTimeout(resolve, 1000));

    } catch (error) {
      console.error(`${voteType} 投票失败:`, error);
    }
  }
}