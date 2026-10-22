"""Dependency-free learning sample, not a production HTTP server."""

import os
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import TCPServer
from urllib.parse import urlsplit


MEME_URLS = (
    "https://i.imgflip.com/30b1gx.jpg",
    "https://i.imgflip.com/1g8my4.jpg",
    "https://i.imgflip.com/1ur9b0.jpg",
    "https://i.imgflip.com/22bdq6.jpg",
)


def render_home(greeting):
    meme_urls = ",\n                ".join(f'"{url}"' for url in MEME_URLS)
    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>App Service Builder Python sample</title>
    <style>
        body {{
            background: #f5f7fa;
            color: #172b4d;
            font-family: system-ui, sans-serif;
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
        }}
        main {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgb(9 30 66 / 15%);
            max-width: 680px;
            padding: 2rem;
            text-align: center;
            width: min(85%, 680px);
        }}
        button {{
            background: #0067b8;
            border: 0;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font: inherit;
            font-weight: 600;
            padding: 0.75rem 1.25rem;
        }}
        button:hover {{ background: #005a9e; }}
        button:focus-visible {{ outline: 3px solid #ffb900; outline-offset: 3px; }}
        img {{
            border-radius: 8px;
            display: none;
            margin: 1.5rem auto 0;
            max-height: 420px;
            max-width: 100%;
        }}
    </style>
</head>
<body>
    <main>
        <h1>App Service Builder / python-web: {escape(greeting)}</h1>
        <p>Click the button for a randomly selected meme.</p>
        <button id="meme-button" type="button">Show me a meme</button>
        <img id="meme-image" alt="A randomly selected meme">
    </main>
    <script>
        const memeUrls = [
                {meme_urls}
        ];
        const memeButton = document.getElementById("meme-button");
        const memeImage = document.getElementById("meme-image");

        memeButton.addEventListener("click", () => {{
            const randomIndex = Math.floor(Math.random() * memeUrls.length);
            memeImage.src = memeUrls[randomIndex];
            memeImage.style.display = "block";
        }});
    </script>
</body>
</html>
"""


class SampleHTTPServer(ThreadingHTTPServer):
    def server_bind(self):
        # HTTPServer's default bind performs reverse DNS for a display name.
        # This sample needs no DNS dependency; bind directly and use a fixed name.
        TCPServer.server_bind(self)
        self.server_name = "builder-python-sample"
        self.server_port = self.server_address[1]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            status, body, content_type = 200, "OK\n", "text/plain; charset=utf-8"
        elif path == "/":
            greeting = os.environ.get("SAMPLE_GREETING") or "Hello"
            status, body, content_type = (
                200,
                render_home(greeting),
                "text/html; charset=utf-8",
            )
        else:
            status, body, content_type = (
                404,
                "Not found\n",
                "text/plain; charset=utf-8",
            )
        content = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        # Do not print request URLs or environment variables.
        pass


if __name__ == "__main__":
    SampleHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
