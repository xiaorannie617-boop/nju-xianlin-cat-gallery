"""猫苑图鉴 Supabase持久化版：沿用原网页与低内存匹配模块。"""
import base64
import json
import math
import os
from pathlib import Path
import threading
from time import perf_counter
import uuid
from flask import Flask, Response, abort, jsonify, redirect, request, send_from_directory, session
from cloud_store import Store, CloudError, cat_view

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(32)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
store = Store()
match_lock = threading.Lock()
FIELDS = {'名字':40,'活动区域':120,'毛色':100,'体型':100,'性格':500,'常见行为':2000,'发现地点':200,'备注':2000,'性别':20,'绝育情况':30}


@app.errorhandler(CloudError)
def cloud_error(error):
    status = 409 if error.status == 409 else 503
    app.logger.error('CLOUD_STORAGE_ERROR status=%s', error.status)
    return jsonify(message='资料已被其他访客修改，请重新载入' if status == 409 else '云端存储暂不可用，请检查Supabase配置或服务状态。没有切换到临时文件保存。'), status


@app.errorhandler(413)
def too_large(error):
    return jsonify(message='提交内容过大，请选择10 MB以内照片'), 413


def cats():
    return [cat_view(r) for r in store.rows('maoyuan_cats')]


def maps():
    rows = store.rows('maoyuan_map_areas')
    return {r['name']:r['data'] for r in rows}, {r['name']:str(r['revision']) for r in rows}


def parse_image(value):
    try:
        head, encoded = value.split(',',1)
        mime = head.split(';')[0].removeprefix('data:')
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, AttributeError): abort(400, '照片格式无效')
    ext = {'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp'}.get(mime)
    valid = (mime == 'image/jpeg' and raw.startswith(b'\xff\xd8\xff')) or (mime == 'image/png' and raw.startswith(b'\x89PNG\r\n\x1a\n')) or (mime == 'image/webp' and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP')
    if not ext or not valid or not raw or len(raw)>10*1024*1024: abort(400, '照片格式或大小不符合要求')
    return raw,mime,ext


@app.route('/')
def index(): return send_from_directory('.', 'index.html')


@app.route('/contribute')
def contribute(): return send_from_directory('.', 'public_editor.html')


@app.route('/api/cats')
@app.route('/api/public/cats')
@app.route('/cats_detail.json')
def get_cats():
    response=jsonify(cats());response.headers['Cache-Control']='no-store';return response


@app.route('/api/map_areas')
@app.route('/map_areas.json')
def get_map():
    response=jsonify(maps()[0]);response.headers['Cache-Control']='no-store';return response


@app.route('/api/public/map_areas')
def get_public_map():
    areas,versions=maps();response=jsonify(areas=areas,versions=versions);response.headers['Cache-Control']='no-store';return response


@app.route('/api/public/map_areas',methods=['PUT'])
def put_map():
    if not store.rows('maoyuan_cats'):
        return jsonify(message='云端尚未完成迁移，请管理员先完成迁移，不要重新录入旧档案'),503
    p=request.get_json(silent=True)
    if not isinstance(p,dict):return jsonify(message='无效资料'),400
    name,pos=p.get('area'),p.get('position')
    if not isinstance(name,str) or not 1<=len(name.strip())<=120 or not isinstance(pos,dict):return jsonify(message='请填写活动区域'),400
    place=pos.get('地图标准地点')
    if not isinstance(place,str) or not 1<=len(place.strip())<=200:return jsonify(message='请填写标准地点'),400
    for axis in ('x','y'):
        v=pos.get(axis)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=100:return jsonify(message='坐标应为0—100'),400
    position={'x':round(pos['x'],2),'y':round(pos['y'],2),'地图标准地点':place.strip()}
    row=store.write('maoyuan_map_areas',name.strip(),position,p.get('_version'))
    return jsonify(status='success',area=name.strip(),position=row['data'],version=str(row['revision']))


@app.route('/api/public/cats',methods=['POST'])
@app.route('/api/public/cats/<int:cat_id>',methods=['PUT'])
def save_cat(cat_id=None):
    if not store.rows('maoyuan_cats'):
        return jsonify(message='云端尚未完成迁移，请管理员先完成迁移，不要重新录入旧档案'),503
    p=request.get_json(silent=True)
    if not isinstance(p,dict):return jsonify(message='无效资料'),400
    submission = None
    if cat_id is None:
        try: submission = str(uuid.UUID(str(p.get('submission_id',''))))
        except ValueError:return jsonify(message='请刷新编辑页后重新提交'),400
        existing=store.rows('maoyuan_cats',{'data->>_submission_id':'eq.'+submission})
        if existing:return jsonify(status='success',cat=cat_view(existing[0])),200
    previous=store.cat(cat_id) if cat_id is not None else None
    if cat_id is not None and previous is None:return jsonify(message='找不到猫咪'),404
    if previous and str(p.get('_version'))!=str(previous['revision']):raise CloudError(409)
    data=dict(previous['data']) if previous else {}
    for field,limit in FIELDS.items():
        value=p.get(field,data.get(field,''))
        if not isinstance(value,str) or len(value.strip())>limit:return jsonify(message=field+'格式无效或过长'),400
        data[field]=value.strip()
    if not data['名字'] or not data['活动区域']:return jsonify(message='请填写名字和活动区域'),400
    if p.get('photo_data'):
        raw,mime,ext=parse_image(p['photo_data']);name='public-'+uuid.uuid4().hex+ext
        store.upload(name,raw,mime);data['照片']=name
    elif not previous:return jsonify(message='新增猫咪请提供照片'),400
    data.pop('id',None);data.pop('_version',None)
    if submission:data['_submission_id']=submission
    data['猫苑评价']=[];data['匹配状态']='待匹配'
    row=store.write('maoyuan_cats',cat_id,data,previous['revision'] if previous else None)
    print('CLOUD_CAT_SAVED id=%s revision=%s' % (row['id'],row['revision']),flush=True)
    return jsonify(status='success',cat=cat_view(row)),200 if previous else 201


@app.route('/api/public/cats/<int:cat_id>/match',methods=['POST'])
def match_cat(cat_id):
    row=store.cat(cat_id)
    if not row:return jsonify(message='找不到猫咪'),404
    p=request.get_json(silent=True) or {}
    if str(p.get('_version'))!=str(row['revision']):raise CloudError(409)
    if not match_lock.acquire(blocking=False):return jsonify(message='另一个匹配任务正在进行，档案已保存，请稍后重试匹配'),429
    try:
        started=perf_counter()
        from cat_match_v2 import match_catyuan
        imported=perf_counter()
        cat=cat_view(row)
        existing=[c for c in cats() if c['id']!=cat_id]
        loaded=perf_counter()
        results=match_catyuan(cat,existing_cats=existing)
        matched=perf_counter()
        data=dict(row['data'],猫苑评价=results,匹配状态='完成')
        updated=store.write('maoyuan_cats',cat_id,data,row['revision'])
        print('CLOUD_MATCH_TIMING id=%s import=%.2fs read=%.2fs match=%.2fs write=%.2fs' % (cat_id,imported-started,loaded-imported,matched-loaded,perf_counter()-matched),flush=True)
        return jsonify(status='success',cat=cat_view(updated))
    except CloudError:raise
    except Exception:
        app.logger.exception('CLOUD_MATCH_FAILED id=%s',cat_id)
        return jsonify(message='档案和照片已保存，匹配未完成，可稍后单独重试'),500
    finally:match_lock.release()


@app.route('/images/<path:name>')
def image(name):
    if '/' in name or '\\' in name or name.startswith('.'):abort(404)
    raw,mime=store.image(name)
    return Response(raw,content_type=mime,headers={'Cache-Control':'public,max-age=3600','X-Content-Type-Options':'nosniff'})


@app.route('/api/storage_status')
def storage_status():
    return jsonify(storage='supabase',cats=len(cats()),areas=len(maps()[0]))


@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    if request.method=='GET':return send_from_directory('.','admin_login.html')
    password=os.environ.get('ADMIN_PASSWORD')
    if password and request.form.get('username')==os.environ.get('ADMIN_USERNAME','admin') and request.form.get('password')==password:
        session['admin_logged_in']=True;return redirect('/admin')
    return '登录失败，请检查账号和密码',401


@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):return redirect('/admin_login')
    return send_from_directory('.','admin.html')


@app.route('/admin_logout')
def logout():session.clear();return redirect('/')


@app.route('/api/delete_cat/<int:cat_id>',methods=['DELETE'])
def delete_cat(cat_id):
    if not session.get('admin_logged_in'):return jsonify(message='请先登录管理员'),401
    store.request('DELETE','/rest/v1/maoyuan_cats?id=eq.'+str(cat_id));return jsonify(status='success')


# Do not let old administrative writes silently update ephemeral JSON files.
@app.route('/api/add_cat',methods=['POST'])
@app.route('/api/update_cat/<int:cat_id>',methods=['PUT'])
@app.route('/api/map_areas',methods=['POST'])
@app.route('/api/upload',methods=['POST'])
@app.route('/api/rematch_all',methods=['POST'])
def legacy_write(cat_id=None):
    return jsonify(message='云端版请使用相猫台新增/编辑/地图及逐只匹配，旧版批量写入接口已停用，避免误写临时文件'),410


@app.route('/admin/migration', methods=['GET','POST'])
def admin_migration():
    if not session.get('admin_logged_in'):return redirect('/admin_login')
    from migration import prepare,migrate
    if request.method=='POST':
        if request.form.get('confirm')!='IMPORT':return jsonify(message='请在确认框输入IMPORT'),400
        try:return jsonify(status='success',result=migrate(store,Path(__file__).parent))
        except ValueError as e:return jsonify(message=str(e)),400
    try:
        seed,areas,photos=prepare(Path(__file__).parent)
        summary={'cloud_cats':len(store.rows('maoyuan_cats')),'cloud_areas':len(store.rows('maoyuan_map_areas')),
                 'planned_cats':[{'id':c['id'],'名字':c['名字']} for c in seed], 'planned_areas':len(areas),'photos':len(photos)}
    except ValueError as e:return jsonify(message=str(e)),400
    from markupsafe import escape
    return '<meta charset="utf-8"><h2>迁移预检</h2><pre>'+str(escape(json.dumps(summary,ensure_ascii=False,indent=2)))+'</pre><p>只允许向空表导入，不覆盖云端已有档案。确认名单和照片完整后输入IMPORT。</p><form method="post"><input name="confirm" required><button>导入云端</button></form>'


@app.errorhandler(400)
def bad_input(error):
    return jsonify(message='提交资料格式无效，请检查字段与图片'),400


@app.route('/<path:path>')
def static_files(path):
    allowed={'style.css','script.js','detail.js','admin.js','detail.html','favicon.svg'}
    if path not in allowed:abort(404)
    return send_from_directory('.',path)


if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')))
