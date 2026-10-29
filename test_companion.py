import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from companion import Store, chat, probe, complete, protect, endpoint


class Handler(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *_):
        pass

    def reply(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        self.reply({'data': [{'id': 'test-chat'}]})

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.requests.append(data)
        if self.headers.get('Authorization') != 'Bearer test-secret':
            self.reply({}, 401)
        else:
            summary = '整理长期记忆' in data['messages'][0]['content']
            text = '用户喜欢喝茶。' if summary else '你好，我是小雅。'
            self.reply({'choices': [{'message': {'content': text}}]})


class CompanionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.config = dict(base_url=f'http://127.0.0.1:{cls.server.server_port}', model='test-chat', api_key='test-secret')

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_probe_and_failed_key(self):
        result = probe(self.config)
        self.assertEqual(result['models'], ['test-chat'])
        with self.assertRaisesRegex(RuntimeError, '401'):
            complete(dict(self.config, api_key='wrong'), [{'role': 'user', 'content': 'hi'}])

    def test_history_memory_and_personality_survive_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            store.set('personality', '温柔，但有自己的主见。')
            store.set('user_notes', '喜欢喝茶')
            for _ in range(8):
                self.assertIn('小雅', chat(store, self.config, '我喜欢喝茶')['answer'])
            reopened = Store(folder)
            self.assertEqual(len(reopened.history()), 16)
            self.assertIn('喜欢喝茶', reopened.get('memory'))
            context = reopened.context('还记得我吗？')
            self.assertIn('自己的主见', context[0]['content'])
            self.assertIn('喜欢喝茶', context[0]['content'])
            self.assertEqual(context[-1]['role'], 'user')

    def test_dpapi_config_has_no_plaintext_key(self):
        encrypted = protect('test-secret')
        self.assertEqual(protect(encrypted, True), 'test-secret')
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            store.save_config(self.config)
            self.assertNotIn('test-secret', store.get('config'))
            self.assertEqual(Store(folder).credentials()['api_key'], 'test-secret')

    def test_reject_plain_http_remote_and_embedded_credentials(self):
        for url in ('http://example.com/v1', 'https://user:pass@example.com', 'https://example.com?api_key=x'):
            with self.assertRaises(ValueError):
                endpoint({'base_url': url})


if __name__ == '__main__':
    unittest.main()
