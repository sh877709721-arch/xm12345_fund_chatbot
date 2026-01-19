// 知识库数据
import { useKnowledgeData } from "./use-knowledge-data";
import { useVoteData } from "./use-vote-data";
// 标签数据
//import { useLabelBatchData } from "./use-label-batch-data";

export function useAdminData() {
  const knowledgeData = useKnowledgeData();
  const voteData = useVoteData();
  //const labelBatchData = useLabelBatchData();

  return {
    // 知识库相关
    knowledge: {
      ...knowledgeData,
      refresh: knowledgeData.refreshCatalogs,
    },

    // 投票相关
    vote: {
      ...voteData,
      refresh: voteData.handleRefresh,
    },

    // 标签批次相关
    // labelBatch: {
    //   ...labelBatchData,
    //   refresh: labelBatchData.fetchBatches,
    // },
  };
}