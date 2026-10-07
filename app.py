from flask import Flask, request, jsonify, send_from_directory, session, redirect
import json
import os
from werkzeug.utils import secure_filename
from cat_match_v2 import match_catyuan


app = Flask(__name__)

# =========================
# 管理员登录配置
# =========================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "local-development-secret"
)

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "请在本地设置你的密码"
)


DATA_FILE = "cats_detail.json"
IMAGE_FOLDER = "images"


if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)



# 首页文件

@app.route("/")
def index():

    return send_from_directory(
        ".",
        "index.html"
    )

# =========================
# 管理员后台登录
# =========================

@app.route("/admin")
def admin_page():

    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    return send_from_directory(
        ".",
        "admin.html"
    )


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":

        return send_from_directory(
            ".",
            "admin_login.html"
        )

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if (
        username == ADMIN_USERNAME
        and password == ADMIN_PASSWORD
    ):

        session["admin_logged_in"] = True

        return redirect("/admin")

    return """
    <script>
        alert("用户名或密码错误");
        window.location.href = "/admin_login";
    </script>
    """


@app.route("/admin_logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect("/")



# 静态文件

@app.route("/<path:path>")
def static_files(path):

    return send_from_directory(
        ".",
        path
    )




# 获取猫咪数据

@app.route("/api/cats")
def get_cats():


    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        cats=json.load(f)


    return jsonify(cats)

# =========================
# 地图区域坐标 API
# =========================

MAP_AREAS_FILE = "map_areas.json"


@app.route("/api/map_areas", methods=["GET"])
def get_map_areas():

    if not os.path.exists(MAP_AREAS_FILE):

        return jsonify({})

    with open(
        MAP_AREAS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        map_areas = json.load(f)

    return jsonify(map_areas)


@app.route("/api/map_areas", methods=["POST"])
def save_map_areas():

    map_areas = request.json

    if map_areas is None:
        return jsonify({
            "status": "error",
            "message": "没有收到地图数据"
        }), 400

    with open(
        MAP_AREAS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            map_areas,
            f,
            ensure_ascii=False,
            indent=4
        )

    return jsonify({
        "status": "success"
    })



from werkzeug.utils import secure_filename
# 上传图片

@app.route(
    "/api/upload",
    methods=["POST"]
)
def upload():


    file = request.files["file"]


    filename = secure_filename(
        file.filename
    )


    save_path = os.path.join(
        IMAGE_FOLDER,
        filename
    )


    file.save(save_path)


    return jsonify(
        {
            "status":"success",
            "filename":filename
        }
    )
# 添加猫咪

@app.route("/api/add_cat", methods=["POST"])
def add_cat():

    import time

    total_start = time.perf_counter()

    print("\n==============================")
    print("🐱 开始新增猫咪")
    print("==============================")

    # ① 接收前端数据
    step_start = time.perf_counter()

    new_cat = request.json

    print(
        f"① 接收猫咪数据："
        f"{time.perf_counter() - step_start:.3f} 秒"
    )

    # ② 读取猫咪数据库
    step_start = time.perf_counter()

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        cats = json.load(f)

    print(
        f"② 读取 cats_detail.json："
        f"{time.perf_counter() - step_start:.3f} 秒"
    )

    # ③ 分配 ID
    step_start = time.perf_counter()

    if cats:
        new_cat["id"] = max(
            item["id"] for item in cats
        ) + 1
    else:
        new_cat["id"] = 1

    print(
        f"③ 分配 ID："
        f"{time.perf_counter() - step_start:.3f} 秒"
    )

    # ④ 《猫苑》自动匹配
    step_start = time.perf_counter()

    print("④ 开始进行《猫苑》匹配……")

    new_cat["猫苑评价"] = match_catyuan(new_cat)

    print(
        f"④ 《猫苑》匹配完成："
        f"{time.perf_counter() - step_start:.3f} 秒"
    )

    # ⑤ 加入数据库
    step_start = time.perf_counter()

    cats.append(new_cat)

    print(
        f"⑤ 加入猫咪数据库："
        f"{time.perf_counter() - step_start:.3f} 秒"
    )

    # ⑥ 写回 JSON
    step_start = time.perf_counter()

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            cats,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"⑥ 写入 cats_detail.json："
        f"{time.perf_counter() - step_start:.3f} 秒"
    )

    # ⑦ 总耗时
    total_time = (
        time.perf_counter()
        - total_start
    )

    print(
        f"🐱 新增猫咪完成！"
        f"总耗时：{total_time:.3f} 秒"
    )

    print("==============================\n")

    return jsonify({
        "status": "success",
        "id": new_cat["id"]
    })

@app.route("/api/delete_cat/<int:cat_id>", methods=["DELETE"])
def delete_cat(cat_id):

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        cats = json.load(f)

    cats = [
        cat
        for cat in cats
        if cat["id"] != cat_id
    ]

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            cats,
            f,
            ensure_ascii=False,
            indent=4
        )

    return jsonify({
        "status": "success"
    })

# =========================
# 修改猫咪信息
# =========================

@app.route(
    "/api/update_cat/<int:cat_id>",
    methods=["PUT"]
)
def update_cat(cat_id):

    data = request.json

    if data is None:
        return jsonify({
            "status": "error",
            "message": "没有收到猫咪数据"
        }), 400

    # 读取猫咪数据库
    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        cats = json.load(f)

    # 查找猫咪
    target_cat = None

    for cat in cats:

        if cat["id"] == cat_id:

            target_cat = cat
            break

    if target_cat is None:

        return jsonify({
            "status": "error",
            "message": "没有找到这只猫咪"
        }), 404

    # 更新基本信息
    fields = [
        "名字",
        "活动区域",
        "性格",
        "常见行为",
        "毛色",
        "体型",
        "发现地点",
        "备注"
    ]

    for field in fields:

        if field in data:

            target_cat[field] = data[field]

    # 重新匹配《猫苑》
    print(
        f"🐱 正在重新匹配猫咪："
        f"{target_cat.get('名字', '未命名')}"
    )

    target_cat["猫苑评价"] = match_catyuan(
        target_cat
    )

    # 保存数据库
    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            cats,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"🐱 猫咪修改完成："
        f"{target_cat.get('名字', '未命名')}"
    )

    return jsonify({
        "status": "success",
        "id": cat_id
    })

# =========================
# 重新匹配全部猫咪
# =========================

@app.route(
    "/api/rematch_all",
    methods=["POST"]
)
def rematch_all():

    try:

        # 读取猫咪数据库
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            cats = json.load(f)

        print("开始重新匹配所有猫咪")
        print("猫咪数量：", len(cats))

        # 逐只重新匹配
        for index, cat in enumerate(cats, start=1):

            print(
                f"正在匹配第 {index} 只猫："
                f"{cat.get('名字', '未命名')}"
            )

            cat["猫苑评价"] = match_catyuan(cat)

            print(
                f"第 {index} 只猫匹配完成"
            )

        # 保存
        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                cats,
                f,
                ensure_ascii=False,
                indent=4
            )

        print("所有猫咪重新匹配完成")

        return jsonify(
            {
                "status": "success",
                "count": len(cats)
            }
        )

    except Exception as e:

        import traceback

        print("重新匹配失败！")
        print("错误：", e)

        traceback.print_exc()

        return jsonify(
            {
                "status": "error",
                "message": str(e)
            }
        ), 500

if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )