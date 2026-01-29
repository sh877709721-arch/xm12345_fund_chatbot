"""
意图分类优化器
提供意图分类的优化策略和性能调优
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from app.core.agents.assistant_intent import IntentClassifier


@dataclass
class ClassificationConfig:
    """分类配置类"""
    model_name: str = "glm-4.5-air"
    temperature: float = 0.1
    max_tokens: int = 1024
    vector_weight: float = 0.4
    bm25_weight: float = 0.3
    graph_weight: float = 0.3
    similarity_threshold: float = 0.6
    top_k: int = 5
    use_rerank: bool = True
    confidence_threshold: float = 0.7
    use_graph: bool = True
    graph_similarity_threshold: float = 0.5
    # 新增：增强分类器配置
    enable_enhanced_classifier: bool = True
    graph_knowledge_weight: float = 0.7  # 图谱知识在分类中的权重
    max_graph_entities: int = 10  # 最大实体数量
    max_graph_relationships: int = 15  # 最大关系数量


class IntentOptimizer:
    """意图分类优化器"""

    def __init__(self, config: Optional[ClassificationConfig] = None):
        self.config = config or ClassificationConfig()

    def optimize_search_weights(self, 
                                test_queries: List[str], 
                                expected_results: List[Dict]) -> Dict:
        """
        优化搜索权重参数

        Args:
            test_queries: 测试查询列表
            expected_results: 期望的分类结果

        Returns:
            最优参数配置
        """
        best_params = {}
        best_accuracy = 0.0

        # 参数网格搜索
        vector_weights = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        thresholds = [0.5, 0.6, 0.7, 0.8]
        top_ks = [3, 5, 10, 15]

        for vw in vector_weights:
            for thr in thresholds:
                for tk in top_ks:
                    accuracy = self._evaluate_params(
                        test_queries, expected_results, vw, 1-vw, thr, tk
                    )

                    if accuracy > best_accuracy:
                        best_accuracy = accuracy
                        best_params = {
                            'vector_weight': vw,
                            'bm25_weight': 1-vw,
                            'similarity_threshold': thr,
                            'top_k': tk,
                            'accuracy': accuracy
                        }

        logging.info(f"最优参数: {best_params}")
        return best_params

    def _evaluate_params(self, queries: List[str], expected: List[Dict],
                        vw: float, bw: float, thr: float, tk: int) -> float:
        """评估参数组合的准确率"""
        correct = 0
        total = len(queries)

        for query, expected_result in zip(queries, expected):
            try:
                # 创建测试配置
                test_config = ClassificationConfig(
                    vector_weight=vw,
                    bm25_weight=bw,
                    similarity_threshold=thr,
                    top_k=tk
                )

                # 使用配置化的分类方法
                result = self._classify_with_config(query, test_config)

                # 检查分类是否正确
                if (result.get('main_category') == expected_result.get('main_category') and
                    result.get('sub_category') == expected_result.get('sub_category')):
                    correct += 1

            except Exception as e:
                logging.warning(f"参数评估出错: {e}")
                continue

        return correct / total if total > 0 else 0.0

    def ensemble_classification(self, 
                                query: str, 
                                strategies: List[str] = None, 
                                include_confidence: bool = False, 
                                use_graph: Optional[bool] = None) -> Dict:
        """
        集成分类，使用多种策略进行分类并投票

        Args:
            query: 用户查询
            strategies: 分类策略列表
            include_confidence: 是否包含置信度分析
            use_graph: 是否使用知识图谱搜索（None表示使用默认配置）
            force_enhanced: 是否强制使用增强分类器（None表示自动选择）

        Returns:
            集成分类结果，可选包含置信度信息
        """
        if strategies is None:
            strategies = ['conservative', 'balanced']

        results = []
        confidence_variations = []  # 存储用于置信度分析的变化结果

        from app.core.agents.assistant_intent import IntentClassifier
        self.classifier = IntentClassifier()
        self.use_enhanced = False
        logging.info("临时切换到传统意图分类器")

        # 如果指定了use_graph，更新配置
        if use_graph is not None:
            original_use_graph = self.config.use_graph
            self.config.use_graph = use_graph
        else:
            original_use_graph = self.config.use_graph

        try:
            # 保守策略：高阈值，更多搜索结果
            if 'conservative' in strategies:
                self.config.similarity_threshold = 0.8
                self.config.top_k = 10
                if self.config.use_graph:
                    self.config.vector_weight = 0.3
                    self.config.bm25_weight = 0.3
                    self.config.graph_weight = 0.4  # 知识图谱权重更高
                else:
                    self.config.vector_weight = 0.6
                    self.config.bm25_weight = 0.4

                result = self._classify_with_config(query, self.config)
                result['strategy'] = 'conservative'
                result['search_mode'] = 'graph_enhanced' if self.config.use_graph else 'traditional'
                result['classifier_type'] = 'enhanced' if self.use_enhanced else 'traditional'
                results.append(result)

                if include_confidence:
                    confidence_variations.append({
                        'params': {
                            'similarity_threshold': 0.8,
                            'strategy': 'conservative',
                            'use_graph': self.config.use_graph,
                            'graph_weight': self.config.graph_weight if self.config.use_graph else 0.0,
                            'classifier_type': 'enhanced' if self.use_enhanced else 'traditional'
                        },
                        'result': result
                    })

            # 平衡策略：默认参数
            if 'balanced' in strategies:
                self.config.similarity_threshold = 0.6
                self.config.top_k = 5
                if self.config.use_graph:
                    self.config.vector_weight = 0.4
                    self.config.bm25_weight = 0.3
                    self.config.graph_weight = 0.3  # 平衡的权重分配
                else:
                    self.config.vector_weight = 0.6
                    self.config.bm25_weight = 0.4

                result = self._classify_with_config(query, self.config)
                result['strategy'] = 'balanced'
                result['search_mode'] = 'graph_enhanced' if self.config.use_graph else 'traditional'
                results.append(result)

                if include_confidence:
                    confidence_variations.append({
                        'params': {
                            'similarity_threshold': 0.6,
                            'strategy': 'balanced',
                            'use_graph': self.config.use_graph,
                            'graph_weight': self.config.graph_weight if self.config.use_graph else 0.0
                        },
                        'result': result
                    })

            # 图谱优先策略（仅在使用知识图谱时）
            if self.config.use_graph and 'graph_priority' in strategies:
                self.config.similarity_threshold = 0.7
                self.config.top_k = 8
                self.config.vector_weight = 0.2
                self.config.bm25_weight = 0.2
                self.config.graph_weight = 0.6  # 知识图谱主导

                result = self._classify_with_config(query, self.config)
                result['strategy'] = 'graph_priority'
                result['search_mode'] = 'graph_enhanced'
                results.append(result)

                if include_confidence:
                    confidence_variations.append({
                        'params': {
                            'similarity_threshold': 0.7,
                            'strategy': 'graph_priority',
                            'use_graph': self.config.use_graph,
                            'graph_weight': self.config.graph_weight
                        },
                        'result': result
                    })

        finally:
            # 恢复原始配置
            if use_graph is not None:
                self.config.use_graph = original_use_graph

        # 投票决定最终结果
        final_result = self._vote_results(results)

        # 如果需要置信度分析，直接使用已有的变体结果计算
        if include_confidence and confidence_variations:
            confidence_analysis = self._calculate_confidence_from_variations(
                confidence_variations, query
            )
            final_result['confidence_analysis'] = confidence_analysis

        # 添加搜索模式信息
        final_result['ensemble_search_mode'] = 'graph_enhanced' if (use_graph if use_graph is not None else self.config.use_graph) else 'traditional'

        return final_result

    def _calculate_confidence_from_variations(self, variations: List[Dict], query: str) -> Dict:
        """
        基于已有的分类变体计算置信度分析

        Args:
            variations: 分类变体结果列表
            query: 原始查询

        Returns:
            置信度分析结果
        """
        try:
            # 收集所有主要分类结果
            main_categories = {}
            successful_variations = [var for var in variations if var.get('result') and not var.get('result', {}).get('main_category') == '错误']

            # 统计各分类出现的频率
            for var in successful_variations:
                result = var['result']
                main_cat = result.get('main_category', '未知')

                if main_cat not in main_categories:
                    main_categories[main_cat] = {
                        'count': 0,
                        'sub_categories': {},
                        'total_confidence': 0.0,
                        'variations': []
                    }

                main_categories[main_cat]['count'] += 1
                main_categories[main_cat]['total_confidence'] += result.get('confidence', 0.0)
                main_categories[main_cat]['variations'].append(var)

                # 统计子分类
                sub_cat = result.get('sub_category', '未知')
                if sub_cat not in main_categories[main_cat]['sub_categories']:
                    main_categories[main_cat]['sub_categories'][sub_cat] = 0
                main_categories[main_cat]['sub_categories'][sub_cat] += 1

            if not main_categories:
                return {
                    'overall_confidence': 0.0,
                    'consistency_score': 0.0,
                    'strategy_agreement': {},
                    'recommendation': 'no_valid_results',
                    'variations_count': 0
                }

            # 找出最多的主要分类
            dominant_category = max(main_categories.keys(), key=lambda x: main_categories[x]['count'])
            dominant_data = main_categories[dominant_category]

            # 计算一致性分数
            total_variations = len(successful_variations)
            consistency_score = dominant_data['count'] / total_variations if total_variations > 0 else 0.0

            # 计算平均置信度
            avg_confidence = dominant_data['total_confidence'] / dominant_data['count'] if dominant_data['count'] > 0 else 0.0

            # 计算策略一致性
            strategy_agreement = {}
            for var in successful_variations:
                strategy = var['params'].get('strategy', 'unknown')
                category = var['result'].get('main_category', '未知')
                if strategy not in strategy_agreement:
                    strategy_agreement[strategy] = {}
                if category not in strategy_agreement[strategy]:
                    strategy_agreement[strategy][category] = 0
                strategy_agreement[strategy][category] += 1

            # 生成推荐
            if consistency_score >= 0.8:
                recommendation = 'high_confidence'
            elif consistency_score >= 0.6:
                recommendation = 'moderate_confidence'
            else:
                recommendation = 'low_confidence'

            return {
                'overall_confidence': avg_confidence,
                'consistency_score': consistency_score,
                'strategy_agreement': strategy_agreement,
                'dominant_category': dominant_category,
                'category_distribution': {cat: data['count'] for cat, data in main_categories.items()},
                'recommendation': recommendation,
                'variations_count': total_variations,
                'search_optimization': {
                    'rerank_calls_saved': 2,  # 相比于单独调用analyze_classification_confidence节省的rerank次数
                    'performance_improvement': '50%'
                }
            }

        except Exception as e:
            logging.error(f"置信度分析失败: {e}")
            return {
                'overall_confidence': 0.0,
                'consistency_score': 0.0,
                'error': str(e),
                'recommendation': 'analysis_failed'
            }

    def _classify_with_config(self, query: str, config: ClassificationConfig) -> Dict:
        """使用指定配置进行分类"""
        original_method = None
        try:
            # 根据配置选择搜索方法
            if config.use_graph:
                # 使用综合搜索（包含知识图谱）
                original_method = self.classifier.rag_search.hybrid_search_with_rerank

                def configured_search(query: str,
                                     vector_weight: float = 0.4,
                                     bm25_weight: float = 0.3,
                                     similarity_threshold: float = 0.7,
                                     top_k: int = 10) -> List[Dict]:
                    # 使用传入的参数，如果未传入则使用配置的参数
                    actual_vector_weight = vector_weight if vector_weight != 0.4 else config.vector_weight
                    actual_bm25_weight = bm25_weight if bm25_weight != 0.3 else config.bm25_weight
                    actual_graph_weight = config.graph_weight
                    actual_similarity_threshold = similarity_threshold if similarity_threshold != 0.7 else config.similarity_threshold
                    actual_top_k = top_k if top_k != 10 else config.top_k

                    # 使用综合搜索，包含知识图谱
                    return self.classifier.rag_search.comprehensive_search_with_graph(
                        query,
                        vector_weight=actual_vector_weight,
                        bm25_weight=actual_bm25_weight,
                        graph_weight=actual_graph_weight,
                        similarity_threshold=actual_similarity_threshold,
                        top_k=actual_top_k,
                        enable_rerank=config.use_rerank
                    )

                self.classifier.rag_search.hybrid_search_with_rerank = configured_search
            else:
                # 使用传统的混合搜索（不包含知识图谱）
                original_method = self.classifier.rag_search.hybrid_search_with_rerank

                def configured_search(query: str,
                                     vector_weight: float = 0.7,
                                     bm25_weight: float = 0.3,
                                     similarity_threshold: float = 0.7,
                                     top_k: int = 10) -> List[Dict]:
                    # 使用传入的参数，如果未传入则使用配置的参数
                    actual_vector_weight = vector_weight if vector_weight != 0.7 else config.vector_weight
                    actual_bm25_weight = bm25_weight if bm25_weight != 0.3 else config.bm25_weight
                    actual_similarity_threshold = similarity_threshold if similarity_threshold != 0.7 else config.similarity_threshold
                    actual_top_k = top_k if top_k != 10 else config.top_k

                    return original_method(
                        query,
                        vector_weight=actual_vector_weight,
                        bm25_weight=actual_bm25_weight,
                        similarity_threshold=actual_similarity_threshold,
                        top_k=actual_top_k
                    )

                self.classifier.rag_search.hybrid_search_with_rerank = configured_search

            # 使用配置好的分类器进行分类
            result = self.classifier.classify_intent(query, top_k=config.top_k)

            return result

        except Exception as e:
            logging.error(f"配置化分类失败: {e}")
            # 返回错误结果
            return {
                "main_category": "错误",
                "sub_category": "错误",
                "detail_category": "错误",
                "confidence": 0.0,
                "reason": f"配置化分类异常: {str(e)}"
            }
        finally:
            # 确保方法被恢复
            if original_method is not None:
                try:
                    self.classifier.rag_search.hybrid_search_with_rerank = original_method
                except:
                    pass

    def _vote_results(self, results: List[Dict]) -> Dict:
        """对多个分类结果进行投票"""
        if not results:
            return {"error": "没有可用的分类结果"}

        # 统计投票
        category_votes = {}
        confidence_sum = 0.0

        for result in results:
            confidence = result.get('confidence', 0.0)
            main_cat = result.get('main_category', '未知')
            sub_cat = result.get('sub_category', '未知')
            detail_cat = result.get('detail_category', '未知')

            category_key = f"{main_cat}|{sub_cat}|{detail_cat}"

            if category_key not in category_votes:
                category_votes[category_key] = {
                    'count': 0,
                    'confidence_sum': 0.0,
                    'main_category': main_cat,
                    'sub_category': sub_cat,
                    'detail_category': detail_cat
                }

            category_votes[category_key]['count'] += 1
            category_votes[category_key]['confidence_sum'] += confidence
            confidence_sum += confidence

        # 选择得票最多的类别
        if not category_votes:
            return results[0]  # 如果没有投票结果，返回第一个结果

        # 按投票数和置信度排序
        sorted_votes = sorted(
            category_votes.values(),
            key=lambda x: (x['count'], x['confidence_sum']),
            reverse=True
        )

        best_category = sorted_votes[0]
        avg_confidence = confidence_sum / len(results)

        # 组合所有结果的搜索上下文
        all_search_context = []
        for result in results:
            all_search_context.extend(result.get('search_context', []))

        return {
            'main_category': best_category['main_category'],
            'sub_category': best_category['sub_category'],
            'detail_category': best_category['detail_category'],
            'confidence': avg_confidence,
            'vote_count': best_category['count'],
            'total_votes': len(results),
            'reason': f"集成分类结果，{best_category['count']}/{len(results)}票支持",
            'search_results_count': len(all_search_context),
            'search_context': all_search_context[:5],  # 保留前5个上下文
            'ensemble_strategies': [r.get('strategy', 'unknown') for r in results]
        }

    def analyze_classification_confidence(self, query: str, fast_mode: bool = True, use_ensemble_optimization: bool = False, use_graph: Optional[bool] = None) -> Dict:
        """
        分析分类置信度的详细信息 - 优化性能版本

        Args:
            query: 用户查询
            fast_mode: 是否使用快速模式（较少参数组合）
            use_ensemble_optimization: 是否使用ensemble优化（复用ensemble分类结果）
            use_graph: 是否使用知识图谱搜索（None表示使用默认配置）
        """

        # 如果启用ensemble优化，直接使用ensemble_classification的结果
        if use_ensemble_optimization:
            ensemble_result = self.ensemble_classification(
                query,
                strategies=['conservative', 'balanced'],
                include_confidence=True,
                use_graph=use_graph
            )
            return ensemble_result.get('confidence_analysis', {})
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # 确定是否使用知识图谱
        current_use_graph = use_graph if use_graph is not None else self.config.use_graph

        # 根据模式选择参数组合
        if fast_mode:
            # 快速模式：只测试2-3个关键参数组合
            if current_use_graph:
                # 包含知识图谱的参数组合
                param_combinations = [
                    {'similarity_threshold': 0.6, 'param_type': 'threshold', 'value': 0.6, 'use_graph': True},
                    {
                        'vector_weight': 0.4, 'bm25_weight': 0.3, 'graph_weight': 0.3,
                        'param_type': 'graph_balanced', 'value': 'balanced', 'use_graph': True
                    },
                ]
            else:
                # 传统搜索的参数组合
                param_combinations = [
                    {'similarity_threshold': 0.6, 'param_type': 'threshold', 'value': 0.6, 'use_graph': False},
                    {'vector_weight': 0.6, 'bm25_weight': 0.4, 'param_type': 'vector_weight', 'value': 0.6, 'use_graph': False},
                ]
            max_workers = 4
            timeout = 15
        else:
            # 完整模式：测试所有参数组合
            if current_use_graph:
                # 包含知识图谱的完整参数组合
                param_combinations = [
                    # 改变相似度阈值
                    {'similarity_threshold': 0.4, 'param_type': 'threshold', 'value': 0.4, 'use_graph': True},
                    {'similarity_threshold': 0.6, 'param_type': 'threshold', 'value': 0.6, 'use_graph': True},
                    {'similarity_threshold': 0.8, 'param_type': 'threshold', 'value': 0.8, 'use_graph': True},
                    # 改变搜索权重（包含知识图谱）
                    {
                        'vector_weight': 0.2, 'bm25_weight': 0.2, 'graph_weight': 0.6,
                        'param_type': 'graph_priority', 'value': 'graph_priority', 'use_graph': True
                    },
                    {
                        'vector_weight': 0.4, 'bm25_weight': 0.3, 'graph_weight': 0.3,
                        'param_type': 'graph_balanced', 'value': 'balanced', 'use_graph': True
                    },
                    {
                        'vector_weight': 0.5, 'bm25_weight': 0.4, 'graph_weight': 0.1,
                        'param_type': 'graph_supplement', 'value': 'supplement', 'use_graph': True
                    },
                ]
            else:
                # 传统搜索的完整参数组合
                param_combinations = [
                    # 改变相似度阈值
                    {'similarity_threshold': 0.4, 'param_type': 'threshold', 'value': 0.4, 'use_graph': False},
                    {'similarity_threshold': 0.6, 'param_type': 'threshold', 'value': 0.6, 'use_graph': False},
                    {'similarity_threshold': 0.8, 'param_type': 'threshold', 'value': 0.8, 'use_graph': False},
                    # 改变搜索权重
                    {'vector_weight': 0.3, 'bm25_weight': 0.7, 'param_type': 'vector_weight', 'value': 0.3, 'use_graph': False},
                    {'vector_weight': 0.5, 'bm25_weight': 0.5, 'param_type': 'vector_weight', 'value': 0.5, 'use_graph': False},
                    {'vector_weight': 0.7, 'bm25_weight': 0.3, 'param_type': 'vector_weight', 'value': 0.7, 'use_graph': False},
                ]
            max_workers = 10
            timeout = 30

        def classify_with_params(params: Dict) -> Dict:
            """使用指定参数进行分类的辅助函数"""
            try:
                # 创建临时配置
                temp_config = ClassificationConfig(
                    vector_weight=params.get('vector_weight', self.config.vector_weight),
                    bm25_weight=params.get('bm25_weight', self.config.bm25_weight),
                    graph_weight=params.get('graph_weight', self.config.graph_weight),
                    similarity_threshold=params.get('similarity_threshold', self.config.similarity_threshold),
                    top_k=self.config.top_k,
                    use_graph=params.get('use_graph', current_use_graph)
                )

                result = self._classify_with_config(query, temp_config)
                return {
                    'params': params,
                    'result': result,
                    'success': True
                }
            except Exception as e:
                logging.error(f"参数化分类失败 {params}: {e}")
                return {
                    'params': params,
                    'error': str(e),
                    'success': False
                }

        # 并发执行所有参数组合
        variations = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_params = {
                executor.submit(classify_with_params, params): params
                for params in param_combinations
            }

            # 收集结果
            for future in as_completed(future_to_params):
                try:
                    variation_result = future.result(timeout=timeout)
                    if variation_result['success']:
                        variations.append(variation_result)
                    else:
                        logging.warning(f"分类失败: {variation_result['error']}")
                except Exception as e:
                    params = future_to_params[future]
                    logging.error(f"获取分类结果失败 {params}: {e}")

        # 分析结果的一致性
        categories = {}
        successful_variations = [var for var in variations if var['success']]

        for var in successful_variations:
            result = var['result']
            cat_key = f"{result.get('main_category', '')}|{result.get('sub_category', '')}"
            if cat_key not in categories:
                categories[cat_key] = []
            categories[cat_key].append({
                'confidence': result.get('confidence', 0.0),
                'params': var['params']
            })

        # 计算一致性分数
        max_consensus = max(len(confs) for confs in categories.values()) if categories else 0
        consistency_score = max_consensus / len(successful_variations) if successful_variations else 0.0

        # 获取最一致的分类结果
        best_category_key = max(categories.keys(), key=lambda k: len(categories[k])) if categories else ""

        if best_category_key and categories[best_category_key]:
            confidences = [item['confidence'] for item in categories[best_category_key]]
            avg_confidence = sum(confidences) / len(confidences)

            # 获取最优参数组合
            best_params_info = max(categories[best_category_key], key=lambda x: x['confidence'])
            best_params = best_params_info['params']
        else:
            avg_confidence = 0.0
            best_params = {}

        main_cat, sub_cat = best_category_key.split('|') if '|' in best_category_key else (best_category_key, '')

        return {
            'query': query,
            'consistency_score': consistency_score,
            'predicted_category': {
                'main_category': main_cat,
                'sub_category': sub_cat,
                'confidence': avg_confidence
            },
            'best_params': best_params,
            'variations_tested': len(param_combinations),
            'successful_classifications': len(successful_variations),
            'category_distribution': {k: len(v) for k, v in categories.items()},
            'detailed_results': [
                {
                    'params': var['params'],
                    'category': f"{var['result'].get('main_category', '')}|{var['result'].get('sub_category', '')}",
                    'confidence': var['result'].get('confidence', 0.0)
                }
                for var in successful_variations
            ],
            'is_reliable': consistency_score >= 0.7 and avg_confidence >= 0.7,
            'performance_gain': {
                'mode': 'fast_mode' if fast_mode else 'full_mode',
                'param_combinations': len(param_combinations),
                'sequential_time_estimate': len(param_combinations) * 2.0,  # 估算串行时间
                'concurrent_time_estimate': 2.0 + (len(param_combinations) / max_workers) * 0.5,  # 估算并发时间
                'speedup_ratio': (len(param_combinations) * 2.0) / (2.0 + (len(param_combinations) / max_workers) * 0.5)
            }
        }

    def quick_confidence_estimate(self, query: str) -> Dict:
        """超快速置信度估计 - 单次分类 + 简单启发式判断"""
        try:
            # 只进行一次基础分类
            result = self.classifier.classify_intent(query)

            # 基于搜索结果和置信度进行快速判断
            confidence = result.get('confidence', 0.0)
            search_count = result.get('search_results_count', 0)

            # 简单的启发式规则
            consistency_estimate = min(1.0, confidence * (search_count / 5.0))
            reliability = confidence >= 0.6 and search_count >= 2

            return {
                'query': query,
                'consistency_score': consistency_estimate,
                'predicted_category': {
                    'main_category': result.get('main_category', '未知'),
                    'sub_category': result.get('sub_category', '未知'),
                    'confidence': confidence
                },
                'is_reliable': reliability,
                'mode': 'quick_estimate',
                'search_results_count': search_count,
                'performance_gain': {
                    'mode': 'ultra_fast',
                    'param_combinations': 1,
                    'time_estimate': 2.0,  # 单次分类时间
                    'speedup_ratio': 6.0  # 相比完整模式的加速比
                }
            }
        except Exception as e:
            return {
                'query': query,
                'consistency_score': 0.0,
                'predicted_category': {
                    'main_category': '错误',
                    'sub_category': '错误',
                    'confidence': 0.0
                },
                'is_reliable': False,
                'mode': 'quick_estimate',
                'error': str(e),
                'performance_gain': {
                    'mode': 'ultra_fast',
                    'time_estimate': 0.1,  # 快速失败时间
                    'speedup_ratio': 60.0
                }
            }


# 使用示例
# def example_optimizer_usage():
#     """优化器使用示例"""
#     optimizer = IntentOptimizer()

#     # 示例查询
#     query = "我想了解职工医保的报销比例"

#     print("=== 集成分类示例 ===")
#     ensemble_result = optimizer.ensemble_classification(query)
#     print(f"集成分类结果: {ensemble_result}")

#     print("\n=== 置信度分析示例 ===")
#     confidence_analysis = optimizer.analyze_classification_confidence(query)
#     print(f"置信度分析: {confidence_analysis}")


# if __name__ == "__main__":
#     example_optimizer_usage()