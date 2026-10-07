from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ========= 模型 =========

MODEL_PATH = r"C:\Users\20693\.cache\modelscope\models\AI-ModelScope--bge-small-zh-v1.5\snapshots\master"

model = SentenceTransformer(MODEL_PATH)

# ========= 特征定义 =========

FEATURES = {

    "亲人":
    "喜欢和人相处，喜欢被摸，依恋人，陪伴人",

    "活泼":
    "喜欢玩耍，跳跃，跑动，好动",

    "聪明":
    "聪慧，机灵，会观察，会学习",

    "善捕":
    "抓老鼠，抓虫子，捕猎，驱赶动物",

    "喜欢爬高":
    "喜欢爬树，登高，待在高处",

    "晒太阳":
    "喜欢晒太阳，睡觉，躺着休息",

    "忠守":
    "守在人身边，不离开，依守",

    "勇敢":
    "敢于驱赶动物，保护领地"
}
# ========= 特征向量 =========

feature_names = list(FEATURES.keys())

feature_vectors = model.encode(
    list(FEATURES.values()),
    normalize_embeddings=True
)
def understand_cat(cat):

    text = ""

    if cat.get("性格"):
        text += cat["性格"] + " "

    if cat.get("常见行为"):
        text += cat["常见行为"]

    print("正在理解：", text)

    vec = model.encode(
        [text],
        normalize_embeddings=True
    )

    sims = cosine_similarity(
        vec,
        feature_vectors
    )[0]

    result = []

    for i, score in enumerate(sims):

        if score > 0.35:

            result.append({
                "特征": feature_names[i],
                "相似度": float(score)
            })

    result.sort(
        key=lambda x:x["相似度"],
        reverse=True
    )

    return result