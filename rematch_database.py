"""在网站目录运行：python rematch_database.py。先备份，再原子替换。"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from collections import Counter
from cat_match_v2 import rematch_cats


def stats(cats):
    texts = [e.get('原文', e.get('猫苑原文', '')) for cat in cats for e in cat.get('猫苑评价', [])]
    counts = Counter(texts)
    return {'匹配数': len(texts), '不同原文数': len(counts), '重复占比': round(1-len(counts)/len(texts), 3) if texts else 0,
            '最常见原文': counts.most_common(5)}


if __name__ == '__main__':
    path = Path('cats_detail.json')
    original = path.read_bytes()
    cats = json.loads(original)
    print('修改前：', stats(cats))
    rematch_cats(cats)
    print('修改后：', stats(cats))
    backup = path.with_name('cats_detail.backup.' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.json')
    backup.write_bytes(original)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
            temporary = f.name
            json.dump(cats, f, ensure_ascii=False, indent=4)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    print('完成，原数据备份：', backup)
