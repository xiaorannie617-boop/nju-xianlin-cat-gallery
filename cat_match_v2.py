import re
import numpy as np
from openpyxl import load_workbook

from sentence_transformers import SentenceTransformer


# ============================================================
# 1. 模型
# ============================================================

import os

LOCAL_MODEL_PATH = r"C:\Users\20693\.cache\modelscope\models\AI-ModelScope--bge-small-zh-v1.5\snapshots\master"

if os.path.exists(LOCAL_MODEL_PATH):
    print("使用本地《猫苑》匹配模型：", LOCAL_MODEL_PATH)
    MODEL_PATH = LOCAL_MODEL_PATH
else:
    print("本地模型不存在，使用在线模型：BAAI/bge-small-zh-v1.5")
    MODEL_PATH = "BAAI/bge-small-zh-v1.5"

model = None


# ============================================================
# 2. 读取新版《猫苑》
# ============================================================

wb = load_workbook("Maoyuan_new_database.xlsx", read_only=True, data_only=True)
ws = wb.active

headers = [cell.value for cell in ws[1]]

rows = []
for row in ws.iter_rows(min_row=2, values_only=True):
    rows.append(dict(zip(headers, row)))

wb.close()

print("《猫苑》原始记录：", len(rows))


# ============================================================
# 3. 拆成句子
# ============================================================

sentences = []

for row in rows:

    text = str(row["原文"])

    parts = re.split(
        r"[。！？；\n]",
        text
    )

    for part in parts:

        part = part.strip()

        if len(part) >= 8:

            sentences.append({
                "编号": row["编号"],
                "原文": part
            })


print("《猫苑》拆句后：", len(sentences))

# ============================================================
# 3.5 预先计算《猫苑》所有句子的语义向量
# ============================================================

model = None
maoyuan_vectors = None


def initialize_model():
    global model
    global maoyuan_vectors

    if model is not None:
        return

    print("正在加载《猫苑》匹配模型……")
    model = SentenceTransformer(MODEL_PATH)

    print("正在预计算《猫苑》句子向量……")

    maoyuan_texts = [
        item["原文"]
        for item in sentences
    ]

    maoyuan_vectors = model.encode(
        maoyuan_texts,
        normalize_embeddings=True
    )

    print("《猫苑》句子向量预计算完成！")


# ============================================================
# 4. 给猫咪生成现代特征
# ============================================================

def build_features(cat):

    features = []

    # personality
    personality = str(cat.get("性格", "")).strip()

    if personality:

        # ============================================================
        # 性格正负方向
        # ============================================================

        personality_text = (
                str(cat.get("性格", "")) +
                " " +
                str(cat.get("常见行为", ""))
        )

        personality_direction = personality_direction_evidence(
            personality_text
        )

        # ============================================================
        # 构建性格特征
        # ============================================================

        if "亲人" in personality:
            feature = (
                "猫喜欢与人亲近，"
                "愿意接受人的接触，"
                "性情驯熟，"
                "对人友好，"
                "喜欢和人相处。"
            )
        else:
            feature = (
                f"猫的性格是{personality}，"
                f"表现出明显的{personality}性情。"
            )

        # 加入常见行为中的性格信息
        behavior = str(cat.get("常见行为", "")).strip()

        if behavior:
            behavior_parts = re.split(
                r"[，,、；;。]",
                behavior
            )

            personality_related_parts = []

            for part in behavior_parts:
                part = part.strip()

                if len(part) < 2:
                    continue

                part_direction = personality_direction_evidence(part)

                if (
                        part_direction["positive_words"]
                        or part_direction["negative_words"]
                ):
                    personality_related_parts.append(part)

            if personality_related_parts:
                feature += (
                        " 与性格有关的常见行为："
                        + "；".join(personality_related_parts)
                        + "。"
                )

        # 明确告诉后面的匹配程序：
        # 这个猫有哪些正向性格、哪些负向性格
        if personality_direction["positive_words"]:
            feature += (
                    " 正向性格特征："
                    + "、".join(
                personality_direction["positive_words"]
            )
                    + "。"
            )

        if personality_direction["negative_words"]:
            feature += (
                    " 负向性格特征："
                    + "、".join(
                personality_direction["negative_words"]
            )
                    + "。"
            )

        features.append({
            "类型": "性格",
            "特征": feature
        })

    # ========================================================
    # 2. 常见行为
    # ========================================================

    behavior = str(
        cat.get("常见行为", "")
    ).strip()

    if behavior:

        behavior_parts = re.split(
            r"[，,、；;。]",
            behavior
        )

        for part in behavior_parts:

            part = part.strip()

            if len(part) < 2:
                continue

            # ------------------------------------------------
            # 捕猎 / 驱赶 / 除害
            # ------------------------------------------------

            if (
                "赶走虫子" in part
                or "赶走" in part
                or "驱赶" in part
                or "捕捉" in part
                or (
                    "捕" in part
                    and (
                        "鼠" in part
                        or "虫" in part
                        or "动物" in part
                    )
                )
            ):

                features.append({

                    "类型": "捕猎行为",

                    "特征": (
                        "猫能够主动捕捉、驱赶或消灭其他动物，"
                        "尤其能够处理会危害人类生活的害物，"
                        "这种行为能够帮助人类减少动物造成的危害。"
                    )

                })

            # ------------------------------------------------
            # 抱、摸、抚摸
            # ------------------------------------------------

            elif (
                "抱" in part
                or "摸" in part
                or "抚摸" in part
            ):

                features.append({

                    "类型": "亲人行为",

                    "特征": (
                        "猫愿意接受人的拥抱和抚摸，"
                        "不抗拒人与猫的身体接触，"
                        "表现出亲近人的性情。"
                    )

                })

            # ------------------------------------------------
            # 身体气味
            # ------------------------------------------------

            elif (
                "臭" in part
                or "气味" in part
                or "味道" in part
                or "口臭" in part
                or "牙臭" in part
            ):

                features.append({

                    "类型": "身体特征",

                    "特征": (
                        "猫的口腔、牙齿或身体可能存在明显气味。"
                    )

                })

            # ------------------------------------------------
            # 其他行为
            # ------------------------------------------------

            else:

                features.append({

                    "类型": "其他行为",

                    "特征": part

                })

    # ========================================================
    # 3. 毛色
    # ========================================================

    fur = str(
        cat.get("毛色", "")
    ).strip()

    if fur:

        features.append({

            "类型": "毛色",

            "特征":
                f"猫的毛色是{fur}。"

        })

    # ========================================================
    # 注意：
    #
    # 体型不会加入现代特征
    # ========================================================

    return features


# ============================================================
# 5. 捕猎行为证据
# ============================================================

def behavior_evidence(text):

    score = 0
    reasons = []

    # --------------------------------------------------------
    # 1. 反向 / 否定行为
    # --------------------------------------------------------

    negative_patterns = [

        "反以导鼠",
        "导鼠",
        "不捕鼠",
        "不捕",
        "未捕鼠",
        "未捕",
        "无所捕",
        "非捕",
        "不能捕"

    ]

    found_negative = []

    for word in negative_patterns:

        if word in text:

            found_negative.append(word)

    if found_negative:

        score -= 5

        reasons.append(

            "存在反向/否定行为：" +

            "、".join(found_negative)

        )

    # --------------------------------------------------------
    # 2. 猫 / 貍明确实施捕猎行为
    # --------------------------------------------------------

    cat_action_patterns = [

        r"(猫|貍).{0,5}(捕|食|搜|降|驱|除|执)",

        r"(猫|貍).{0,8}(善于|善).{0,5}(捕|食|搜|降|驱|除|执)",

        r"(猫|貍).{0,5}(以|来).{0,5}(捕|食|搜|降|驱|除|执)",

        r"(猫|貍).{0,5}(方|正在).{0,5}(捕|食)"

    ]

    explicit_cat_action = False

    for pattern in cat_action_patterns:

        if re.search(
            pattern,
            text
        ):

            explicit_cat_action = True

            score += 4

            reasons.append(
                "猫/貍明确实施行为"
            )

            break

    # --------------------------------------------------------
    # 3. 具体行为词
    # --------------------------------------------------------

    if explicit_cat_action:

        action_words = [

            "捕",
            "捕鼠",
            "捕虫",
            "食鼠",
            "食虫",
            "搜穴",
            "降鼠",
            "除害",
            "驱除",
            "驱鼠",
            "除鼠",
            "鼠耗",
            "执鼠"

        ]

        found_actions = []

        for word in action_words:

            if word in text:

                found_actions.append(word)

        if found_actions:

            score += min(
                len(found_actions),
                2
            )

            reasons.append(

                "行为词：" +

                "、".join(found_actions)

            )

    # --------------------------------------------------------
    # 4. 人利用猫
    # --------------------------------------------------------

    human_use_patterns = [

        "多取猫",
        "取猫",
        "挖去",
        "以警",
        "利用猫",
        "用猫",
        "使猫"

    ]

    found_human_use = []

    for pattern in human_use_patterns:

        if pattern in text:

            found_human_use.append(pattern)

    if found_human_use:

        score -= 5

        reasons.append(

            "疑似人利用猫：" +

            "、".join(found_human_use)

        )

    return score, reasons

# ============================================================
# 正负性格词库
# ============================================================

POSITIVE_PERSONALITY_WORDS = [
    "亲人",
    "亲近人",
    "亲近",
    "黏人",
    "粘人",
    "温顺",
    "温和",
    "驯良",
    "驯熟",
    "乖",
    "友好",
    "善媚",
    "和柔",
    "恋旧",
    "依守",
    "依人",
    "亲昵",
    "不怕人",
    "喜欢人",
    "喜欢亲近",
    "善解人意",
    "讨人喜欢",
    "讨喜"
]


NEGATIVE_PERSONALITY_WORDS = [
    "挠人",
    "抓人",
    "抓伤人",
    "咬人",
    "咬伤人",
    "凶",
    "凶猛",
    "凶狠",
    "攻击",
    "攻击人",
    "暴躁",
    "暴烈",
    "暴",
    "不驯",
    "不驯服",
    "桀骜",
    "桀骜不驯",
    "雄桀",
    "顽劣",
    "顽皮",
    "野",
    "野性",
    "怕人",
    "警惕",
    "易惊",
    "容易受惊",
    "惊",
    "没有猫德"
]


def personality_direction_evidence(text):
    """
    判断一段文字中是否存在正向 / 负向性格证据。

    返回：
        {
            "positive": 正向词数量,
            "negative": 负向词数量,
            "positive_words": [...],
            "negative_words": [...]
        }
    """

    if not text:
        return {
            "positive": 0,
            "negative": 0,
            "positive_words": [],
            "negative_words": []
        }

    text = str(text)

    positive_words = [
        word
        for word in POSITIVE_PERSONALITY_WORDS
        if word in text
    ]

    negative_words = [
        word
        for word in NEGATIVE_PERSONALITY_WORDS
        if word in text
    ]

    return {
        "positive": len(positive_words),
        "negative": len(negative_words),
        "positive_words": positive_words,
        "negative_words": negative_words
    }

def human_affection_evidence(text):

    score = 0
    reasons = []

    # --------------------------------------------------------
    # 强相关词
    # --------------------------------------------------------

    strong_words = [

        "驯良",
        "驯熟",
        "和柔",
        "善媚",
        "依守不离",
        "依恋",
        "恋旧",
        "解人意",
        "得人爱护"

    ]

    found_strong = []

    for word in strong_words:

        if word in text:

            found_strong.append(word)

    if found_strong:

        score += min(
            len(found_strong) * 2,
            6
        )

        reasons.append(

            "亲人/驯熟特征：" +

            "、".join(found_strong)

        )

    # --------------------------------------------------------
    # 一般相关词
    # --------------------------------------------------------

    normal_words = [

        "人意",
        "如人意",
        "爱护"

    ]

    found_normal = []

    for word in normal_words:

        if word in text:

            found_normal.append(word)

    if found_normal:

        score += min(
            len(found_normal),
            2
        )

        reasons.append(

            "人与猫关系：" +

            "、".join(found_normal)

        )

    # --------------------------------------------------------
    # 明显负面
    # --------------------------------------------------------

    negative_words = [

        "不驯",
        "暴戾",
        "咬人"

    ]

    found_negative = []

    for word in negative_words:

        if word in text:

            found_negative.append(word)

    if found_negative:

        score -= 3

        reasons.append(

            "可能不亲人：" +

            "、".join(found_negative)

        )

    return score, reasons


# ============================================================
# 7. 身体特征证据
# ============================================================

def body_feature_evidence(text):

    score = 0
    reasons = []

    # --------------------------------------------------------
    # 非常直接的气味表达
    # --------------------------------------------------------

    strong_words = [

        "猫牙臭",
        "牙臭",
        "口臭"

    ]

    found_strong = []

    for word in strong_words:

        if word in text:

            found_strong.append(word)

    if found_strong:

        score += 4

        reasons.append(

            "直接描述气味：" +

            "、".join(found_strong)

        )

    # --------------------------------------------------------
    # 一般“臭”
    # --------------------------------------------------------

    if "臭" in text:

        score += 2

        reasons.append(
            "出现“臭”"
        )

    return score, reasons


# ============================================================
# 8. 语境过滤
# ============================================================

def context_penalty(text):

    penalty = 0
    reasons = []

    # --------------------------------------------------------
    # 梦境 / 占卜
    # --------------------------------------------------------

    dream_words = [

        "梦猫",
        "梦见猫",
        "梦猫捕鼠",
        "梦中",
        "梦占"

    ]

    found_dream = []

    for word in dream_words:

        if word in text:

            found_dream.append(word)

    if found_dream:

        penalty -= 5

        reasons.append(

            "梦境/占卜语境：" +

            "、".join(found_dream)

        )

    # --------------------------------------------------------
    # 非真实猫
    # --------------------------------------------------------

    object_words = [

        "大铁猫",
        "石猫",
        "木猫",
        "铜猫",
        "泥猫"

    ]

    found_objects = []

    for word in object_words:

        if word in text:

            found_objects.append(word)

    if found_objects:

        penalty -= 5

        reasons.append(

            "非真实猫对象：" +

            "、".join(found_objects)

        )

    # --------------------------------------------------------
    # 超自然语境
    # --------------------------------------------------------

    supernatural_words = [

        "猫鬼",
        "猫精",
        "猫妖"

    ]

    found_supernatural = []

    for word in supernatural_words:

        if word in text:

            found_supernatural.append(word)

    if found_supernatural:

        penalty -= 5

        reasons.append(

            "超自然语境：" +

            "、".join(found_supernatural)

        )

    return penalty, reasons


# ============================================================
# 9. 单个特征召回候选
# ============================================================

def get_candidates(feature,feature_type,candidate_n=20):
    initialize_model()

    feature_vector = model.encode(
        [feature],
        normalize_embeddings=True
    )


    # --------------------------------------------------------
    # 现代特征向量
    # --------------------------------------------------------

    feature_vector = model.encode(

        [feature],

        normalize_embeddings=True

    )

    # --------------------------------------------------------
    # 《猫苑》句子
    # --------------------------------------------------------


    # --------------------------------------------------------
    # 《猫苑》向量
    # --------------------------------------------------------


    # --------------------------------------------------------
    # 语义相似度
    # --------------------------------------------------------

    similarities = np.dot(maoyuan_vectors, feature_vector[0])

    candidates = []

    # --------------------------------------------------------
    # 对所有句子评分
    # --------------------------------------------------------

    for i, score in enumerate(
        similarities
    ):

        text = sentences[i]["原文"]

        semantic_score = float(score)

        evidence_score = 0
        evidence_reasons = []

        # ----------------------------------------------------
        # 捕猎
        # ----------------------------------------------------

        if feature_type == "捕猎行为":

            (
                evidence_score,
                evidence_reasons
            ) = behavior_evidence(text)

        # ----------------------------------------------------
        # 亲人行为
        # ----------------------------------------------------

        elif feature_type == "亲人行为":

            (
                evidence_score,
                evidence_reasons
            ) = human_affection_evidence(text)

        # ----------------------------------------------------
        # 性格
        # ----------------------------------------------------

        # ----------------------------------------------------
        # 性格
        # ----------------------------------------------------

        elif feature_type == "性格":

            # 原有的亲人 / 驯熟证据继续保留
            (
                evidence_score,
                evidence_reasons
            ) = human_affection_evidence(text)

            # ------------------------------------------------
            # 现代猫咪的正负性格方向
            # ------------------------------------------------

            modern_direction = \
                personality_direction_evidence(feature)

            modern_positive = \
                modern_direction["positive_words"]

            modern_negative = \
                modern_direction["negative_words"]

            # ------------------------------------------------
            # 《猫苑》候选句子的正负性格方向
            # ------------------------------------------------

            candidate_direction = \
                personality_direction_evidence(text)

            candidate_positive = \
                candidate_direction["positive_words"]

            candidate_negative = \
                candidate_direction["negative_words"]

            # ------------------------------------------------
            # 正向性格匹配
            # ------------------------------------------------

            if (
                modern_positive
                and candidate_positive
            ):
                positive_bonus = min(
                    len(modern_positive),
                    len(candidate_positive)
                ) * 2.5

                evidence_score += positive_bonus

                evidence_reasons.append(
                    "正向性格匹配："
                    + "、".join(candidate_positive)
                )

            # ------------------------------------------------
            # 负向性格匹配
            # ------------------------------------------------

            if (
                modern_negative
                and candidate_negative
            ):
                negative_bonus = min(
                    len(modern_negative),
                    len(candidate_negative)
                ) * 3.5

                evidence_score += negative_bonus

                evidence_reasons.append(
                    "负向性格匹配："
                    + "、".join(candidate_negative)
                )

            # ------------------------------------------------
            # 性格方向冲突
            #
            # 例如：
            # 坏坏 = 亲人 + 爱挠人
            #
            # 候选 = 驯良、和柔、善媚
            #
            # 虽然语义上很像“亲人”，
            # 但是没有负向性格，因此应该降分。
            # ------------------------------------------------

            if (
                modern_negative
                and candidate_positive
                and not candidate_negative
            ):
                penalty -= 3.0

                evidence_reasons.append(
                    "性格方向冲突："
                    "猫咪存在负向性格，"
                    "但《猫苑》候选只有正向性格描述"
                )

            # ------------------------------------------------
            # 反向冲突
            #
            # 如果现代猫明确温顺，
            # 《猫苑》却明确描述不驯、凶、咬人，
            # 也应该降低分数。
            # ------------------------------------------------

            if (
                modern_positive
                and not modern_negative
                and candidate_negative
            ):
                penalty -= 2.5

                evidence_reasons.append(
                    "性格方向冲突："
                    "猫咪主要为正向性格，"
                    "但《猫苑》候选存在负向性格描述"
                )

        # ----------------------------------------------------
        # 其他
        # ----------------------------------------------------

        penalty, penalty_reasons = \
            context_penalty(text)

        # ----------------------------------------------------
        # 最终分数
        # ----------------------------------------------------

        final_score = (

            semantic_score * 10

            + evidence_score

            + penalty

        )

        candidates.append({

            "编号":
                sentences[i]["编号"],

            "原文":
                text,

            "语义分数":
                semantic_score,

            "辅助证据":
                evidence_score,

            "语境调整":
                penalty,

            "最终分数":
                final_score,

            "判断理由":
                evidence_reasons +
                penalty_reasons

        })

    # --------------------------------------------------------
    # 同编号先去重
    # --------------------------------------------------------

    best_by_id = {}

    for item in candidates:

        number = item["编号"]

        if number not in best_by_id:

            best_by_id[number] = item

    candidates = list(
        best_by_id.values()
    )

    # --------------------------------------------------------
    # 排序
    # --------------------------------------------------------

    candidates.sort(

        key=lambda x:
            x["最终分数"],

        reverse=True

    )

    return candidates[:candidate_n]


# ============================================================
# 10. 全局匹配
# ============================================================

def match_all_features(
    features
):

    # --------------------------------------------------------
    # 第一步：
    # 每个现代特征先召回候选
    # --------------------------------------------------------

    all_candidates = []

    for feature_index, item in enumerate(
        features
    ):

        feature_type = item["类型"]

        feature = item["特征"]

        candidates = get_candidates(
            feature,
            feature_type,
            candidate_n=20
        )

        for candidate in candidates:

         for candidate in candidates:

            candidate["特征序号"] = \
                feature_index + 1

            candidate["特征类型"] = \
                feature_type

            candidate["现代特征"] = \
                feature

            all_candidates.append(candidate)

    # --------------------------------------------------------
    # 第二步：
    # 全局按照最终分数排序
    # --------------------------------------------------------

    all_candidates.sort(

        key=lambda x:
            x["最终分数"],

        reverse=True

    )

    # --------------------------------------------------------
    # 第三步：
    # 全局分配
    #
    # 一个《猫苑》编号只能被一个现代特征使用
    #
    # 一个现代特征也只获得一个最终结果
    # --------------------------------------------------------

    used_maoyuan_ids = set()

    used_features = set()

    final_results = []

    for candidate in all_candidates:

        maoyuan_id = candidate["编号"]

        feature_index = candidate["特征序号"]

        # ----------------------------------------------------
        # 已经有特征占用了这个《猫苑》编号
        # ----------------------------------------------------

        if maoyuan_id in used_maoyuan_ids:

            continue

        # ----------------------------------------------------
        # 这个现代特征已经得到结果
        # ----------------------------------------------------

        if feature_index in used_features:

            continue

        # ----------------------------------------------------
        # 分配
        # ----------------------------------------------------

        used_maoyuan_ids.add(
            maoyuan_id
        )

        used_features.add(
            feature_index
        )

        final_results.append(
            candidate
        )

    # --------------------------------------------------------
    # 按现代特征顺序排列
    # --------------------------------------------------------

    final_results.sort(

        key=lambda x:
            x["特征序号"]

    )

    return final_results


# ============================================================
# 11. 网站调用接口
# ============================================================

def match_catyuan(cat):
    """
    给网站调用的《猫苑》匹配函数。

    输入：
        cat = 一只猫咪的信息字典

    输出：
        与这只猫咪现代特征对应的《猫苑》匹配结果
    """

    # 1. 根据猫咪资料生成现代特征
    features = build_features(cat)

    # 2. 进行全局语义匹配
    results = match_all_features(features)

    return results


# ============================================================
# 12. 测试猫咪：杉菜
#
# 只有直接运行本文件时才执行下面的测试。
# 被 app.py 导入时不会自动执行。
# ============================================================

if __name__ == "__main__":

    cat = {

        "名字":
            "杉菜",

        "活动区域":
            "宿舍7栋",

        "毛色":
            "狸白",

        "体型":
            "胖嘟嘟",

        "性格":
            "亲人",

        "常见行为":
            "会帮人类赶走虫子和蝙蝠，给抱抱给摸摸，就是嘴巴有点臭",

        "发现地点":
            "宿舍楼下",

        "备注":
            ""

    }

    # ========================================================
    # 自动生成现代特征
    # ========================================================

    features = build_features(cat)

    print("\n")
    print("=" * 80)
    print("猫咪：", cat["名字"])
    print("=" * 80)

    print("\n自动生成的现代特征：")

    for i, feature in enumerate(
        features,
        1
    ):

        print(
            f"{i}. {feature}"
        )

    # ========================================================
    # 全局匹配
    # ========================================================

    final_results = match_all_features(
        features
    )

    # ========================================================
    # 输出最终结果
    # ========================================================

    print("\n")
    print("=" * 80)
    print("最终匹配结果")
    print("=" * 80)

    for result in final_results:

        print("\n")

        print(
            "现代特征序号：",
            result["特征序号"]
        )

        print(
            "类型：",
            result["特征类型"]
        )

        print(
            "现代特征：",
            result["现代特征"]
        )

        print(
            "《猫苑》编号：",
            result["编号"]
        )

        print(
            "语义分数：",
            round(
                result["语义分数"],
                4
            )
        )

        print(
            "辅助证据：",
            result["辅助证据"]
        )

        print(
            "语境调整：",
            result["语境调整"]
        )

        print(
            "最终分数：",
            round(
                result["最终分数"],
                4
            )
        )

        print(
            "判断理由：",
            "；".join(
                result["判断理由"]
            )
        )

        print(
            "《猫苑》原文：",
            result["原文"]
        )

    # ========================================================
    # 测试结束
    # ========================================================

    print("\n")
    print("=" * 80)
    print("测试结束")
    print("=" * 80)