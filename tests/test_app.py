import os
import threading
import unittest
from http.client import HTTPConnection
from unittest.mock import patch

from app import Handler, MEME_URLS, SampleHTTPServer


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        with patch("socket.getfqdn", side_effect=AssertionError("Unexpected DNS lookup")):
            self.server = SampleHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(self.server.server_close)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive(), "Sample server did not stop")

    def get_response(self, path):
        connection = HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            content = response.read()
            return response, content
        finally:
            connection.close()

    def assert_text_response(self, path, status, body):
        response, content = self.get_response(path)
        try:
            self.assertEqual(response.status, status)
            self.assertEqual(content, body.encode("utf-8"))
            self.assertEqual(response.getheader("Content-Length"), str(len(content)))
            self.assertEqual(
                response.getheader("Content-Type"), "text/plain; charset=utf-8"
            )
        finally:
            response.close()

    def test_default_greeting(self):
        response, content = self.get_response("/")
        body = content.decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "text/html; charset=utf-8")
        self.assertEqual(response.getheader("Content-Length"), str(len(content)))
        self.assertIn("App Service Builder / python-web: Hello", body)
        self.assertIn('id="meme-button"', body)
        self.assertIn('id="meme-image"', body)
        self.assertIn("Math.random()", body)
        for url in MEME_URLS:
            self.assertIn(url, body)
        response.close()

    def test_health(self):
        self.assert_text_response("/health", 200, "OK\n")

    def test_unknown_path(self):
        self.assert_text_response("/not-found", 404, "Not found\n")

    def test_public_greeting(self):
        os.environ["SAMPLE_GREETING"] = "Welcome"
        _, content = self.get_response("/")
        self.assertIn("App Service Builder / python-web: Welcome", content.decode("utf-8"))

    def test_empty_greeting_uses_default(self):
        os.environ["SAMPLE_GREETING"] = ""
        _, content = self.get_response("/")
        self.assertIn("App Service Builder / python-web: Hello", content.decode("utf-8"))

    def test_query_does_not_change_route(self):
        self.assert_text_response("/health?check=1", 200, "OK\n")

    def test_greeting_is_html_escaped(self):
        os.environ["SAMPLE_GREETING"] = "<script>alert(1)</script>"
        _, content = self.get_response("/")
        body = content.decode("utf-8")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", body)
        self.assertNotIn("<script>alert(1)</script>", body)

    def test_bind_does_not_require_reverse_dns(self):
        self.assertEqual(self.server.server_name, "builder-python-sample")
        self.assertEqual(self.server.server_port, self.server.server_address[1])


if __name__ == "__main__":
    unittest.main()
