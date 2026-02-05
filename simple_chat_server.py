# Lightweight HTTP server for serving the chatbot API and frontend assets.
# This implementation uses Python's built-in HTTP server and provides
# mock endpoints alongside a chatbot inference endpoint.

import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Import chatbot instance and model loader
from chatbot.chatbot_core import chatbot as chatbot_instance, load_models

# Load model once at server startup
load_models()

PORT = 8000

def send_json(handler, data, status=200):
    # Utility function for sending JSON responses with CORS headers
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

class MyHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        # ---------- Mock API endpoints ----------
        if self.path.startswith("/api/tasks"):
            return send_json(self, {
                "total_tasks": 16,
                "completed_tasks": 10,
                "overdue_tasks": 2,
                "tasks": [
                    {"id": 1, "title": "Check Elevator", "team_name": "Maintenance", "status": "pending", "due_date": "2026-01-25"},
                    {"id": 2, "title": "Clean Lobby", "team_name": "Cleaning", "status": "completed", "due_date": "2026-01-20"},
                ]
            })

        if self.path.startswith("/api/teams"):
            return send_json(self, [
                {"id": 1, "name": "Maintenance", "members": ["Ali", "Reza"]},
                {"id": 2, "name": "Cleaning", "members": ["Sara", "Mina"]},
            ])

        if self.path.startswith("/api/meetings"):
            return send_json(self, [
                {"id": 1, "title": "Board Meeting", "scheduled_date": "2026-01-24T10:00:00", "status": "scheduled"},
                {"id": 2, "title": "Emergency Meeting", "scheduled_date": "2026-01-25T14:00:00", "status": "pending"},
            ])

        if self.path.startswith("/api/notifications"):
            return send_json(self, [
                {"id": 1, "title": "System Update", "message": "Maintenance planned at 10pm", "notification_type": "general"},
                {"id": 2, "title": "New Task", "message": "New maintenance request added", "notification_type": "maintenance"},
            ])

        # Serve static frontend files
        return super().do_GET()

    def do_POST(self):
        # Handle chatbot inference requests
        if self.path.startswith("/api/chat"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}

            text = data.get("text", "").strip()
            if not text:
                return send_json(self, {"error": "Empty message"}, status=400)

            # Run chatbot prediction
            result = chatbot_instance.predict(text)

            # Return standardized chatbot response
            return send_json(self, result)

        return send_json(self, {"error": "Unknown endpoint"}, status=404)

if name == "__main__":
    print(f"✅ Server running: http://localhost:{PORT}/front/index.html")
    httpd = HTTPServer(("0.0.0.0", PORT), MyHandler)
    httpd.serve_forever()
