"""Explicit administrator migration. Never called at startup or on public requests."""
import json
import mimetypes
from pathlib import Path
from cloud_store import CloudError


def prepare(root):
    root=Path(root)
    cat_path=root/'cats_detail.json';map_path=root/'map_areas.json'
    if not cat_path.is_file() or not map_path.is_file():raise ValueError('缺少原项目cats_detail.json或map_areas.json，已停止迁移')
    original=json.loads(cat_path.read_text(encoding='utf-8'));areas=json.loads(map_path.read_text(encoding='utf-8'))
    if not isinstance(original,list) or not original or not isinstance(areas,dict):raise ValueError('原数据为空或格式错误，已停止迁移')
    cats=[dict(c) for c in original]
    existing={c['名字'] for c in cats};next_id=max(int(c['id']) for c in cats)+1
    for c in json.loads((root/'recovery_cats.json').read_text(encoding='utf-8')):
        if c['名字'] not in existing:
            cats.append(dict(c,id=next_id));next_id+=1
    if len({int(c['id']) for c in cats})!=len(cats):raise ValueError('原数据ID重复，已停止迁移')
    photos={}
    for name in [c.get('照片','') for c in cats]+['campus-map.jpg']:
        if not name or Path(name).name!=name:raise ValueError('照片文件名无效')
        path=root/'recovery-images'/name
        if not path.is_file():path=root/'images'/name
        if not path.is_file():raise ValueError('缺少照片文件：'+name+'，已停止迁移')
        photos[name]=path
    return cats,areas,photos


def migrate(store,root):
    cats,areas,photos=prepare(root)
    if store.rows('maoyuan_cats') or store.rows('maoyuan_map_areas'):
        raise ValueError('云端已有数据，拒绝重复迁移或覆盖；请先核对云端内容')
    # Require private bucket; no silently public photos or auto-created bucket.
    bucket=store.request('GET','/storage/v1/bucket/cat-images')
    if bucket.get('public') is not False:raise ValueError('cat-images必须是私有存储桶')
    for name,path in photos.items():
        raw=path.read_bytes()
        try:
            existing,_=store.image(name)
        except CloudError as e:
            if e.status not in (400,404):raise
        else:
            if existing!=raw:raise ValueError('云端已有不同内容的同名照片：'+name+'；迁移未覆盖它')
            continue
        store.upload(name,raw,mimetypes.guess_type(name)[0] or 'application/octet-stream')
    # A single database transaction imports all records and resets the ID sequence.
    return store.request('POST','/rest/v1/rpc/maoyuan_import_seed',{'p_cats':cats,'p_maps':areas})
