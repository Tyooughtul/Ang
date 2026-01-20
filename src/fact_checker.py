import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .web_searcher import WebSearcher
from openai import OpenAI

logger = logging.getLogger(__name__)

class FactChecker:
    """内容审查员：验证内容的真实性和时效性（集成 GLM-4.7 Web 搜索）"""
    
    def __init__(self, api_key: str = None, base_url: str = None, doubao_api_key: str = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = base_url or DEEPSEEK_BASE_URL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None
        self.web_searcher = WebSearcher(api_key=doubao_api_key)
    
    def _analyze_content_freshness(self, content: str, topic: str) -> Dict:
        """
        分析内容本身的新鲜度（不依赖时间戳）
        
        Args:
            content: 内容文本
            topic: 话题
        
        Returns:
            新鲜度分析结果
        """
        content_lower = content.lower()
        
        fresh_keywords = [
            '最新', '新版本', '刚刚发布', '今天发布', '本月',
            '最近', '新推出', '正式发布', '上线', '发布',
            'v2.0', 'v3.0', 'v4.0', 'v5.0', 'v6.0',
            '2025', '2026', '2027', '2028', '2029', '2030',
            'beta', 'alpha', 'rc', 'release', 'stable'
            '更新', '升级', '新增', '改进', '优化', '修复'
            'breaking news', 'breaking', '突发', '重磅', '重磅'
            '首次', 'first', '首个', '第一', '初次'
            '最新消息', '最新动态', '最新进展', '最新情况'
            '今天', '今日', '现在', '当前', '正在'
        ]
        
        fresh_count = sum(1 for keyword in fresh_keywords if keyword in content_lower)
        
        if fresh_count >= 3:
            return {
                'is_fresh': True,
                'freshness_level': '最新',
                'score': 95,
                'reasoning': f"内容包含 {fresh_count} 个新鲜度关键词，判断为最新",
                'method': 'content_analysis'
            }
        elif fresh_count >= 1:
            return {
                'is_fresh': True,
                'freshness_level': '较新',
                'score': 85,
                'reasoning': f"内容包含 {fresh_count} 个新鲜度关键词，判断为较新",
                'method': 'content_analysis'
            }
        else:
            return {
                'is_fresh': False,
                'freshness_level': '未知',
                'score': 50,
                'reasoning': '内容未包含明显的新鲜度关键词',
                'method': 'content_analysis'
            }
    
    def _check_topic_relevance(self, content: str, topic: str) -> Dict:
        """
        检查内容与话题的相关性
        
        Args:
            content: 内容文本
            topic: 话题
        
        Returns:
            相关性检查结果
        """
        topic_lower = topic.lower()
        content_lower = content.lower()
        
        topic_keywords = topic_lower.split()
        relevance_count = sum(1 for keyword in topic_keywords if keyword in content_lower)
        
        if relevance_count >= 3:
            return {
                'is_relevant': True,
                'relevance_score': 90,
                'reasoning': f"内容与话题高度相关（包含 {relevance_count} 个关键词）",
                'method': 'keyword_matching'
            }
        elif relevance_count >= 1:
            return {
                'is_relevant': True,
                'relevance_score': 70,
                'reasoning': f"内容与话题相关（包含 {relevance_count} 个关键词）",
                'method': 'keyword_matching'
            }
        else:
            return {
                'is_relevant': False,
                'relevance_score': 30,
                'reasoning': '内容与话题相关性较低',
                'method': 'keyword_matching'
            }
    
    def verify_claim(self, claim: str, sources: List[str] = None) -> Dict:
        """
        验证某个声明或事实（使用豆包 Web 搜索，增强版）
        
        Args:
            claim: 待验证的声明
            sources: 已知来源列表
        
        Returns:
            验证结果字典
        """
        try:
            logger.info(f"验证声明: {claim[:50]}...")
            
            if self.web_searcher.api_key:
                logger.info("使用豆包 Web 搜索验证事实（多源验证）")
                
                verification_results = []
                
                for i in range(2):
                    logger.info(f"进行第 {i+1} 轮验证...")
                    web_result = self.web_searcher.verify_fact(claim)
                    
                    if web_result.get('confidence', 0) > 0:
                        verification_results.append(web_result)
                        logger.info(f"第 {i+1} 轮验证成功，可信度: {web_result.get('confidence', 0)}")
                
                if verification_results:
                    avg_confidence = sum(r.get('confidence', 0) for r in verification_results) / len(verification_results)
                    all_sources = []
                    all_search_results = []
                    
                    for result in verification_results:
                        all_sources.extend(result.get('sources', []))
                        all_search_results.extend(result.get('search_results', []))
                    
                    is_true = all(r.get('is_true') for r in verification_results)
                    
                    if is_true and avg_confidence >= 80:
                        reasoning = f"多源验证一致，可信度高（{len(verification_results)} 轮验证）"
                    elif is_true and avg_confidence >= 60:
                        reasoning = f"多源验证基本一致，可信度中等（{len(verification_results)} 轮验证）"
                    elif not is_true:
                        reasoning = f"多源验证发现矛盾，可信度低（{len(verification_results)} 轮验证）"
                    else:
                        reasoning = f"多源验证结果不一致，需要人工审核（{len(verification_results)} 轮验证）"
                    
                    return {
                        'is_true': is_true,
                        'confidence': avg_confidence,
                        'reasoning': reasoning,
                        'sources': list(set(all_sources)),
                        'search_results': all_search_results,
                        'method': 'multi_source_web_search',
                        'verification_count': len(verification_results)
                    }
            
            if not self.client:
                return {
                    "is_true": None,
                    "confidence": 0,
                    "reasoning": "未配置 API Key，无法验证",
                    "sources": [],
                    "method": "none"
                }
            
            verification_prompt = f"""你是一个专业的事实核查员，擅长验证科技新闻的真实性。

任务：严格验证以下声明的真实性

声明：{claim}

验证要求：
1. 使用你的知识库判断这个声明是否真实
2. 如果声明涉及具体公司、产品或技术，必须提供相关背景和证据
3. 如果声明有时间信息，必须判断是否合理
4. 检查声明中是否有夸大、误导或不准确的信息
5. 验证数据、数字、版本号等具体信息
6. 给出严格的可信度评分（0-100），只有完全可信才能给高分
7. 指出任何可疑、需要进一步验证或错误的地方

评分标准：
- 90-100：完全可信，有确凿证据支持
- 70-89：基本可信，但需要进一步验证
- 50-69：可信度一般，存在疑问
- 30-49：可信度较低，存在明显问题
- 0-29：不可信，存在严重错误或误导

返回格式：
{{
    "is_true": true/false,
    "confidence": 0-100,
    "reasoning": "详细验证理由，包括证据和疑点",
    "sources": ["来源1", "来源2"],
    "notes": "额外说明和警告"
}}"""
            
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个严格的事实核查员，对信息真实性要求极高"},
                    {"role": "user", "content": verification_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            
            logger.info(f"验证结果: {result_text[:100]}...")
            
            return self._parse_verification_result(result_text)
            
        except Exception as e:
            logger.error(f"验证声明失败: {str(e)}")
            return {
                "is_true": None,
                "confidence": 0,
                "reasoning": f"验证失败: {str(e)}",
                "sources": [],
                "method": "none"
            }
    
    def check_freshness(self, content: str, topic: str, timestamp: datetime = None) -> Dict:
        """
        检查内容的新鲜度（增强版，使用豆包 Web 搜索，更严格）
        
        Args:
            content: 内容文本
            topic: 话题
            timestamp: 内容时间戳
        
        Returns:
            新鲜度检查结果
        """
        try:
            logger.info("检查内容新鲜度（严格模式）...")
            
            if timestamp:
                age = (datetime.now() - timestamp).total_seconds() / 3600
                
                if age < 1:
                    time_freshness = "最新"
                    time_score = 100
                elif age < 24:
                    time_freshness = "今日"
                    time_score = 95
                elif age < 48:
                    time_freshness = "近2天"
                    time_score = 85
                elif age < 72:
                    time_freshness = "近3天"
                    time_score = 70
                elif age < 168:
                    time_freshness = "近一周"
                    time_score = 50
                elif age < 720:
                    time_freshness = "近一月"
                    time_score = 30
                else:
                    time_freshness = "较旧"
                    time_score = 10
                
                time_reasoning = f"内容发布于 {age:.1f} 小时前"
            else:
                time_freshness = "未知"
                time_score = 50
                time_reasoning = "无时间戳信息，无法判断时效性"
            
            content_freshness = self._analyze_content_freshness(content, topic)
            
            if self.web_searcher.api_key:
                logger.info("使用豆包 Web 检查新鲜度（多轮验证）")
                
                web_freshness_results = []
                
                for i in range(2):
                    logger.info(f"进行第 {i+1} 轮新鲜度验证...")
                    web_freshness = self.web_searcher.check_freshness_with_search(topic, content)
                    
                    if web_freshness.get('score', 0) > 0:
                        web_freshness_results.append(web_freshness)
                        logger.info(f"第 {i+1} 轮新鲜度检查成功，评分: {web_freshness.get('score', 0)}")
                
                if web_freshness_results:
                    avg_web_score = sum(r.get('score', 0) for r in web_freshness_results) / len(web_freshness_results)
                    all_search_results = []
                    
                    for result in web_freshness_results:
                        all_search_results.extend(result.get('search_results', []))
                    
                    is_fresh = all(r.get('is_fresh') for r in web_freshness_results)
                    
                    final_score = (time_score * 0.25 + avg_web_score * 0.55 + content_freshness['score'] * 0.20)
                    
                    if final_score >= 85:
                        fresh_level = "最新"
                    elif final_score >= 70:
                        fresh_level = "较新"
                    elif final_score >= 50:
                        fresh_level = "一般"
                    else:
                        fresh_level = "过时"
                    
                    if is_fresh and avg_web_score >= 85:
                        reasoning = f"多源验证一致，内容非常新鲜（{len(web_freshness_results)} 轮验证）"
                    elif is_fresh and avg_web_score >= 70:
                        reasoning = f"多源验证基本一致，内容较新（{len(web_freshness_results)} 轮验证）"
                    elif not is_fresh:
                        reasoning = f"多源验证发现内容过时或信息陈旧（{len(web_freshness_results)} 轮验证）"
                    else:
                        reasoning = f"多源验证结果不一致，需要人工审核（{len(web_freshness_results)} 轮验证）"
                    
                    return {
                        'is_fresh': is_fresh,
                        'freshness_level': fresh_level,
                        'score': final_score,
                        'time_freshness': time_freshness,
                        'time_score': time_score,
                        'content_freshness': content_freshness,
                        'web_freshness': web_freshness_results,
                        'reasoning': f"时间新鲜度：{time_reasoning}，内容新鲜度：{content_freshness['reasoning']}，Web 搜索新鲜度：{reasoning}",
                        'method': 'multi_source_web_search',
                        'search_results': all_search_results,
                        'verification_count': len(web_freshness_results)
                    }
            
            final_score = (time_score * 0.4 + content_freshness['score'] * 0.6)
            
            if final_score >= 80:
                is_fresh = True
                fresh_level = "最新"
            elif final_score >= 60:
                is_fresh = True
                fresh_level = "较新"
            elif final_score >= 40:
                is_fresh = False
                fresh_level = "一般"
            else:
                is_fresh = False
                fresh_level = "过时"
            
            return {
                "is_fresh": is_fresh,
                "freshness_level": fresh_level,
                "score": final_score,
                "time_freshness": time_freshness,
                "time_score": time_score,
                "content_freshness": content_freshness,
                "reasoning": f"时间新鲜度：{time_reasoning}，内容新鲜度：{content_freshness['reasoning']}（未启用 Web 搜索验证）",
                "method": "hybrid",
                "warning": "未启用 Web 搜索验证，时效性判断可能不准确"
            }
            
        except Exception as e:
            logger.error(f"检查新鲜度失败: {str(e)}")
            return {
                "is_fresh": None,
                "freshness_level": "未知",
                "score": 0,
                "time_freshness": "未知",
                "time_score": 0,
                "content_freshness": {},
                "reasoning": f"检查失败: {str(e)}",
                "method": "hybrid"
            }
    
    def cross_reference(self, topic: str, content: str) -> Dict:
        """
        交叉验证：通过 Web 搜索验证内容
        
        Args:
            topic: 主题
            content: 内容
        
        Returns:
            交叉验证结果
        """
        try:
            logger.info(f"交叉验证主题: {topic[:50]}...")
            
            if self.web_searcher.api_key:
                logger.info("使用豆包 Web 搜索进行交叉验证")
                search_results = self.web_searcher.search_topic(topic, max_results=5)
                
                if search_results:
                    logger.info(f"豆包搜索找到 {len(search_results)} 条相关结果")
                    
                    search_summary = "\n".join([
                        f"- {result.get('title', '')}: {result.get('summary', '')[:100]}"
                        for result in search_results[:3]
                    ])
                    
                    cross_ref_prompt = f"""你是一个科技新闻交叉验证员。

任务：通过以下搜索结果验证内容

主题：{topic}
内容：{content[:800]}

搜索结果：
{search_summary}

要求：
1. 对比内容与搜索结果的一致性
2. 指出任何矛盾或可疑之处
3. 提供额外的背景信息
4. 给出可信度评分（0-100）

返回格式：
{{
    "is_consistent": true/false,
    "confidence": 0-100,
    "known_facts": ["已知事实1", "已知事实2"],
    "contradictions": ["矛盾1", "矛盾2"],
    "additional_context": "额外背景信息",
    "reasoning": "验证理由",
    "search_results": {search_results[:3]}
}}"""
                    
                    if not self.client:
                        return {
                            "is_consistent": None,
                            "confidence": 50,
                            "known_facts": [],
                            "contradictions": [],
                            "additional_context": "",
                            "reasoning": "未配置 API Key，无法验证",
                            "method": "none"
                        }
                    
                    response = self.client.chat.completions.create(
                        model=DEEPSEEK_MODEL,
                        messages=[
                            {"role": "system", "content": "你是一个科技新闻交叉验证员"},
                            {"role": "user", "content": cross_ref_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=800
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    logger.info(f"交叉验证结果: {result_text[:100]}...")
                    
                    parsed_result = self._parse_cross_ref_result(result_text)
                    parsed_result['search_results'] = search_results
                    parsed_result['method'] = 'web_search'
                    
                    return parsed_result
            
            if not self.client:
                return {
                    "is_consistent": None,
                    "confidence": 0,
                    "known_facts": [],
                    "contradictions": [],
                    "additional_context": "",
                    "reasoning": "未配置 API Key，无法验证",
                    "method": "none"
                }
            
            cross_ref_prompt = f"""你是一个科技新闻交叉验证员。

任务：通过你的知识库验证以下内容

主题：{topic}
内容：{content[:800]}

要求：
1. 使用你的知识库搜索相关信息
2. 对比内容与已知信息的一致性
3. 指出任何矛盾或可疑之处
4. 提供额外的背景信息
5. 给出可信度评分（0-100）

返回格式：
{{
    "is_consistent": true/false,
    "confidence": 0-100,
    "known_facts": ["已知事实1", "已知事实2"],
    "contradictions": ["矛盾1", "矛盾2"],
    "additional_context": "额外背景信息",
    "reasoning": "验证理由"
}}"""
            
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个科技新闻交叉验证员"},
                    {"role": "user", "content": cross_ref_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            
            return self._parse_cross_ref_result(result_text)
            
        except Exception as e:
            logger.error(f"交叉验证失败: {str(e)}")
            return {
                "is_consistent": None,
                "confidence": 0,
                "known_facts": [],
                "contradictions": [],
                "additional_context": "",
                "reasoning": f"验证失败: {str(e)}",
                "method": "none"
            }
    
    def comprehensive_check(self, topic: str, content: str, timestamp: datetime = None) -> Dict:
        """
        综合检查：真实性、时效性、一致性（使用豆包 Web 搜索，严格模式）
        
        Args:
            topic: 主题
            content: 内容
            timestamp: 时间戳
        
        Returns:
            综合检查结果
        """
        logger.info("开始综合检查（严格模式）...")
        
        truth_check = self.verify_claim(content)
        freshness_check = self.check_freshness(content, topic, timestamp)
        consistency_check = self.cross_reference(topic, content)
        
        truth_score = truth_check.get("confidence", 0)
        freshness_score = freshness_check.get("score", 0)
        consistency_score = consistency_check.get("confidence", 0)
        
        overall_score = (
            truth_score * 0.35 +
            freshness_score * 0.45 +
            consistency_score * 0.20
        )
        
        is_pass = overall_score >= 70
        
        if overall_score >= 90:
            recommendation = "✅ 内容质量优秀，强烈推荐发布"
            quality_level = "优秀"
        elif overall_score >= 80:
            recommendation = "✅ 内容质量良好，推荐发布"
            quality_level = "良好"
        elif overall_score >= 70:
            recommendation = "⚠️ 内容质量达标，可以发布，但建议人工审核"
            quality_level = "达标"
        elif overall_score >= 60:
            recommendation = "❌ 内容质量一般，不建议发布，需要修改"
            quality_level = "一般"
        elif overall_score >= 50:
            recommendation = "❌ 内容质量较差，不建议发布，需要大幅修改"
            quality_level = "较差"
        else:
            recommendation = "❌ 内容质量很差，绝对不能发布"
            quality_level = "很差"
        
        improvement_suggestions = []
        
        if truth_score < 70:
            improvement_suggestions.append("真实性不足：建议重新核实事实，添加更多可靠来源")
        if freshness_score < 70:
            improvement_suggestions.append("时效性不足：建议更新内容，添加最新信息")
        if consistency_score < 70:
            improvement_suggestions.append("一致性不足：建议检查内容逻辑，确保信息一致")
        
        if truth_score < 50:
            improvement_suggestions.append("警告：内容可能包含虚假信息，必须彻底核查")
        if freshness_score < 50:
            improvement_suggestions.append("警告：内容可能过时，建议重新获取最新资讯")
        
        result = {
            "overall_score": overall_score,
            "is_pass": is_pass,
            "quality_level": quality_level,
            "truth_check": truth_check,
            "freshness_check": freshness_check,
            "consistency_check": consistency_check,
            "recommendation": recommendation,
            "improvement_suggestions": improvement_suggestions,
            "score_breakdown": {
                "truth_score": truth_score,
                "freshness_score": freshness_score,
                "consistency_score": consistency_score,
                "weights": {
                    "truth": 0.35,
                    "freshness": 0.45,
                    "consistency": 0.20
                }
            }
        }
        
        logger.info(f"综合检查完成，总分: {overall_score:.1f}, 质量等级: {quality_level}, 是否通过: {is_pass}")
        
        return result
    
    def _parse_verification_result(self, text: str) -> Dict:
        """解析验证结果"""
        try:
            import json
            result = json.loads(text)
            return result
        except:
            return {
                "is_true": None,
                "confidence": 50,
                "reasoning": text,
                "sources": [],
                "method": "none"
            }
    
    def _parse_cross_ref_result(self, text: str) -> Dict:
        """解析交叉验证结果"""
        try:
            import json
            result = json.loads(text)
            return result
        except:
            return {
                "is_consistent": None,
                "confidence": 50,
                "known_facts": [],
                "contradictions": [],
                "additional_context": text,
                "reasoning": "",
                "method": "none"
            }
