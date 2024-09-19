"""
Preview and edit SAML XML in requests.

Inspired by https://github.com/simplesamlphp/SAML-tracer

This extension detects SAMLRequest and SAMLResponse in requests and supports:
- extracting and pretty printing SAML XML for preview
- editing SAML XML with your $EDITOR
- automatically editing SAML XML in request()
- flows with SAML are marked with "S"

"SAML" may be selected as the "flow view mode" to enable pretty printing. The
keyboard shortcut "s" or the "saml.edit" command may be used to edit SAML with
your default $EDITOR.  Editing only works in console mitmproxy, SAML viewing
still works in mitmweb however.

Note, editing SAML XML may invalidate SAML signatures.

Unlike SAML-tracer, this addon does not support SAMLArt or WS-Fed.
"""

import base64
import zlib
from collections.abc import Sequence
from typing import cast

from mitmproxy import addonmanager
from mitmproxy import command
from mitmproxy import contentviews
from mitmproxy import exceptions
from mitmproxy import flow
from mitmproxy import http
from mitmproxy.contentviews import xml_html
from mitmproxy.coretypes import multidict
from mitmproxy.tools.console.master import ConsoleMaster

form_types = [
    "query",
    "urlencoded_form",
    "multipart_form",
]


def get_saml(request: http.Request):
    for form_type in form_types:
        form = cast(
            multidict.MultiDictView[str, str], getattr(request, form_type, None)
        )
        if form:
            if "SAMLRequest" in form:
                saml_parameter = "SAMLRequest"
            elif "SAMLResponse" in form:
                saml_parameter = "SAMLResponse"
            else:
                continue

            saml = base64.b64decode(form[saml_parameter])

            set_saml = None
            if form_type == "query":
                try:
                    saml = zlib.decompress(saml, wbits=-15)
                    set_saml = lambda saml: form.set_all(  # noqa: E731
                        saml_parameter,
                        [str(base64.b64encode(zlib.compress(saml, wbits=-15)))],
                    )
                except zlib.error:
                    # If we get a zlib parse error, ignore it and guess that the data is uncompressed
                    pass
            if not set_saml:
                set_saml = lambda saml: form.set_all(  # noqa: E731
                    saml_parameter, [str(base64.b64encode(saml))]
                )

            return saml_parameter, set_saml, saml


class ViewSAML(xml_html.ViewXmlHtml):
    name = "SAML"

    def __call__(
        self,
        data: bytes,
        *unknown_args,
        content_type: str | None = None,
        flow: flow.Flow | None = None,
        http_message: http.Message | None = None,
        **unknown_metadata,
    ) -> contentviews.TViewResult:
        if not isinstance(http_message, http.Request):
            raise exceptions.CommandError("Not a Request.")

        # Extract SAML XML from request
        if parsed_saml := get_saml(http_message):
            saml_parameter, _, saml = parsed_saml
            # Reuse ViewXmlHtml's XML formatter
            _, formatted_xml = super().__call__(saml)
            # But override the format name to be SAMLRequest/SAMLResponse
            return saml_parameter, formatted_xml

        raise exceptions.CommandError("Could not parse SAML.")

    def render_priority(
        self,
        data: bytes,
        *,
        content_type: str | None = None,
        flow: flow.Flow | None = None,
        http_message: http.Message | None = None,
        **unknown_metadata,
    ) -> float:
        if isinstance(http_message, http.Request):
            if get_saml(http_message):
                return 2
        return 0


view = ViewSAML()
master: ConsoleMaster | None = None


def load(loader: addonmanager.Loader):
    global master

    contentviews.add(view)

    if isinstance(loader.master, ConsoleMaster):
        master = loader.master
        # Ideally this could be added to consoleaddons edit_focus(), but that isn't extensible
        master.keymap.add("s", "saml.edit @focus", ["flowview"], "Edit SAML")


def done():
    contentviews.remove(view)
    if master:
        master.keymap.remove("s", ["flowview"])


@command.command("saml.edit")
def saml_edit(flows: Sequence[flow.Flow]) -> None:
    if not master:
        raise exceptions.CommandError(
            "SAML addon error: Must be loaded as a mitmproxy console addon."
        )

    if len(flows) > 1:
        raise exceptions.CommandError("Multiple flows not supported.")
    elif not (len(flows) == 1 and isinstance(flows[0], http.HTTPFlow)):
        raise exceptions.CommandError("No flow selected.")
    flow = flows[0]

    parsed_saml = get_saml(flow.request)
    if not parsed_saml:
        raise exceptions.CommandError("SAML not detected.")

    flow.backup()

    _, set_saml, saml = parsed_saml
    saml = master.spawn_editor(saml)
    set_saml(saml)


def request(flow: flow.Flow) -> None:
    if not isinstance(flow, http.HTTPFlow):
        return

    parsed_saml = get_saml(flow.request)
    if parsed_saml:
        saml_parameter, set_saml, saml = parsed_saml

        # Mark SAML flows
        flow.marked = "S"

        # Optionally, perform an automated transformation on the SAML:
        # if saml_parameter == "SAMLResponse":
        #     saml = ...
        #     set_saml(saml)

        # Or automatically generate a SAMLResponse for any SAMLRequest, skipping the IdP:
        # if saml_parameter == "SAMLRequest":
        #     flow.response = http.Response.make(
        #         200,
        #         b"<form method=post onload='document.forms[0].submit()' action='...'>...</form>",  # respond with a SAMLResponse <form>
        #         {"Content-Type": "text/html"},
        #     )
