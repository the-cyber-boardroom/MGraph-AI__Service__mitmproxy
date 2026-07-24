from unittest                                                               import TestCase
from unittest.mock                                                          import patch
from mgraph_ai_service_mitmproxy.service.proxy.inject.Proxy__Inject__Service import Proxy__Inject__Service

TEST_SCRIPT = 'console.log("mitm-filter")'


class test_Proxy__Inject__Service(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.inject_service = Proxy__Inject__Service()

    def inject(self, html, host='www.example.com'):
        with patch.object(Proxy__Inject__Service, 'resolve_script', return_value=TEST_SCRIPT):
            return self.inject_service.inject_script_into_html(html=html, host=host)

    def test_inject_script_into_html__ascii(self):                                       # baseline: script lands just before </body>
        html = '<html><body><p>hello</p></body></html>'
        (modified, headers_to_add, headers_to_remove) = self.inject(html)

        assert TEST_SCRIPT in modified
        assert modified.index('id="mitm-inject"') < modified.index('</body>')
        assert modified.endswith('</body></html>')
        assert headers_to_add['x-mitm-inject'] == 'true'

    def test_inject_script_into_html__unicode_length_changing(self):                     # regression: 'İ'.lower() is 2 chars, which used to skew the splice index
        assert len('İ'.lower()) == 2                                                     # the property the old code tripped over

        html = '<html><body><p>İSTANBUL İZMİR İNGİLTERE</p></body></html>'
        (modified, _, _) = self.inject(html)

        assert '</body></html>' in modified                                              # closing tags intact (old code produced 'y></html>' style corruption)
        assert modified.count('</body>') == 1
        assert modified.index('id="mitm-inject"') < modified.index('</body>')
        assert '</bod\n' not in modified

    def test_inject_script_into_html__uppercase_body_tag(self):                          # case-insensitive matching preserved
        html = '<HTML><BODY><P>HELLO</P></BODY></HTML>'
        (modified, _, _) = self.inject(html)

        assert modified.endswith('</BODY></HTML>')
        assert modified.index('id="mitm-inject"') < modified.index('</BODY>')

    def test_inject_script_into_html__multiple_body_tags(self):                          # rfind semantics kept: inject before the LAST </body>
        html = '<html><body><iframe></body></iframe><p>real</p></body></html>'
        (modified, _, _) = self.inject(html)

        assert modified.endswith('</body></html>')
        assert modified.index('id="mitm-inject"') > modified.index('</body>')            # after the first one
        assert modified.index('id="mitm-inject"') < modified.rindex('</body>')           # before the last one

    def test_inject_script_into_html__no_body_tag(self):                                 # fallback: append at the end
        html = '<html><p>fragment</p></html>'
        (modified, _, _) = self.inject(html)

        assert modified.endswith('</script>')
        assert TEST_SCRIPT in modified
