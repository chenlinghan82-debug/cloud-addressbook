"""Isolated regression tests; never touch a running website's database."""
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def workbook_bytes(rows):
    wb = Workbook()
    for row in rows:
        wb.active.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def canonical(c):
    return (c['name'], c['favorite'], c['notes'], tuple(sorted((d['type'], d['value']) for d in c['details'])))


class AddressBookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.env = {k: os.environ.get(k) for k in ('DB_PATH', 'DATABASE_URL', 'SEED_DEMO', 'VERCEL')}
        test_url = os.environ.get('TEST_POSTGRES_URL', '')
        if test_url and urlsplit(test_url).path != '/addressbook_test':
            raise RuntimeError('PostgreSQL tests require a dedicated addressbook_test database')
        os.environ.update(DB_PATH=str(Path(cls.temp.name) / 'test.db'), DATABASE_URL=test_url, SEED_DEMO='0', VERCEL='0')
        spec = importlib.util.spec_from_file_location('addressbook_under_test', ROOT / 'app.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.module.app.config['TESTING'] = True

    @classmethod
    def tearDownClass(cls):
        for k, v in cls.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        cls.temp.cleanup()

    def setUp(self):
        self.client = self.module.app.test_client()
        with self.module.get_db() as db:
            db.execute('DELETE FROM contact_details')
            db.execute('DELETE FROM contacts')

    def create(self, name='Alice', favorite=True):
        response = self.client.post('/api/contacts', json={
            'name': name, 'favorite': favorite, 'notes': 'Classmate',
            'details': [{'type': 'phone', 'value': '00123'}, {'type': 'phone', 'value': '+86-123'},
                        {'type': 'email', 'value': 'alice@example.com'},
                        {'type': 'social', 'value': 'WeChat: alice'}, {'type': 'address', 'value': 'Campus'}]})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def upload(self, rows, filename='contacts.xlsx'):
        return self.client.post('/api/import', data={'file': (io.BytesIO(workbook_bytes(rows)), filename)})

    def test_crud_and_multiple_methods(self):
        c = self.create()
        self.assertEqual(len(c['details']), 5)
        c['notes'] = 'Updated'
        c['details'].append({'type': 'email', 'value': 'second@example.com'})
        response = self.client.put(f"/api/contacts/{c['id']}", json=c)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['notes'], 'Updated')
        self.assertEqual(len(response.json['details']), 6)
        self.assertEqual(self.client.delete(f"/api/contacts/{c['id']}").status_code, 200)
        self.assertEqual(self.client.get('/api/contacts').json, [])
        with self.module.get_db() as db:
            self.assertEqual(len(db.execute('SELECT * FROM contact_details').fetchall()), 0)

    def test_bookmark_and_search(self):
        c = self.create(favorite=False)
        route = f"/api/contacts/{c['id']}/favorite"
        self.assertTrue(self.client.patch(route).json['favorite'])
        self.assertTrue(self.client.get('/api/contacts').json[0]['favorite'])
        self.assertFalse(self.client.patch(route).json['favorite'])
        for query in ('ALICE', '00123', 'Classmate', 'Campus', 'WeChat'):
            self.assertEqual(len(self.client.get('/api/contacts', query_string={'q': query}).json), 1)
        self.assertEqual(self.client.get('/api/contacts?q=absent').json, [])

    def test_round_trip_all_fields_and_text(self):
        before = [self.create('张三'), self.create('=1+1', favorite=False)]
        response = self.client.get('/api/export')
        self.assertEqual(response.status_code, 200)
        wb = load_workbook(io.BytesIO(response.data), data_only=False)
        ws = wb['通讯录']
        self.assertEqual(ws.max_row, 3)
        self.assertIn('电话2', [c.value for c in ws[1]])
        self.assertEqual(ws['A3'].data_type, 's')
        self.assertEqual(ws['D2'].value, '00123')
        self.assertIn('导入模板', wb.sheetnames)
        wb.close()
        with self.module.get_db() as db:
            db.execute('DELETE FROM contact_details')
            db.execute('DELETE FROM contacts')
        imported = self.client.post('/api/import', data={'file': (io.BytesIO(response.data), 'roundtrip.xlsx')})
        self.assertEqual(imported.json, {'imported': 2, 'skipped': 0})
        self.assertEqual(sorted(map(canonical, before)), sorted(map(canonical, self.client.get('/api/contacts').json)))

    def test_english_reordered_headers_zero_and_blank_first_column(self):
        r = self.upload([['Notes', 'Name', 'Favorite', 'Phone1', 'Email1'],
                         [None, 'Bob', True, '00100', 'b@example.com'], [0, 'Carol', False, 0, None]])
        self.assertEqual(r.json, {'imported': 2, 'skipped': 0})
        contacts = {c['name']: c for c in self.client.get('/api/contacts').json}
        self.assertTrue(contacts['Bob']['favorite'])
        self.assertEqual(contacts['Carol']['notes'], '0')
        self.assertEqual(contacts['Carol']['details'][0]['value'], '0')

    def test_bad_workbooks(self):
        for rows in ([], [['Name']], [['Phone'], ['123']], [['Name', '姓名'], ['A', 'B']]):
            with self.subTest(rows=rows):
                self.assertEqual(self.upload(rows).status_code, 400)
        self.assertEqual(self.upload([['姓名'], ['Alice']], 'test.csv').status_code, 400)
        self.assertEqual(self.client.post('/api/import').status_code, 400)
        self.assertEqual(self.client.post('/api/import', data={'file': (io.BytesIO(b'broken'), 'broken.xlsx')}).status_code, 400)

    def test_blank_names_and_additive_import(self):
        rows = [['姓名', '电话1'], [None, '123'], ['  ', None], ['Bob', '00123']]
        self.assertEqual(self.upload(rows).json, {'imported': 1, 'skipped': 2})
        self.assertEqual(self.upload(rows).json, {'imported': 1, 'skipped': 2})
        self.assertEqual(len(self.client.get('/api/contacts').json), 2)

    def test_import_rollback(self):
        self.assertEqual(self.upload([['Name'], ['Bob'], ['x' * 201]]).status_code, 400)
        self.assertEqual(self.client.get('/api/contacts').json, [])

    def test_invalid_api_data_and_missing_ids(self):
        for payload in ([], None, {'name': None}, {'name': ' '}, {'name': 'A', 'details': {}},
                        {'name': 'A', 'details': [None]}, {'name': 'A', 'favorite': 'false'}):
            with self.subTest(payload=payload):
                r = self.client.post('/api/contacts', json=payload)
                self.assertIn(r.status_code, (400, 415))
                self.assertIn('error', r.json)
        self.assertEqual(self.client.delete('/api/contacts/99999').status_code, 404)
        self.assertEqual(self.client.patch('/api/contacts/99999/favorite').status_code, 404)
        self.assertEqual(self.client.put('/api/contacts/99999', json={'name': 'A'}).status_code, 404)
        self.assertEqual(self.client.get('/api/absent').status_code, 404)
        self.assertEqual(self.client.get('/missing-page').status_code, 404)

    def test_upload_limit_and_health(self):
        self.assertEqual(self.client.post('/api/import', data=b'x' * (5 * 1024 * 1024 + 1),
                                         content_type='application/octet-stream').status_code, 413)
        self.assertTrue(self.client.get('/api/health').json['persistent'])
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_sqlite_survives_new_process(self):
        self.create('Persisted')
        result = subprocess.run([sys.executable, '-c',
            "from app import app; assert app.test_client().get('/api/contacts').json[0]['name'] == 'Persisted'; print('persisted')"],
            cwd=ROOT, env=os.environ.copy(), capture_output=True, text=True, check=True)
        self.assertIn('persisted', result.stdout)

    def test_vercel_without_database_is_explicitly_unavailable(self):
        env = os.environ.copy()
        env.update(VERCEL='1', DATABASE_URL='', DB_PATH=str(Path(self.temp.name) / 'must-not-be-created.db'))
        code = "from app import app; c=app.test_client(); assert c.get('/api/health').status_code==503; assert c.get('/api/contacts').status_code==503; assert c.get('/').status_code==200"
        subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, check=True)
        self.assertFalse(Path(env['DB_PATH']).exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
