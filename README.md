# mitmproxy-addons

## [saml.py](saml.py)

Preview and edit SAML XML in requests.

Inspired by https://github.com/simplesamlphp/SAML-tracer

This extension detects SAMLRequest and SAMLResponse in requests and supports:
- extracting and pretty printing SAML XML for preview
- editing SAML XML with your `$EDITOR`
- automatically editing SAML XML in `request()`
- flows with SAML are marked with `S`

"SAML" may be selected as the "flow view mode" to enable pretty printing. The keyboard shortcut <kbd>s</kbd> or the `saml.edit` command may be used to edit SAML with your default $EDITOR. Editing only works in console mitmproxy, SAML viewing still works in mitmweb however.

Note, editing SAML XML may invalidate SAML signatures.

Unlike SAML-tracer, this addon does not support SAMLArt or S-Fed.
