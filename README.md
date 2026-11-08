# 《猫苑》句向量冷启动加速
把两个 Python 文件放到当前 Render 图鉴仓库根目录，沿用现网的 Maoyuan_new_database.xlsx、模型和 Python 依赖。

1. 在本地已装好图鉴依赖的环境中，从仓库根目录运行 python build_maoyuan_vectors.py。
2. 确认出现 Validated，并把 cat_match_v2.py 和生成的 maoyuan_vectors.npz 一同提交到 Render 使用的仓库。检查 Git 是否忽略 .npz。
3. 重新部署后，在第一条真实匹配时检查 Render 日志。MAOYUAN_VECTOR_CACHE_HIT 表示已跳过整库编码。保留上一版 app.py 里的 CLOUD_MATCH_TIMING，用于比较首次和后续匹配。
4. 修改《猫苑》语料、模型权重或向量生成规则后重新生成缓存。生成端和 Render 应使用同一份模型权重。若使用 Hugging Face 模型，可在两边设置相同的 MAOYUAN_MODEL_REVISION 固定版本。若使用本地模型副本，MAOYUAN_MODEL_PATH 指向副本，两个环境使用相同的 MAOYUAN_MODEL_KEY 标识该模型版本。
5. 如果出现 MISS 或 INVALID，先检查缓存是否随部署发布、语料和模型配置是否一致。缺少或不匹配时会沿用低内存逐句计算路径。
