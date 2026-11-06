"""公开投稿与编辑。仅注册此模块的路由；无需管理员登录。"""
import base64
import hashlib
import json
import math
import os
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import fcntl
from flask import Blueprint, current_app, jsonify, request, send_from_directory, g
import resource
import time
import threading

bp = Blueprint('public_editor', __name__)
# Only metadata is logged: no names, descriptions, image contents or credentials.
def diagnostic_line(trace, stage, started):
    try:
        peak_mb = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
        memory = {'process_peak_mb': peak_mb}
        for label, path in [('container_current_bytes', '/sys/fs/cgroup/memory.current'),
                            ('container_limit_bytes', '/sys/fs/cgroup/memory.max')]:
            try:
                memory[label] = Path(path).read_text().strip()
            except OSError:
                pass
        print('[CAT_SAVE_DIAG] ' + json.dumps({'request_id': trace, 'pid': os.getpid(),
              'stage': stage, 'elapsed_s': round(time.monotonic() - started, 2),
              **memory}, ensure_ascii=False), flush=True)
    except Exception:
        # Diagnostics must not change the request result.
        pass


def diagnostic(stage):
    diagnostic_line(g.cat_diag_id, stage, g.cat_diag_started)


@bp.before_request
def begin_diagnostic():
    if request.method in {'POST', 'PUT'} and request.path.startswith('/api/public/cats'):
        g.cat_diag_id = uuid.uuid4().hex[:12]
        g.cat_diag_started = time.monotonic()
        diagnostic('01_request_entered bytes=' + str(request.content_length))


@bp.after_request
def finish_diagnostic(response):
    if hasattr(g, 'cat_diag_id'):
        diagnostic('99_response status=' + str(response.status_code))
        response.headers['X-Cat-Request-ID'] = g.cat_diag_id
    return response


@bp.teardown_request
def diagnostic_exception(error):
    if error is not None and hasattr(g, 'cat_diag_id'):
        diagnostic('ERROR_unhandled type=' + type(error).__name__)


FIELDS = {'名字': 40, '活动区域': 120, '毛色': 100, '体型': 100,
          '性格': 500, '常见行为': 2000, '发现地点': 200, '备注': 2000}


def data_path():
    return Path(current_app.config['PUBLIC_CAT_DATA']).resolve()


def version(cat):
    return hashlib.sha256(json.dumps(cat, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


@contextmanager
def locked():
    path = data_path().with_suffix('.lock')
    with path.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def load():
    return json.loads(data_path().read_text(encoding='utf-8'))


def save(cats, original):
    folder = Path(current_app.config['PUBLIC_CAT_BACKUPS']).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    (folder / (stamp + '-' + uuid.uuid4().hex + '.json')).write_text(original, encoding='utf-8')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=data_path().parent, delete=False) as f:
            temporary = f.name
            json.dump(cats, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, data_path())
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def image_bytes(value):
    if not isinstance(value, str) or len(value) > 14500000:
        raise ValueError('照片过大，请选择不超过10 MB的图片')
    try:
        head, encoded = value.split(',', 1)
        mime = head.split(';')[0]
        ext = {'data:image/jpeg': '.jpg', 'data:image/png': '.png', 'data:image/webp': '.webp'}[mime]
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, KeyError):
        raise ValueError('照片格式必须为JPG、PNG或WebP')
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise ValueError('照片不能为空且不得超过10 MB')
    valid = ((ext == '.jpg' and raw.startswith(b'\xff\xd8\xff')) or
             (ext == '.png' and raw.startswith(b'\x89PNG\r\n\x1a\n')) or
             (ext == '.webp' and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP'))
    if not valid:
        raise ValueError('图片内容与格式不符')
    return raw, ext


@bp.route('/contribute')
def editor():
    return send_from_directory(Path(__file__).parent, 'public_editor.html')


@bp.route('/api/public/cats', methods=['GET'])
def list_cats():
    with locked():
        cats = load()
    response = jsonify([dict(c, _version=version(c)) for c in cats])
    response.headers['Cache-Control'] = 'no-store'
    return response


@bp.route('/api/public/cats', methods=['POST'])
@bp.route('/api/public/cats/<int:cat_id>', methods=['PUT'])
def write_cat(cat_id=None):
    if request.content_length and request.content_length > 16 * 1024 * 1024:
        return jsonify(message='提交内容过大'), 413
    diagnostic('02_reading_request_json')
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(message='没有收到有效资料'), 400
    cleaned = {}
    for key, limit in FIELDS.items():
        value = payload.get(key, '')
        if not isinstance(value, str) or len(value.strip()) > limit:
            return jsonify(message=key + '格式不正确或过长'), 400
        cleaned[key] = value.strip()
    if not cleaned['名字'] or not cleaned['活动区域']:
        return jsonify(message='请填写名字和活动区域'), 400
    picture = None
    if payload.get('photo_data'):
        try:
            picture = image_bytes(payload['photo_data'])
        except ValueError as e:
            return jsonify(message=str(e)), 400
    diagnostic('03_fields_and_image_validated')
    created_photo = None
    try:
        diagnostic('04_waiting_for_data_lock')
        with locked():
            diagnostic('05_lock_acquired_reading_database')
            original = data_path().read_text(encoding='utf-8')
            cats = json.loads(original)
            previous = next((c for c in cats if c['id'] == cat_id), None) if cat_id is not None else None
            if cat_id is not None:
                if previous is None:
                    return jsonify(message='这只猫已不存在，请刷新列表'), 404
                if payload.get('_version') != version(previous):
                    return jsonify(message='其他访客刚刚更新了这只猫。你的输入仍保留，请先复制后重新载入最新档案再修改。'), 409
            elif not picture:
                return jsonify(message='新增档案请上传真实猫咪照片'), 400
            item = dict(previous or {})
            item.update(cleaned)
            if cat_id is None:
                item['id'] = max((int(c['id']) for c in cats), default=0) + 1
            # 不信任客户端提供的ID、图片路径或古文匹配结果。
            diagnostic('06_matching_started')
            stop_heartbeat = threading.Event()
            trace, started = g.cat_diag_id, g.cat_diag_started
            def heartbeat():
                while not stop_heartbeat.wait(10):
                    diagnostic_line(trace, '06_matching_still_running', started)
            thread = threading.Thread(target=heartbeat, daemon=True)
            thread.start()
            try:
                matches = current_app.config['PUBLIC_CAT_MATCHER'](item, existing_cats=[c for c in cats if c['id'] != item['id']])
            finally:
                stop_heartbeat.set()
            diagnostic('07_matching_finished')
            item['猫苑评价'] = matches
            diagnostic('08_writing_photo')
            if picture:
                folder = Path(current_app.config['PUBLIC_CAT_IMAGES']).resolve()
                folder.mkdir(parents=True, exist_ok=True)
                raw, ext = picture
                created_photo = folder / ('public-' + uuid.uuid4().hex + ext)
                created_photo.write_bytes(raw)
                item['照片'] = created_photo.name
            item['更新时间'] = datetime.now(timezone.utc).isoformat()
            if previous is None:
                cats.append(item)
            else:
                cats[cats.index(previous)] = item
            diagnostic('09_backing_up_and_saving_database')
            save(cats, original)
            diagnostic('10_database_saved')
        return jsonify(status='success', cat=dict(item, _version=version(item))), 200 if previous else 201
    except Exception:
        if created_photo:
            created_photo.unlink(missing_ok=True)
        diagnostic('ERROR_save_failed')
        current_app.logger.exception('公开猫咪档案保存失败')
        return jsonify(message='保存失败，原档案未被替换，请稍后再试'), 500



def map_data():
    path = Path(current_app.config['PUBLIC_CAT_MAP'])
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


@bp.route('/api/public/map_areas', methods=['GET'])
def public_map():
    with locked():
        areas = map_data()
    response = jsonify(areas=areas, versions={key: version(value) for key, value in areas.items()})
    response.headers['Cache-Control'] = 'no-store'
    return response


@bp.route('/api/public/map_areas', methods=['PUT'])
def update_public_map():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(message='无效地图资料'), 400
    area, pos = data.get('area'), data.get('position')
    if not isinstance(area, str) or not area.strip() or len(area) > 120 or not isinstance(pos, dict):
        return jsonify(message='请填写活动区域并选择地图位置'), 400
    area = area.strip()
    place = pos.get('地图标准地点')
    if not isinstance(place, str) or not place.strip() or len(place) > 200:
        return jsonify(message='请填写地图标准地点'), 400
    for axis in ('x', 'y'):
        v = pos.get(axis)
        if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or not 0 <= v <= 100:
            return jsonify(message='地图坐标必须在0到100之间'), 400
    position = {'x': round(pos['x'], 2), 'y': round(pos['y'], 2), '地图标准地点': place.strip()}
    with locked():
        areas = map_data()
        previous = areas.get(area)
        if data.get('_version') != (version(previous) if previous is not None else None):
            return jsonify(message='该区域已被其他访客修改，请重新载入地图后再定位'), 409
        # 仅更新这个区域，不以客户端整张地图覆盖其他访客的新地点。
        path = Path(current_app.config['PUBLIC_CAT_MAP'])
        backup = Path(current_app.config['PUBLIC_CAT_BACKUPS'])
        backup.mkdir(parents=True, exist_ok=True)
        (backup / ('map-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex + '.json')).write_text(json.dumps(areas, ensure_ascii=False, indent=4), encoding='utf-8')
        areas[area] = position
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as f:
                temporary = f.name
                json.dump(areas, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
    return jsonify(status='success', area=area, position=position, version=version(position))

def register_public_editor(app, data_file, image_folder, matcher, map_file="map_areas.json"):
    app.config['PUBLIC_CAT_MAP'] = str(Path(map_file).resolve())
    app.config['PUBLIC_CAT_DATA'] = str(Path(data_file).resolve())
    app.config['PUBLIC_CAT_IMAGES'] = str(Path(image_folder).resolve())
    # 不放在网站根目录，避免被原有静态通配路由公开。
    app.config['PUBLIC_CAT_BACKUPS'] = os.environ.get('CAT_BACKUP_DIR', str(Path(data_file).resolve().parent.parent / 'cat-private-backups'))
    app.config['PUBLIC_CAT_MATCHER'] = matcher
    app.register_blueprint(bp)
