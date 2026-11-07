"""Only Supabase is authoritative. There is intentionally no local-data fallback."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request


class CloudError(Exception):
    def __init__(self, status=503):
        self.status = status
        super().__init__('云端存储请求失败（状态 %s）' % status)


class Store:
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL', 'https://cmjxnryeextyvprrtxqc.supabase.co').rstrip('/')
        self.key = os.environ.get('SUPABASE_SECRET_KEY', '')
        self.bucket = 'cat-images'

    def request(self, method, path, data=None, mime='application/json', raw=False, headers=None):
        if not self.key:
            raise CloudError(503)
        hdr = {'apikey': self.key, 'Content-Type': mime, **(headers or {})}
        if self.key.startswith('eyJ'):
            hdr['Authorization'] = 'Bearer ' + self.key
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode() if data is not None else None
        req = urllib.request.Request(self.url + path, data=body, method=method, headers=hdr)
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                b = response.read()
                return (b, response.headers.get('Content-Type', 'application/octet-stream')) if raw else json.loads(b) if b else None
        except urllib.error.HTTPError as e:
            raise CloudError(e.code) from None
        except (OSError, ValueError):
            raise CloudError(503) from None

    def rows(self, table, filters=None):
        result = []
        for offset in range(0, 100000, 500):
            params = {'select': '*', 'order': 'id.asc' if table == 'maoyuan_cats' else 'name.asc', 'limit': '500', 'offset': str(offset), **(filters or {})}
            rows = self.request('GET', '/rest/v1/' + table + '?' + urllib.parse.urlencode(params))
            result.extend(rows)
            if len(rows) < 500:
                return result
        raise CloudError(503)

    def cat(self, cat_id):
        rows = self.rows('maoyuan_cats', {'id': 'eq.' + str(cat_id)})
        return rows[0] if rows else None

    def write(self, table, key, data, revision=None):
        if revision is None:
            payload = {'data': data}
            if table == 'maoyuan_map_areas': payload['name'] = key
            rows = self.request('POST', '/rest/v1/' + table, payload, headers={'Prefer': 'return=representation'})
        else:
            column = 'id' if table == 'maoyuan_cats' else 'name'
            query = urllib.parse.urlencode({column: 'eq.' + str(key), 'revision': 'eq.' + str(revision)})
            rows = self.request('PATCH', '/rest/v1/' + table + '?' + query, {'data': data}, headers={'Prefer': 'return=representation'})
        if not rows: raise CloudError(409)
        return rows[0]

    def upload(self, name, raw, mime):
        return self.request('POST', '/storage/v1/object/' + self.bucket + '/' + urllib.parse.quote(name, safe=''), raw, mime, headers={'x-upsert': 'false'})

    def image(self, name):
        return self.request('GET', '/storage/v1/object/authenticated/' + self.bucket + '/' + urllib.parse.quote(name, safe=''), raw=True)


def cat_view(row):
    data = {k:v for k,v in row['data'].items() if k != '_submission_id'}
    return dict(data, id=row['id'], _version=str(row['revision']))
