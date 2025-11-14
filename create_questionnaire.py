import csv
import json
import os
import hashlib
from pathlib import Path
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 定义6个定性评估维度 (基于scoring_principles.md)
QUALITATIVE_DIMENSIONS = [
    {
        "name": "accuracy",
        "display_name": "准确性 (Accuracy)",
        "description": "评估回答的相关性和准确性,是否直接回答了用户的问题",
        "question": """请评价该回答的准确性(1-4分):
1分 (POOR): 回答与问题严重不相关或信息严重不准确
2分 (FAIR): 回答部分相关但准确性有明显问题,或相关性和准确性都一般
3分 (GOOD): 回答高度相关且准确性良好,或高度准确且相关性良好
4分 (EXCELLENT): 回答高度相关且高度准确,直接回答了用户问题且信息可靠"""
    },
    {
        "name": "naturalness",
        "display_name": "自然度 (Naturalness)",
        "description": "衡量广告插入是否破坏了对话的流畅性和自然性",
        "question": """请评价该回答的自然度(1-4分):
1分 (HIGHLY_DISRUPTIVE): 广告严重打断对话流程,有强烈的"跳出感",显得非常生硬
2分 (MODERATELY_DISRUPTIVE): 广告明显打断阅读流程,有较强的"跳出感",回答显得有些生硬
3分 (SLIGHTLY_DISRUPTIVE): 广告造成轻微打断,有轻微"跳出感",对自然性影响较小
4分 (SEAMLESS): 广告自然融入对话,无打断感,保持了对话的自然真实性"""
    },
    {
        "name": "personality",
        "display_name": "个性化 (Personality)",
        "description": "评估聊天机器人在‘帮助用户’和‘推销产品’两个维度的表现",
        "question": """请评价该回答的个性化表现(1-4分):
1分 (UNACCEPTABLE): 过度以产品为中心,忽视用户需求
2分 (NEEDS_IMPROVEMENT): 部分偏离用户需求,转向产品推广
3分 (SATISFACTORY): 主要以用户为中心,有温和的产品提及
4分 (EXEMPLARY): 完全以用户为中心,很少或没有产品推广"""
    },
    {
        "name": "trust",
        "display_name": "信任度 (Trust)",
        "description": "衡量用户对整个回答的可信度和公正性的感知",
        "question": """请评价该回答的信任度(1-4分):
1分 (NOT_CREDIBLE): 可信度差,明显的偏见,用户会认为内容被商业动机驱动
2分 (SOMEWHAT_CREDIBLE): 可信度一般但有明显偏见问题,用户会怀疑存在商业动机
3分 (CREDIBLE): 可信度良好,偏见最小,用户总体上信任内容
4分 (HIGHLY_CREDIBLE): 可信度很高,无偏见感知,用户完全信任内容"""
    },
    {
        "name": "notice_products",
        "display_name": "广告注意度 (Ad Notice)",
        "description": "模拟用户是否会注意到回答中的产品或品牌,以及对其的态度",
        "question": """请评价用户对该回答中广告的注意度和态度(1-4分):
1分 (NOTICEABLE_NEGATIVE): 用户注意到产品/品牌且反应负面,感觉广告侵入性强、不可信
2分 (NOT_NOTICEABLE): 用户不会注意到任何产品、品牌或赞助内容
3分 (NOTICEABLE_NEUTRAL): 用户注意到产品/品牌但态度中立,既不特别积极也不消极
4分 (NOTICEABLE_POSITIVE): 用户清楚注意到产品/品牌且反应积极,认为推荐有价值且有帮助"""
    },
    {
        "name": "click_products",
        "display_name": "广告点击意愿 (Ad Click)",
        "description": "模拟用户是否会点击回答中的产品或品牌链接",
        "question": """请评价用户点击该回答中广告链接的可能性(1-4分):
1分 (NOT_NOTICEABLE): 用户不会注意到任何赞助链接
2分 (BARELY_NOTICEABLE): 用户可能勉强注意到赞助链接(由于位置不佳、展示不明显等)
3分 (NOTICEABLE_NOT_CLICKED): 用户注意到赞助链接但不太可能点击(由于相关性差、吸引力弱等)
4分 (NOTICEABLE_CLICKED): 用户清楚注意到赞助链接且很可能点击(相关性强、吸引力高)"""
    }
]

def translate_text(client, text, is_query=True):
    """使用LLM翻译文本为地道中文"""
    if is_query:
        prompt = f"""请将以下英文问题翻译成地道的中文,保持原意和格式:

{text}

要求:
1. 翻译要地道自然,符合中国人的表达习惯
2. 不要改变原问题的含义
3. 保持原有的格式和标点
4. 直接输出翻译结果,不要有其他说明"""
    else:
        prompt = f"""请将以下英文回答翻译成地道的中文,保持原意、格式和结构:

{text}

要求:
1. 翻译要地道自然,符合中国人的阅读习惯
2. 保持原文的段落结构和格式
3. 保持链接URL不变
4. 保持列表、标题等格式不变
5. 直接输出翻译结果,不要有其他说明"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一个专业的翻译助手,擅长将英文翻译成地道的中文。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"翻译出错: {e}")
        return text

def generate_hash(text):
    """生成文本的哈希值作为唯一标识"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]

def load_benchmark_output(output_dir, methods=['GIR-R', 'Ad-Chat']):
    """从benchmark输出目录加载结果

    Args:
        output_dir: 输出目录路径
        methods: 要比较的方法列表

    Returns:
        按query组织的数据字典
    """
    print(f"读取benchmark输出目录: {output_dir}")

    # 读取results.json获取所有response
    results_path = Path(output_dir) / "results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"找不到 results.json: {results_path}")

    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print(f"加载了 {len(results)} 个method|dataset|batch组合")

    # 读取evaluation_result.json获取评分
    eval_result_path = Path(output_dir) / "evaluation_result.json"
    eval_results = []
    if eval_result_path.exists():
        with open(eval_result_path, 'r', encoding='utf-8') as f:
            eval_results = json.load(f)
        print(f"加载了 {len(eval_results)} 条评估结果")

    # 按query组织数据: {query: {method: {batch_id: {content, scores, ...}}}}
    query_data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    # 解析results.json
    # 格式: {"method|dataset|batch": [{prompt, category, solution, content, product, price}, ...]}
    for key, items in results.items():
        # 解析key: "Ad-Chat|MT-Human|0"
        parts = key.split('|')
        if len(parts) != 3:
            continue

        method, dataset, batch = parts

        if method not in methods:
            continue

        for item in items:
            query = item.get('prompt', '').strip()
            if not query:
                continue

            batch_key = f"{dataset}|{batch}"

            # 存储response和metadata
            query_data[query][method][batch_key] = {
                'content': item.get('content', ''),
                'category': item.get('category', ''),
                'dataset': dataset,
                'batch': batch,
                'product': item.get('product', {}),
                'price': item.get('price', {}),
                'scores': {}
            }

    # 解析evaluation_result.json
    # 格式: [[[method, dataset, batch, metric, category, query, [content, product]], score], ...]
    for eval_item in eval_results:
        if not isinstance(eval_item, list) or len(eval_item) != 2:
            continue

        metadata, score = eval_item

        if not isinstance(metadata, list) or len(metadata) < 6:
            continue

        method = metadata[0]
        dataset = metadata[1]
        batch = metadata[2]
        metric = metadata[3]
        category = metadata[4]
        query = metadata[5]

        if method not in methods:
            continue

        batch_key = f"{dataset}|{batch}"

        # 添加评分
        if query in query_data and method in query_data[query]:
            if batch_key in query_data[query][method]:
                query_data[query][method][batch_key]['scores'][metric] = score

    print(f"\n检测到 {len(query_data)} 个unique queries")

    # 检查每个query在不同batch的出现情况
    for query in list(query_data.keys()):
        for method in list(query_data[query].keys()):
            num_batches = len(query_data[query][method])
            if num_batches > 1:
                print(f"  Query '{query[:50]}...' 在 {method} 中出现了 {num_batches} 次")

    return dict(query_data)

def select_best_batch(query_data, strategy='max_diff'):
    """为每个query选择最佳batch

    当同一个query在多个batch中出现时,选择最佳的那个batch

    Args:
        query_data: 按query组织的数据 {query: {method: {batch_key: {...}}}}
        strategy: 选择策略
            - 'max_diff': 选择两个方法差异最大的batch
            - 'first': 选择第一个batch
            - 'last': 选择最后一个batch

    Returns:
        去重后的数据 {query: {method: {...}}}
    """
    deduped_data = {}

    print(f"\n应用batch选择策略: {strategy}")

    for query, methods_data in query_data.items():
        # 获取所有batch的keys (假设不同method有相同的batch)
        all_batch_keys = set()
        for method, batches in methods_data.items():
            all_batch_keys.update(batches.keys())

        if len(all_batch_keys) == 1:
            # 只有一个batch,直接使用
            deduped_data[query] = {}
            for method, batches in methods_data.items():
                batch_key = list(batches.keys())[0]
                deduped_data[query][method] = batches[batch_key]
        else:
            # 多个batch,需要选择
            print(f"  Query '{query[:50]}...' 有 {len(all_batch_keys)} 个batch: {list(all_batch_keys)}")

            if strategy == 'first':
                # 选择第一个(按字典序)
                selected_batch = sorted(all_batch_keys)[0]
                print(f"    -> 选择 batch {selected_batch} (首个)")

            elif strategy == 'last':
                # 选择最后一个(按字典序)
                selected_batch = sorted(all_batch_keys)[-1]
                print(f"    -> 选择 batch {selected_batch} (最后)")

            elif strategy == 'max_diff':
                # 选择两个方法评分差异最大的batch
                max_diff = -1
                selected_batch = sorted(all_batch_keys)[0]

                for batch_key in all_batch_keys:
                    # 计算这个batch在不同方法间的差异
                    try:
                        # 获取所有方法在这个batch的评分
                        batch_scores = {}
                        for method, batches in methods_data.items():
                            if batch_key in batches:
                                scores = batches[batch_key].get('scores', {})
                                batch_scores[method] = scores

                        # 只在有多个方法且都有评分时计算差异
                        if len(batch_scores) >= 2:
                            methods_list = list(batch_scores.keys())
                            method1_scores = batch_scores[methods_list[0]]
                            method2_scores = batch_scores[methods_list[1]]

                            # 计算6个定性维度的平均差异
                            diffs = []
                            for dim in ['accuracy', 'naturalness', 'personality',
                                       'trust', 'notice_products', 'click_products']:
                                score1 = method1_scores.get(dim, 0)
                                score2 = method2_scores.get(dim, 0)

                                if isinstance(score1, (int, float)) and isinstance(score2, (int, float)):
                                    diffs.append(abs(score1 - score2))

                            avg_diff = sum(diffs) / len(diffs) if diffs else 0

                            if avg_diff > max_diff:
                                max_diff = avg_diff
                                selected_batch = batch_key
                    except Exception as e:
                        print(f"      警告: batch {batch_key} 计算差异出错: {e}")
                        continue

                print(f"    -> 选择 batch {selected_batch} (avg_diff={max_diff:.3f})")

            else:
                selected_batch = sorted(all_batch_keys)[0]

            # 保存选中的batch数据
            deduped_data[query] = {}
            for method, batches in methods_data.items():
                if selected_batch in batches:
                    deduped_data[query][method] = batches[selected_batch]

    return deduped_data

def filter_by_response_length(query_data, min_length=100, max_length=2000):
    """根据回答长度筛选queries

    Args:
        query_data: 按query组织的数据 {query: {method: {...}}}
        min_length: 最小字符数
        max_length: 最大字符数

    Returns:
        筛选后的数据
    """
    filtered_data = {}

    print(f"\n应用回答长度筛选: {min_length}-{max_length}字符")

    for query, methods_data in query_data.items():
        valid = True

        # 检查所有方法的回答长度
        for method, data in methods_data.items():
            content = data.get('content', '')
            length = len(content)

            if length < min_length or length > max_length:
                print(f"  跳过Query '{query[:50]}...': {method}回答长度{length}不在范围内")
                valid = False
                break

        if valid:
            filtered_data[query] = methods_data

    print(f"长度筛选后保留 {len(filtered_data)}/{len(query_data)} 个queries")
    return filtered_data

def score_query_feasibility(client, query, responses, methods):
    """使用LLM评估问题的人工评测可行性

    评估标准:
    1. 回答长度是否适中(已在前面筛选)
    2. 问题是否超出本科生常识认知
    3. 是否适合本科生评判
    4. 是否是本科生大概率会问的问题

    Args:
        client: OpenAI客户端
        query: 问题文本
        responses: 各方法的回答 {method: {content: ...}}
        methods: 方法列表

    Returns:
        float: 综合得分 (0-10)
    """
    # 构造评估prompt
    responses_text = ""
    for method in methods:
        content = responses[method].get('content', '')
        responses_text += f"\n【{method}的回答】\n{content}\n"

    prompt = f"""你是一位教育评估专家。请评估以下问题和回答是否适合交给**中国本科生**进行人工评测。

注意:评估对象是中国本科生,需要考虑中国本土文化背景和认知水平。涉及国外文化、地理、品牌、习俗等中国学生不熟悉的内容会影响评分。

【问题】
{query}

【回答】
{responses_text}

请从以下5个维度评分(每项0-10分):

1. **问题真实性** (0-10分) [关键筛选维度]
   - 10分: 真实用户提出的自然问题,有明确的信息需求
   - 7分: 问题真实但表述略显正式/生硬
   - 4分: 问题看起来像是测试用例,但还算自然
   - 0分: 明显是任务型对话测试/学术研究的人造问题(如"请改写这段话使语气更友好"、"评估系统回复的语气"),或包含明显的系统/任务指令

2. **常识认知适配性** (0-10分)
   - 10分: 问题完全在中国本科生常识范围内,无需专业背景,不涉及国外特定文化内容
   - 5分: 需要一些专业知识或涉及部分国外内容,但中国本科生基本能理解
   - 0分: 涉及深奥专业知识或大量国外特定文化/地理/品牌等,超出中国本科生认知

3. **评判可行性** (0-10分)
   - 10分: 评判标准清晰,中国本科生能客观评价回答质量,不需要了解国外背景
   - 5分: 部分评判标准主观,需要一定判断力,或需要了解部分国外背景
   - 0分: 评判标准模糊,或需要深入了解国外文化/市场,中国本科生难以做出合理判断

4. **问题代表性** (0-10分)
   - 10分: 典型的日常问题,中国本科生大概率会问,贴近中国生活场景
   - 5分: 较为常见的问题,中国本科生可能会问
   - 0分: 冷门或特殊场景问题,或主要针对国外用户的问题

5. **回答差异性** (0-10分)
   - 10分: 两个回答有明显差异,易于比较
   - 5分: 回答有一定差异
   - 0分: 两个回答几乎相同,难以比较

请按以下JSON格式输出(只输出JSON,不要其他内容):
{{
    "问题真实性": <分数>,
    "常识认知适配性": <分数>,
    "评判可行性": <分数>,
    "问题代表性": <分数>,
    "回答差异性": <分数>,
    "综合评分": <平均分>,
    "简短理由": "<一句话说明>"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位专业的教育评估专家,擅长评估问题的教学和评测价值。请严格按JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        result_text = response.choices[0].message.content.strip()

        # 解析JSON
        # 移除可能的markdown代码块标记
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        result = json.loads(result_text)

        return {
            "score": result.get("综合评分", 0),
            "details": result
        }

    except Exception as e:
        print(f"  评分出错: {e}")
        return {
            "score": 5.0,  # 默认中等分数
            "details": {"error": str(e)}
        }

def rank_queries_by_feasibility(client, query_data, methods, top_k=20):
    """对所有queries进行可行性评分并排序

    Args:
        client: OpenAI客户端
        query_data: 按query组织的数据
        methods: 方法列表
        top_k: 保留前k个

    Returns:
        排序后的queries列表
    """
    print(f"\n开始对 {len(query_data)} 个queries进行人工评测可行性评分...")

    scored_queries = []

    for i, (query, methods_data) in enumerate(query_data.items(), 1):
        print(f"\n[{i}/{len(query_data)}] 评分Query: {query[:60]}...")

        # 评分
        score_result = score_query_feasibility(client, query, methods_data, methods)

        # 获取数据集和类别信息(从第一个方法获取)
        first_method = methods[0]
        dataset = methods_data[first_method].get('dataset', 'Unknown')
        category = methods_data[first_method].get('category', 'Unknown')

        scored_queries.append({
            "query": query,
            "data": methods_data,
            "score": score_result["score"],
            "score_details": score_result["details"],
            "dataset": dataset,
            "category": category
        })

        print(f"  综合得分: {score_result['score']:.2f}")
        print(f"  数据集: {dataset}, 类别: {category}")
        if "简短理由" in score_result["details"]:
            print(f"  理由: {score_result['details']['简短理由']}")

    # 先过滤掉问题真实性得分过低的queries
    print(f"\n{'='*80}")
    print("应用问题真实性过滤...")

    authentic_queries = []
    filtered_out = []

    for item in scored_queries:
        authenticity_score = item['score_details'].get('问题真实性', 5.0)
        if authenticity_score >= 5.0:  # 真实性得分需要>=5分
            authentic_queries.append(item)
        else:
            filtered_out.append(item)
            print(f"  过滤: [真实性:{authenticity_score:.1f}分] {item['query'][:60]}...")

    print(f"\n真实性筛选: 保留 {len(authentic_queries)}/{len(scored_queries)} 个queries")

    if filtered_out:
        print(f"以下{len(filtered_out)}个问题因真实性不足被过滤:")
        for item in filtered_out[:5]:  # 只显示前5个
            print(f"  - {item['query'][:80]}...")
            if '简短理由' in item['score_details']:
                print(f"    理由: {item['score_details']['简短理由']}")

    # 按综合得分降序排序
    authentic_queries.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n{'='*80}")
    print(f"评分完成! 前{top_k}个最适合的queries:")
    for i, item in enumerate(authentic_queries[:top_k], 1):
        auth_score = item['score_details'].get('问题真实性', 0)
        print(f"  {i}. [综合:{item['score']:.2f}|真实性:{auth_score:.1f}] [{item['dataset']}|{item['category']}] {item['query'][:45]}...")

    # 保存评分详情
    return authentic_queries[:top_k]

def deduplicate_queries(rows, strategy='max_diff'):
    """去除重复的query

    Args:
        rows: CSV行列表
        strategy: 去重策略
            - 'first': 保留第一次出现
            - 'max_diff': 保留GIR-R和Ad-Chat差异最大的

    Returns:
        去重后的行列表
    """
    from collections import defaultdict

    # 按query分组
    query_groups = defaultdict(list)
    for row in rows:
        query = row.get('Query', '').strip()
        query_groups[query].append(row)

    # 统计重复情况
    duplicates = {q: items for q, items in query_groups.items() if len(items) > 1}
    if duplicates:
        print(f"\n发现 {len(duplicates)} 个重复的query:")
        for query, items in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
            ranks = [item.get('Rank', '?') for item in items]
            print(f"  - Query在Rank {ranks} 中重复出现 ({len(items)}次)")

    # 根据策略选择保留哪一行
    deduped_rows = []
    for query, items in query_groups.items():
        if len(items) == 1:
            # 没有重复,直接保留
            deduped_rows.append(items[0])
        else:
            # 有重复,根据策略选择
            if strategy == 'first':
                # 保留第一个
                selected = items[0]
                print(f"    -> 保留Rank {selected.get('Rank')} (首次出现)")
            elif strategy == 'max_diff':
                # 选择差异最大的
                max_diff = -1
                selected = items[0]

                for item in items:
                    try:
                        # 计算6个定性维度的平均绝对差异
                        diffs = []
                        for dim in ['accuracy', 'naturalness', 'personality', 'trust',
                                   'notice_products', 'click_products']:
                            girr_key = f'GIR-R_{dim}'
                            adchat_key = f'Ad-Chat_{dim}'

                            if girr_key in item and adchat_key in item:
                                girr_score = float(item.get(girr_key, 0) or 0)
                                adchat_score = float(item.get(adchat_key, 0) or 0)
                                diffs.append(abs(girr_score - adchat_score))

                        avg_diff = sum(diffs) / len(diffs) if diffs else 0

                        if avg_diff > max_diff:
                            max_diff = avg_diff
                            selected = item
                    except (ValueError, TypeError) as e:
                        print(f"    警告: Rank {item.get('Rank')} 计算差异时出错: {e}")
                        continue

                print(f"    -> 保留Rank {selected.get('Rank')} (平均差异={max_diff:.3f})")
            else:
                selected = items[0]

            deduped_rows.append(selected)

    # 按原始Rank排序
    deduped_rows.sort(key=lambda x: int(x.get('Rank', 999)))

    return deduped_rows

def create_questionnaire_structure(benchmark_output_dir, output_base_dir, methods=['GIR-R', 'Ad-Chat']):
    """创建问卷调查文件夹结构

    Args:
        benchmark_output_dir: benchmark输出目录路径
        output_base_dir: 问卷输出目录
        methods: 要比较的方法列表
    """

    # 初始化OpenAI客户端
    print("初始化翻译服务...")
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('BASE_URL')
    client = OpenAI(api_key=api_key, base_url=base_url)

    # 从benchmark输出加载数据
    print(f"\n加载benchmark结果...")
    query_data_raw = load_benchmark_output(benchmark_output_dir, methods=methods)

    # 为每个query选择最佳batch (去重)
    query_data = select_best_batch(query_data_raw, strategy='max_diff')

    print(f"\n最终处理 {len(query_data)} 个unique queries")

    # 步骤1: 根据回答长度筛选
    query_data = filter_by_response_length(query_data, min_length=100, max_length=2000)

    # 步骤2: 使用LLM评分并排序,选择前20个
    top_queries = rank_queries_by_feasibility(client, query_data, methods, top_k=20)

    print(f"\n最终选择 {len(top_queries)} 个queries生成问卷")

    # 创建主输出目录
    os.makedirs(output_base_dir, exist_ok=True)

    # 哈希表映射
    hash_mapping = {}

    # 保存评分详情
    scoring_details_path = os.path.join(output_base_dir, "feasibility_scores.json")
    scoring_details = []
    for item in top_queries:
        scoring_details.append({
            "query": item["query"],
            "score": item["score"],
            "details": item["score_details"],
            "dataset": item["dataset"],
            "category": item["category"]
        })
    with open(scoring_details_path, 'w', encoding='utf-8') as f:
        json.dump(scoring_details, f, ensure_ascii=False, indent=2)
    print(f"\n可行性评分详情已保存: {scoring_details_path}")

    # 生成问题来源汇总文件
    source_summary_path = os.path.join(output_base_dir, "questions_source_summary.csv")
    with open(source_summary_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['问题编号', '数据集', '类别', '可行性得分', '问题(前100字符)'])
        for i, item in enumerate(top_queries, 1):
            writer.writerow([
                f'Query_{str(i).zfill(2)}',
                item['dataset'],
                item['category'],
                f"{item['score']:.2f}",
                item['query'][:100] + ('...' if len(item['query']) > 100 else '')
            ])
    print(f"问题来源汇总已保存: {source_summary_path}")

    # 处理每个query
    for i, item in enumerate(top_queries, 1):
        query = item["query"]
        method_responses = item["data"]
        print(f"\n{'='*80}")
        print(f"处理第 {i}/{len(top_queries)} 个query...")

        # 检查是否有所有需要的方法的响应
        if not all(m in method_responses for m in methods):
            print(f"  跳过: 缺少某些方法的响应")
            continue

        query_en = query

        # 获取responses
        responses = {}
        for method in methods:
            responses[method] = method_responses[method]

        # 创建query文件夹
        folder_name = f"Query_{str(i).zfill(2)}"
        folder_path = os.path.join(output_base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        print(f"创建文件夹: {folder_name}")

        # 翻译query
        print("翻译Query...")
        query_zh = translate_text(client, query_en, is_query=True)

        # 翻译responses并生成哈希
        response_hashes = {}
        response_translations = {}

        for method in methods:
            print(f"翻译{method} Response...")
            response_en = responses[method]['content']
            response_zh = translate_text(client, response_en, is_query=False)

            # 生成哈希值
            resp_hash = generate_hash(response_en)
            response_hashes[method] = resp_hash
            response_translations[method] = response_zh

            # 保存哈希映射
            hash_mapping[resp_hash] = {
                "method": method,
                "query_rank": str(i),
                "response_en": response_en[:100] + "...",
                "response_zh": response_zh[:100] + "..."
            }

        # 1. 保存query.txt
        with open(os.path.join(folder_path, "query.txt"), 'w', encoding='utf-8') as f:
            f.write(f"数据集: {item['dataset']}\n")
            f.write(f"类别: {item['category']}\n")
            f.write(f"可行性得分: {item['score']:.2f}/10\n")
            f.write("="*80 + "\n\n")
            f.write(f"原始问题:\n{query_en}\n\n")
            f.write(f"中文翻译:\n{query_zh}\n")

        # 2. 保存response文件
        for method in methods:
            resp_hash = response_hashes[method]
            resp_zh = response_translations[method]
            with open(os.path.join(folder_path, f"response_{resp_hash}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"回答编号: {resp_hash}\n\n")
                f.write(f"{resp_zh}\n")

        # 3. 保存6个定性维度的得分CSV
        metrics_csv_path = os.path.join(folder_path, "evaluation_scores.csv")
        with open(metrics_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            # 创建表头
            header = ['评测维度'] + [f'{m}得分' for m in methods] + ['差值(第一项-第二项)']
            writer.writerow(header)

            # 只保留6个定性维度
            for dim in QUALITATIVE_DIMENSIONS:
                metric_name = dim['name']

                # 获取各方法的分数
                scores = []
                for method in methods:
                    score = responses[method].get('scores', {}).get(metric_name, 'N/A')
                    scores.append(score)

                # 计算差值(如果有两个方法)
                if len(scores) == 2:
                    try:
                        diff = float(scores[0]) - float(scores[1])
                        writer.writerow([dim['display_name']] + scores + [f"{diff:.2f}"])
                    except (ValueError, TypeError):
                        writer.writerow([dim['display_name']] + scores + ['N/A'])
                else:
                    writer.writerow([dim['display_name']] + scores + ['N/A'])

        # 4. 生成定性评估问题文件
        qualitative_path = os.path.join(folder_path, "qualitative_evaluation.txt")
        with open(qualitative_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("定性评估问卷\n")
            f.write("="*80 + "\n\n")
            f.write(f"问题: {query_zh}\n\n")
            f.write("="*80 + "\n\n")

            # 为每个回答生成评估问题
            for method in methods:
                resp_hash = response_hashes[method]
                resp_text = response_translations[method]

                f.write(f"【回答编号: {resp_hash}】\n")
                f.write(f"{resp_text}\n\n")
                f.write("-"*80 + "\n")
                f.write(f"请对上述回答(编号:{resp_hash})进行以下6个维度的评分:\n\n")

                for j, dim in enumerate(QUALITATIVE_DIMENSIONS, 1):
                    f.write(f"{j}. {dim['display_name']}\n")
                    f.write(f"   {dim['description']}\n\n")
                    f.write(f"   {dim['question']}\n")
                    f.write(f"   您的评分: _____ 分\n\n")

                f.write("="*80 + "\n\n")

        # 5. 生成问卷星格式的CSV
        questionnaire_csv_path = os.path.join(folder_path, "questionnaire_format.csv")
        with open(questionnaire_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            # 表头
            header = ['问题']
            for idx, method in enumerate(methods):
                resp_hash = response_hashes[method]
                label = chr(65 + idx)  # A, B, C, ...
                header.append(f'回答{label}(编号:{resp_hash})')

            for dim in QUALITATIVE_DIMENSIONS:
                for idx in range(len(methods)):
                    label = chr(65 + idx)
                    header.append(f'{label}-{dim["display_name"]}(1-4分)')

            writer.writerow(header)

            # 数据行
            data_row = [query_zh]
            for method in methods:
                resp_zh = response_translations[method]
                data_row.append(resp_zh[:500] + "...")

            for _ in QUALITATIVE_DIMENSIONS:
                for _ in methods:
                    data_row.append('')  # 空白供填写

            writer.writerow(data_row)

        print(f"✓ Query {i} 处理完成")

    # 保存全局哈希映射表
    hash_mapping_path = os.path.join(output_base_dir, "hash_mapping.json")
    with open(hash_mapping_path, 'w', encoding='utf-8') as f:
        json.dump(hash_mapping, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 哈希映射表已保存: {hash_mapping_path}")

    # 生成总的问卷说明文件
    readme_path = os.path.join(output_base_dir, "README.txt")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("问卷调查文件夹结构说明\n")
        f.write("="*80 + "\n\n")
        f.write(f"总共包含 {len(top_queries)} 个精选query的调查问卷\n")
        f.write(f"比较的方法: {', '.join(methods)}\n\n")
        f.write("选择标准:\n")
        f.write("1. 回答长度筛选: 100-2000字符\n")
        f.write("2. LLM可行性评分,从以下维度评估(针对中国本科生):\n")
        f.write("   - 问题真实性: 是否是真实用户问题,而非任务型测试问题 [关键筛选,<5分将被过滤]\n")
        f.write("   - 常识认知适配性: 是否在中国本科生常识范围内,不涉及过多国外文化内容\n")
        f.write("   - 评判可行性: 中国本科生能否客观评价回答质量\n")
        f.write("   - 问题代表性: 是否是中国本科生大概率会问的问题\n")
        f.write("   - 回答差异性: 两个回答是否有明显差异\n")
        f.write("3. 过滤问题真实性<5分的问题(过滤任务型/人造问题)\n")
        f.write("4. 选择综合得分最高的前20个query\n\n")
        f.write("每个Query文件夹包含以下文件:\n")
        f.write("1. query.txt - 问题的原文、中文翻译、数据集来源和类别信息\n")
        f.write(f"2. response_[哈希值].txt - {len(methods)}个方法的回答(带哈希编号)\n")
        f.write("3. evaluation_scores.csv - 该query在6个定性维度的得分\n")
        f.write("4. qualitative_evaluation.txt - 定性评估问卷(人工打分用)\n")
        f.write("5. questionnaire_format.csv - 问卷星格式的CSV文件\n\n")
        f.write("根目录文件说明:\n")
        f.write("- questions_source_summary.csv: 所有问题的来源汇总(数据集、类别、得分)\n")
        f.write("- feasibility_scores.json: 每个问题的详细可行性评分\n")
        f.write("- hash_mapping.json: 回答哈希值与方法的对应关系\n")
        f.write("- README.txt: 本说明文件\n\n")
        f.write("定性评估的6个维度:\n")
        for i, dim in enumerate(QUALITATIVE_DIMENSIONS, 1):
            f.write(f"{i}. {dim['display_name']}: {dim['description']}\n")
        f.write("\n")
        f.write("注意事项:\n")
        f.write("- 所有问题均已针对**中国本科生**的认知水平和文化背景进行筛选\n")
        f.write("- 问题来源于不同数据集和类别,详见questions_source_summary.csv\n")
        f.write("- 每个回答都有唯一的哈希编号,用于匿名化和溯源\n")
        f.write(f"- hash_mapping.json 文件记录了哈希值与方法({'/'.join(methods)})的对应关系\n")
        f.write(f"- feasibility_scores.json 文件记录了每个query的可行性评分详情\n")
        f.write("- 评分采用1-4分制,分数越高表示该维度表现越好\n")
        f.write("- 6个维度基于LAAJ Evaluator的评分原则定义\n")
        f.write("- 数据来源: 自动从benchmark输出目录加载,经过去重、长度筛选和LLM可行性评分\n")

    print(f"\n✓ README说明文件已保存: {readme_path}")
    print(f"\n{'='*80}")
    print(f"所有文件生成完成!")
    print(f"输出目录: {output_base_dir}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='从benchmark输出创建问卷调查文件夹结构')
    parser.add_argument('benchmark_output', type=str,
                       help='Benchmark输出目录路径')
    parser.add_argument('--output', type=str,
                       required=True,
                       help='问卷输出目录路径')
    parser.add_argument('--methods', type=str,
                       nargs='+',
                       default=['GIR-R', 'Ad-Chat'],
                       help='要比较的方法列表 (默认: GIR-R Ad-Chat)')

    args = parser.parse_args()

    create_questionnaire_structure(args.benchmark_output, args.output, methods=args.methods)
