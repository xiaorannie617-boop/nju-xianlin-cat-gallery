import pandas as pd
import re
import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# 1. 模型
# ============================================================

MODEL_PATH = r"C:\Users\20693\.cache\modelscope\models\AI-ModelScope--bge-small-zh-v1.5\snapshots\master"

model = SentenceTransformer(MODEL_PATH)



# ============================================================
# 2. 读取《猫苑》
# ============================================================

maoyuan = pd.read_excel(
    "Maoyuan_new_database.xlsx"
)


print(
    "《猫苑》记录:",
    len(maoyuan)
)



# ============================================================
# 3. 拆句
# ============================================================

sentences = []


for _, row in maoyuan.iterrows():

    text = str(row["原文"])

    parts = re.split(
        r"[。！？；\n]",
        text
    )


    for p in parts:

        p = p.strip()

        if len(p) >= 8:

            sentences.append(
                {
                    "编号": row["编号"],
                    "原文": p
                }
            )


print(
    "《猫苑》句子:",
    len(sentences)
)



# ============================================================
# 4. 预计算向量
# ============================================================


print("正在生成《猫苑》向量...")


yuan_vectors = model.encode(
    [
        x["原文"]
        for x in sentences
    ],
    normalize_embeddings=True
)



# ============================================================
# 5. 自动生成现代特征
# ============================================================


def build_features(cat):

    features = []


    # -------------------------
    # 性格
    # -------------------------

    personality = str(
        cat.get("性格","")
    )


    if "亲人" in personality:

        features.append(
            {
                "类型":"性格",

                "现代描述":
                "猫喜欢与人亲近，愿意接受人的接触，性情驯熟，对人友好。"
            }
        )


    elif personality:

        features.append(
            {
                "类型":"性格",

                "现代描述":
                f"猫表现出{personality}的性格特点。"
            }
        )



    # -------------------------
    # 行为
    # -------------------------

    behavior = str(
        cat.get("常见行为","")
    )


    parts = re.split(
        r"[，,、；;]",
        behavior
    )


    for b in parts:

        b=b.strip()

        if not b:
            continue


        if (
            "赶" in b
            or "虫" in b
            or "鼠" in b
            or "蝙蝠" in b
        ):


            features.append(
                {
                    "类型":
                    "捕猎行为",

                    "现代描述":
                    "猫能够主动捕捉、驱赶或消灭其他动物，帮助人类减少动物造成的危害。"
                }
            )


        elif (
            "抱" in b
            or "摸" in b
        ):


            features.append(
                {
                    "类型":
                    "亲人行为",

                    "现代描述":
                    "猫愿意接受人的拥抱和抚摸，表现出亲近人的性情。"
                }
            )


        elif (
            "臭" in b
            or "味" in b
        ):


            features.append(
                {
                    "类型":
                    "身体特征",

                    "现代描述":
                    "猫的口腔或身体可能存在明显气味。"
                }
            )


        else:

            features.append(
                {
                    "类型":
                    "行为",

                    "现代描述":
                    b
                }
            )



    # -------------------------
    # 毛色
    # -------------------------

    fur=str(
        cat.get("毛色","")
    )


    if fur:


        features.append(
            {
                "类型":
                "毛色",

                "现代描述":
                f"猫的毛色是{fur}。"
            }
        )


    return features




# ============================================================
# 6. 匹配《猫苑》
# ============================================================


def match_maoyuan(feature):


    vector=model.encode(
        [
            feature["现代描述"]
        ],
        normalize_embeddings=True
    )


    scores=cosine_similarity(
        vector,
        yuan_vectors
    )[0]



    result=[]


    for i,score in enumerate(scores):

        result.append(
            {
                "编号":
                sentences[i]["编号"],

                "原文":
                sentences[i]["原文"],

                "语义分数":
                round(float(score),4)
            }
        )


    result.sort(
        key=lambda x:x["语义分数"],
        reverse=True
    )


    return result[:3]



# ============================================================
# 7. 单只猫生成档案
# ============================================================


def generate_cat_profile(cat):


    profile={}


    profile["基础资料"]=cat



    features=build_features(cat)


    profile["现代观察"]=[]



    for f in features:


        matches=match_maoyuan(f)


        item={

            "类型":
            f["类型"],


            "现代描述":
            f["现代描述"],


            "猫苑依据":
            matches

        }


        profile["现代观察"].append(
            item
        )


    return profile




# ============================================================
# 8. 测试猫
# ============================================================


cat={

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



profile=generate_cat_profile(cat)



print("\n生成完成\n")


print(
    json.dumps(
        profile,
        ensure_ascii=False,
        indent=4
    )
)



# ============================================================
# 9. 保存
# ============================================================


with open(
    "cat_encyclopedia.json",
    "w",
    encoding="utf-8"
) as f:


    json.dump(
        profile,
        f,
        ensure_ascii=False,
        indent=4
    )



print(
    "\n已生成：cat_encyclopedia.json"
)