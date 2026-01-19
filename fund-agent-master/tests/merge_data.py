import pandas as pd
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def merge_data():
    """
    将源数据的question匹配测试问题的"测试问题"列，
    在test_chatbot_001.xlsx文件最右侧添加两列（knowledge_content, knowledge_label_id），
    然后保存为新的Excel文件
    """
    # 1. 读取源数据
    source_file = "data/result_concurrent_20251113_180444.xlsx"
    test_file = "data/test_chatbot_001.xlsx"
    output_file = "data/test_chatbot_with_knowledge.xlsx"

    try:
        # 读取源数据和测试数据
        df_source = pd.read_excel(source_file)
        df_test = pd.read_excel(test_file)

        logger.info(f"源数据文件 {source_file}: {len(df_source)} 行, 列: {list(df_source.columns)}")
        logger.info(f"测试问题文件 {test_file}: {len(df_test)} 行, 列: {list(df_test.columns)}")

        # 2. 创建源数据匹配字典
        # 从源数据中提取 question 和对应的content, knowledge_label_id信息
        source_mapping = {}
        for _, row in df_source.iterrows():
            source_question = str(row['question']).strip()
            if source_question != 'nan':  # 跳过空值
                source_mapping[source_question] = {
                    'content': row.get('content', ''),
                    'knowledge_label_id': row.get('knowledge_label_id', ''),
                    'question': source_question
                }

        logger.info(f"创建了包含 {len(source_mapping)} 个源问题的映射字典")

        # 3. 为测试数据添加匹配列
        knowledge_contents = []
        knowledge_label_ids = []
        match_count = 0

        for _, row in df_test.iterrows():
            test_question = str(row['测试问题']).strip()

            # 尝试精确匹配
            if test_question in source_mapping:
                match_info = source_mapping[test_question]
                knowledge_contents.append(match_info['content'])
                knowledge_label_ids.append(match_info['knowledge_label_id'])
                match_count += 1
            else:
                # 如果没有精确匹配，尝试模糊匹配（基于字符相似度）
                best_match = None
                best_score = 0

                for source_q in source_mapping.keys():
                    # 简单的相似度计算：基于共同字符比例
                    common_chars = set(test_question) & set(source_q)
                    similarity = len(common_chars) / max(len(set(test_question)), len(set(source_q)))

                    if similarity > best_score and similarity > 0.7:  # 相似度阈值
                        best_score = similarity
                        best_match = source_q

                if best_match:
                    knowledge_contents.append(source_mapping[best_match]['content'])
                    knowledge_label_ids.append(source_mapping[best_match]['knowledge_label_id'])
                    match_count += 1
                else:
                    # 没有找到匹配
                    knowledge_contents.append('')
                    knowledge_label_ids.append('')

        # 4. 添加新列到测试数据
        df_test['knowledge_content'] = knowledge_contents
        df_test['knowledge_label_id'] = knowledge_label_ids

        logger.info(f"成功匹配 {match_count}/{len(df_test)} 条记录")

        # 5. 保存结果到新文件
        df_test.to_excel(output_file, index=False)

        logger.info(f"结果已保存到: {output_file}")
        logger.info(f"输出文件包含 {len(df_test)} 行, {len(df_test.columns)} 列")

        # 6. 显示匹配统计
        matched_df = df_test[(df_test['knowledge_content'] != '') | (df_test['knowledge_label_id'] != '')]
        logger.info(f"匹配成功的记录数: {len(matched_df)}")

        if len(matched_df) > 0:
            logger.info("匹配示例:")
            for _, row in matched_df.head(3).iterrows():
                logger.info(f"  测试问题: {row['测试问题'][:50]}...")
                logger.info(f"  知识内容: {str(row['knowledge_content'])[:50]}...")
                logger.info(f"  知识标签ID: {row['knowledge_label_id']}")

        return df_test

    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        raise
    except Exception as e:
        logger.error(f"数据合并过程中出错: {e}")
        raise

if __name__ == "__main__":
    merge_data()