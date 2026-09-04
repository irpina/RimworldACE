"""Serve the laboratory viewer: ``python -m economy_lab.viewer``."""

from __future__ import annotations

import argparse
import webbrowser

from .server import make_server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    parser.add_argument("--verbose", action="store_true", help="log every request")
    args = parser.parse_args()

    server = make_server(port=args.port, quiet=not args.verbose)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Laboratory viewer at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
