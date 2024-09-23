"""
Embed an ipython terminal into mitmproxy.

Use the ` shortcut to launch IPython.

This is a bit of a hack because nest_asyncio is used.
"""

from mitmproxy import addonmanager
from mitmproxy import command
from mitmproxy.tools.console.master import ConsoleMaster


class IPython:
    def load(self, loader: addonmanager.Loader):
        if isinstance(loader.master, ConsoleMaster):
            self.master = loader.master
            self.master.keymap.add(
                "`", "ipython", ["global"], "IPython embedded terminal"
            )

    @command.command("ipython")
    def ipython(self) -> None:
        if not self.master:
            return

        import nest_asyncio
        from IPython import embed

        nest_asyncio.apply()

        with self.master.uistopped():
            embed(
                using="asyncio",
                user_ns={
                    "master": self.master,
                    "focus": self.master.view.focus.flow,
                    "flow": self.master.view.focus.flow,
                    "marked": [i for i in self.master.view._store.values() if i.marked],
                },
            )


addons = [IPython()]


# see remote-debug.py, could do an ipykernel too/instead?
