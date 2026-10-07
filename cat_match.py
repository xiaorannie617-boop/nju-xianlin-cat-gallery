import pandas as pd

CATYUAN_FILE = "Maoyuan_new_database.xlsx"


# =========================================================
# 现代猫咪特征 → 《猫苑》匹配规则
# =========================================================

FEATURE_RULES = {

    "亲人": {
        "aliases": [
            "亲人",
            "亲近人",
            "亲近人类",
            "黏人",
            "粘人",
            "喜欢人",
            "喜欢亲近人",
            "喜欢抱",
            "喜欢摸",
            "给抱抱",
            "给摸摸",
            "不怕人",
            "不怕生",
            "依赖人",
            "亲近主人",
            "喜欢主人"
        ],

        "keywords": [
            "和柔",
            "善媚",
            "依守",
            "恋旧",
            "灵驯",
            "解人意",
            "驯熟",
            "驯良"
        ]
    },


    "喜欢爬高": {
        "aliases": [
            "喜欢爬高",
            "爬高",
            "喜欢爬树",
            "爬树",
            "喜欢上树",
            "上树",
            "喜欢登高",
            "登高",
            "往高处爬",
            "喜欢往上爬",
            "往上爬"
        ],

        "keywords": [
            "善升",
            "上树",
            "登屋背",
            "攀",
            "登"
        ]
    },


    "晒太阳": {
        "aliases": [
            "晒太阳",
            "喜欢晒太阳",
            "晒日",
            "晒暖",
            "晒太阳取暖",
            "喜欢阳光",
            "喜欢晒"
        ],

        "keywords": [
            "日",
            "阳",
            "暖",
            "向阳"
        ]
    },


    "活泼": {
        "aliases": [
            "活泼",
            "好动",
            "爱玩",
            "喜欢玩",
            "调皮",
            "顽皮",
            "喜欢跳",
            "喜欢跑",
            "喜欢玩耍"
        ],

        "keywords": [
            "喜戏",
            "戏",
            "跳",
            "跃"
        ]
    },


    "聪明": {
        "aliases": [
            "聪明",
            "机灵",
            "聪慧",
            "有智慧",
            "会看人",
            "懂人意",
            "解人意"
        ],

        "keywords": [
            "慧",
            "智",
            "解人意"
        ]
    },


    "捕鼠": {
        "aliases": [
            "抓老鼠",
            "捉老鼠",
            "捕老鼠",
            "捕鼠",
            "抓鼠",
            "捉鼠",
            "会抓老鼠",
            "喜欢抓老鼠",
            "会捉老鼠"
        ],

        "keywords": [
            "捕鼠",
            "捕之",
            "鼠患",
            "鼠耗",
            "鼠害"
        ]
    }
}


# =========================================================
# 识别猫咪的现代特征
# =========================================================

def detect_features(cat):

    features = []

    # -----------------------------------------------------
    # 1. 从“性格”字段识别
    # -----------------------------------------------------

    personality = str(cat.get("性格", "")).strip()

    if personality:

        for feature, rule in FEATURE_RULES.items():

            # 如果性格直接就是“亲人”“活泼”等
            if personality == feature:

                if feature not in features:
                    features.append(feature)

                continue

            # 如果性格描述中包含别名
            for alias in rule["aliases"]:

                if alias in personality:

                    if feature not in features:
                        features.append(feature)

                    break


    # -----------------------------------------------------
    # 2. 从“常见行为”字段识别
    # -----------------------------------------------------

    behavior = str(cat.get("常见行为", "")).strip()

    print("猫咪常见行为：", behavior)

    if behavior:

        for feature, rule in FEATURE_RULES.items():

            for alias in rule["aliases"]:

                if alias in behavior:

                    print(
                        "行为识别：",
                        behavior,
                        "→",
                        feature,
                        "（命中：", alias, "）"
                    )

                    if feature not in features:
                        features.append(feature)

                    break


    return features


# =========================================================
# 给一条《猫苑》原文评分
# =========================================================

def score_text(text, feature):

    rule = FEATURE_RULES[feature]

    score = 0
    hit_keywords = []

    # -----------------------------------------------------
    # 关键词匹配
    # -----------------------------------------------------

    for keyword in rule["keywords"]:

        if keyword in text:

            if keyword not in hit_keywords:
                hit_keywords.append(keyword)

            score += 1


    # -----------------------------------------------------
    # 现代特征名称如果直接出现在原文中
    # 给一点额外分数
    # -----------------------------------------------------

    if feature in text:
        score += 3


    # -----------------------------------------------------
    # 特殊加分
    # 避免“日”“暖”等太宽泛的词造成大量无关匹配
    # -----------------------------------------------------

    if feature == "晒太阳":

        strong_words = [
            "晒",
            "日",
            "向阳",
            "日光",
            "阳光"
        ]

        for word in strong_words:

            if word in text:
                score += 1


    if feature == "捕鼠":

        strong_words = [
            "捕鼠",
            "捉鼠",
            "捕之",
            "鼠患",
            "鼠耗"
        ]

        for word in strong_words:

            if word in text:
                score += 2


    if feature == "喜欢爬高":

        strong_words = [
            "善升",
            "上树",
            "登屋背",
            "攀"
        ]

        for word in strong_words:

            if word in text:
                score += 2


    return score, hit_keywords


# =========================================================
# 匹配《猫苑》
# =========================================================

def match_catyuan(cat):

    print()
    print("======================================")
    print("开始匹配《猫苑》")
    print("猫咪：", cat.get("名字", ""))

    # -----------------------------------------------------
    # 读取数据库
    # -----------------------------------------------------

    df = pd.read_excel(CATYUAN_FILE)

    # -----------------------------------------------------
    # 自动识别现代特征
    # -----------------------------------------------------

    features = detect_features(cat)

    print("识别出的现代特征：", features)

    # 如果没有识别出来
    if not features:

        print("没有识别出可匹配的现代特征")

        return []


    # =====================================================
    # 每个现代特征，只选择一个最佳段落
    # =====================================================

    final_results = []

    used_texts = set()


    for feature in features:

        print()
        print("正在匹配特征：", feature)

        candidates = []

        # -------------------------------------------------
        # 遍历《猫苑》
        # -------------------------------------------------

        for _, row in df.iterrows():

            text = str(row.get("原文", "")).strip()

            if not text:
                continue


            # 评分
            score, hit_keywords = score_text(
                text,
                feature
            )


            # 没有命中关键词
            if score <= 0:
                continue


            # -------------------------------------------------
            # 尽量避免同一段文字被不同特征重复使用
            # -------------------------------------------------

            if text in used_texts:
                continue


            candidates.append({
                "现代特征": feature,
                "匹配关键词": ",".join(hit_keywords),
                "评分": score,
                "猫苑原文": text
            })


        # -------------------------------------------------
        # 按评分从高到低排序
        # -------------------------------------------------

        candidates.sort(
            key=lambda x: x["评分"],
            reverse=True
        )


        # -------------------------------------------------
        # 每个特征只取 1 条
        # -------------------------------------------------

        if candidates:

            best = candidates[0]

            final_results.append(best)

            used_texts.add(best["猫苑原文"])

            print(
                "找到最佳匹配：",
                best["评分"],
                best["猫苑原文"][:80]
            )

        else:

            print(
                "没有找到《猫苑》匹配段落"
            )


    # =====================================================
    # 最终结果
    # =====================================================

    print()
    print("最终匹配结果数量：", len(final_results))

    for item in final_results:

        print(
            " -",
            item["现代特征"],
            "→",
            item["评分"]
        )


    print("======================================")
    print()

    return final_results