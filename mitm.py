#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["mitmproxy>=12"]
# ///
#
# Usage as self contained uv script:
#   ./mitm.py mitmproxy --view-filter='~d example'
#   ./mitm.py mitmdump '~d example'
if __name__ == "__main__":
    import sys, mitmproxy.tools.main
    if len(sys.argv) < 2 or (sys.argv[1] not in ["mitmproxy", "mitmdump", "mitmweb"]):
        sys.exit(f"Usage:  {sys.argv[0]} mitmproxy|mitmdump|mitmweb --help ...")
    cmd = getattr(mitmproxy.tools.main, sys.argv[1])
    cmd(["--scripts", __file__, *sys.argv[2:]])

# Addon example scripts: https://docs.mitmproxy.org/stable/addons/examples/
# Filter expression reference: https://docs.mitmproxy.org/stable/concepts/filters/

from mitmproxy import ctx, http

def running():
    browser = ctx.master.addons.get('browser')
    if not browser.browser:  # Don't launch more browsers on script reload
        browser.start(browser="chrome")  # or "firefox"
