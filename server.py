"""
Production Server Entry Point with Live Backend Sync API
Wraps Streamlit with dedicated REST endpoints for live cloud-to-local synchronization.
"""

import os
import sys
import json
import tornado.web
import streamlit.web.server.server as st_server
import streamlit.web.cli as st_cli

# Monkeypatch Streamlit Server to add REST synchronization endpoints
_original_create_app = st_server.Server._create_app


def _patched_create_app(self):
    app = _original_create_app(self)

    class BackendSyncApiHandler(tornado.web.RequestHandler):
        def set_default_headers(self):
            self.set_header("Access-Control-Allow-Origin", "*")
            self.set_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.set_header("Access-Control-Allow-Headers", "Content-Type")
            self.set_header("Content-Type", "application/json")

        def options(self):
            self.set_status(204)
            self.finish()

        def get(self):
            from src.tracker import export_all_backend_data
            data = export_all_backend_data()
            self.write(json.dumps(data))

    class BackendZipApiHandler(tornado.web.RequestHandler):
        def get(self):
            from src.tracker import create_users_zip_archive
            zip_bytes = create_users_zip_archive()
            self.set_header("Content-Type", "application/zip")
            self.set_header("Content-Disposition", "attachment; filename=users_cloud_data.zip")
            self.write(zip_bytes)

    app.add_handlers(r".*", [
        (r"/api/sync", BackendSyncApiHandler),
        (r"/api/download_users", BackendZipApiHandler),
    ])
    return app


st_server.Server._create_app = _patched_create_app


def run_server():
    port = os.environ.get("PORT", "8501")
    dashboard_path = os.path.join(os.path.dirname(__file__), "app", "dashboard.py")
    
    sys.argv = [
        "streamlit",
        "run",
        dashboard_path,
        "--server.port",
        str(port),
        "--server.address",
        "0.0.0.0",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false"
    ]
    st_cli.main()


if __name__ == "__main__":
    run_server()
