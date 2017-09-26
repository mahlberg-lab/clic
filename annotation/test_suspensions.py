import unittest
from lxml import etree

from suspensions import suspensions

class TestSuspensions(unittest.TestCase):
    def test_colon_at_end(self):
        """If there's a sentence break it's not a suspension"""
        out = suspensions(etree.fromstring("""
          <div>
            <p>
              <s>
                <w>That's</w><n></n><w>what</w><n></n><w>she</w><n></n><w>did</w>
                <qe/>
                <n>,"</n><n></n><w>said</w><n></n><w>Joe</w><n>,</n><n></n><w>slowly</w><n></n>
                <w>clearing</w><n></n><w>the</w><n></n><w>fire</w><n></n><w>between</w><n></n>
                <w>the</w><n></n><w>lower</w><n></n><w>bars</w><n></n><w>with</w><n></n>
                <w>the</w><n></n><w>poker</w><n>,</n><n></n><w>and</w><n></n><w>looking</w>
                <n></n><w>at</w><n></n><w>it</w><n>:</n>
              </s>
              <s>
                <qs/>
                <n>"</n><w>she</w><n></n><w>Ram-paged</w><n></n><w o="15">out</w><n>,</n>
                <n></n><w>Pip</w><n>."</n>
              </s>
            </p>
            <p>
              <qe/>
            </p>
          </div>
        """))
        self.assertTrue('<sls/>' not in etree.tostring(out))


if __name__ == '__main__':
    unittest.main()
