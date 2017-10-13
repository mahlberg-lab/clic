import StringIO
import tempfile
import unittest
import os
from lxml import etree

from clic.clicdb import ClicDb


class MockRecord():
    """Just enough cheshire3 record to survive"""
    def __init__(self, id, dom_str, digest="omnomnom"):
        self.id = id
        self.dom = etree.parse(StringIO.StringIO(dom_str))
        self.digest = digest


class TestClicDb(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            self.temp_db = tmpfile.name
        self.cdb = ClicDb(rdb_file=self.temp_db)
        self.cdb.create_schema()

    def tearDown(self):
        self.cdb.close()
        os.remove(self.temp_db)

    def test_rdb_index_record_phantom_quotes(self):
        """Make sure we handle the qs/qe inserted to ensure cheshire3 indexes properly"""
        self.cdb.rdb_index_record(MockRecord(1, """
<div id="OT.9" book="OT" type="chapter" num="9">
<qe eid="1"/>
<title>CHAPTER IX CONTAINING FURTHER PARTICULARS CONCERNING THE PLEASANT OLD GENTLEMAN, AND HIS HOPEFUL PUPILS</title>

<p pid="1" id="OT.c9.p1" eid="2">
  <s sid="1" id="OT.c9.s1" eid="3"><toks><w o="0">It</w><n> </n><w o="3">was</w><n> </n><w o="7">late</w><n> </n><w o="12">next</w><n> </n><w o="17">morning</w><n> </n><w o="25">when</w><n> </n><w o="30">Oliver</w><n> </n><w o="37">awoke</w><n>,</n><n> </n><w o="44">from</w><n> </n><w o="49">a</w><n> </n><w o="51">sound</w><n>,</n><n> </n><w o="58">long</w><n> </n><w o="63">sleep</w><n>.</n></toks></s>
  <s sid="2" id="OT.c9.s2" eid="4"><toks><w o="0">There</w><n> </n><w o="6">was</w><n> </n><w o="10">no</w><n> </n><w o="13">other</w><n> </n><w o="19">person</w><n> </n><w o="26">in</w><n> </n><w o="29">the</w><n> </n><w o="33">room</w><n> </n><w o="38">but</w><n> </n><w o="42">the</w><n> </n><w o="46">old</w><n> </n><w o="50">Jew</w><n>,</n><n> </n><w o="55">who</w><n> </n><w o="59">was</w><n> </n><w o="63">boiling</w><n> </n><w o="71">some</w><n> </n><w o="76">coffee</w><n> </n><w o="83">in</w><n> </n><w o="86">a</w><n> </n><w o="88">saucepan</w><n> </n><w o="97">for</w><n> </n><w o="101">breakfast</w><n>,</n><n> </n><w o="112">and</w><n> </n><w o="116">whistling</w><n> </n><w o="126">softly</w><n> </n><w o="133">to</w><n> </n><w o="136">himself</w><n> </n><w o="144">as</w><n> </n><w o="147">he</w><n> </n><w o="150">stirred</w><n> </n><w o="158">it</w><n> </n><w o="161">round</w><n> </n><w o="167">and</w><n> </n><w o="171">round</w><n>,</n><n> </n><w o="178">with</w><n> </n><w o="183">an</w><n> </n><w o="186">iron</w><n> </n><w o="191">spoon</w><n>.</n></toks></s>
  <s sid="3" id="OT.c9.s3" eid="5"><toks>
      <qs eid="6" wordOffset="50"/><w o="0">He</w><n> </n><w o="3">would</w><qe eid="7" wordOffset="51"/>
      <n> </n><w o="9">stop</w><n> </n><w o="14">every</w><n> </n><w o="20">now</w><n> </n><w o="24">and</w><n> </n><w o="28">then</w><n> </n><w o="33">to</w><n> </n><w o="36">listen</w><n> </n><w o="43">when</w><n> </n><w o="48">there</w><n> </n><w o="54">was</w><n> </n><w o="58">the</w><n> </n><w o="62">least</w><n> </n><w o="68">noise</w><n> </n><w o="74">below</w><n>:</n><n> </n><w o="81">and</w><n> </n><w o="85">when</w><n> </n><w o="90">he</w><n> </n><w o="93">had</w><n> </n><w o="97">satistified</w><n> </n><w o="109">himself</w><n>,</n><n> </n><w o="118">he</w><n> </n><w o="121">would</w><n> </n><w o="127">go</w><n> </n><w o="130">on</w><n> </n><w o="133">whistling</w><n> </n><w o="143">and</w><n> </n><w o="147">stirring</w><n> </n><w o="156">again</w><n>,</n><n> </n><w o="163">as</w><n> </n><w o="166">before</w><n>.</n></toks></s></p>
</div>
        """))
        out = self.cdb.rdb_query("SELECT subset_type, eid, offset_start, offset_end FROM subset").fetchall()
        self.assertEqual(out, [
            (u'quote', 0, 0, 0),
            (u'nonquote', 1, 0, 50),
            (u'quote', 6, 50, 51),  # NB: We believe the wordOffset, even though they're wrong
            (u'nonquote', 7, 51, 83),
        ])

    def test_rdb_index_record_finalnonqutote(self):
        """Final text ends up in a non-quote"""
        self.cdb.rdb_index_record(MockRecord(1, """
<div id="OT.9" book="OT" type="chapter" num="9">
<title>CHAPTER IX CONTAINING FURTHER PARTICULARS CONCERNING THE PLEASANT OLD GENTLEMAN, AND HIS HOPEFUL PUPILS</title>

<p pid="1" id="OT.c9.p1" eid="2">
  <s sid="1" id="OT.c9.s1" eid="3"><toks>
      <!-- Start a quote -->
      <qs eid="4" wordOffset="2"/><w o="0">It</w><n> </n><w o="3">was</w><qe eid="5" wordOffset="5"/>
      <!-- Rest of this text should be non-quote -->
      <n> </n><w o="7">late</w><n> </n><w o="12">next</w><n> </n><w o="17">morning</w><n> </n><w o="25">when</w><n> </n><w o="30">Oliver</w><n> </n><w o="37">awoke</w><n>,</n><n> </n><w o="44">from</w><n> </n><w o="49">a</w><n> </n><w o="51">sound</w><n>,</n><n> </n><w o="58">long</w><n> </n><w o="63">sleep</w><n>.</n>
  </toks></s>
</p>
</div>
        """))
        out = self.cdb.rdb_query("SELECT subset_type, eid, offset_start, offset_end FROM subset").fetchall()
        self.assertEqual(out, [
            (u'nonquote', 0, 0, 2),
            (u'quote', 4, 2, 5),
            (u'nonquote', 5, 5, 13)
        ])

    def test_rdb_index_record_all_nonquote(self):
        self.cdb.rdb_index_record(MockRecord(1, """
<div id="OT.9" book="OT" type="chapter" num="9">
<qe eid="1"/>
<title>CHAPTER IX CONTAINING FURTHER PARTICULARS CONCERNING THE PLEASANT OLD GENTLEMAN, AND HIS HOPEFUL PUPILS</title>

<p pid="1" id="OT.c9.p1" eid="2">
  <s sid="1" id="OT.c9.s1" eid="3"><toks><w o="0">It</w><n> </n><w o="3">was</w><n> </n><w o="7">late</w><n> </n><w o="12">next</w><n> </n><w o="17">morning</w><n> </n><w o="25">when</w><n> </n><w o="30">Oliver</w><n> </n><w o="37">awoke</w><n>,</n><n> </n><w o="44">from</w><n> </n><w o="49">a</w><n> </n><w o="51">sound</w><n>,</n><n> </n><w o="58">long</w><n> </n><w o="63">sleep</w><n>.</n></toks></s>
  <s sid="2" id="OT.c9.s2" eid="4"><toks><w o="0">There</w><n> </n><w o="6">was</w><n> </n><w o="10">no</w><n> </n><w o="13">other</w><n> </n><w o="19">person</w><n> </n><w o="26">in</w><n> </n><w o="29">the</w><n> </n><w o="33">room</w><n> </n><w o="38">but</w><n> </n><w o="42">the</w><n> </n><w o="46">old</w><n> </n><w o="50">Jew</w><n>,</n><n> </n><w o="55">who</w><n> </n><w o="59">was</w><n> </n><w o="63">boiling</w><n> </n><w o="71">some</w><n> </n><w o="76">coffee</w><n> </n><w o="83">in</w><n> </n><w o="86">a</w><n> </n><w o="88">saucepan</w><n> </n><w o="97">for</w><n> </n><w o="101">breakfast</w><n>,</n><n> </n><w o="112">and</w><n> </n><w o="116">whistling</w><n> </n><w o="126">softly</w><n> </n><w o="133">to</w><n> </n><w o="136">himself</w><n> </n><w o="144">as</w><n> </n><w o="147">he</w><n> </n><w o="150">stirred</w><n> </n><w o="158">it</w><n> </n><w o="161">round</w><n> </n><w o="167">and</w><n> </n><w o="171">round</w><n>,</n><n> </n><w o="178">with</w><n> </n><w o="183">an</w><n> </n><w o="186">iron</w><n> </n><w o="191">spoon</w><n>.</n></toks></s>
  <s sid="3" id="OT.c9.s3" eid="5"><toks>
      <n> </n><w o="9">stop</w><n> </n><w o="14">every</w><n> </n><w o="20">now</w><n> </n><w o="24">and</w><n> </n><w o="28">then</w><n> </n><w o="33">to</w><n> </n><w o="36">listen</w><n> </n><w o="43">when</w><n> </n><w o="48">there</w><n> </n><w o="54">was</w><n> </n><w o="58">the</w><n> </n><w o="62">least</w><n> </n><w o="68">noise</w><n> </n><w o="74">below</w><n>:</n><n> </n><w o="81">and</w><n> </n><w o="85">when</w><n> </n><w o="90">he</w><n> </n><w o="93">had</w><n> </n><w o="97">satistified</w><n> </n><w o="109">himself</w><n>,</n><n> </n><w o="118">he</w><n> </n><w o="121">would</w><n> </n><w o="127">go</w><n> </n><w o="130">on</w><n> </n><w o="133">whistling</w><n> </n><w o="143">and</w><n> </n><w o="147">stirring</w><n> </n><w o="156">again</w><n>,</n><n> </n><w o="163">as</w><n> </n><w o="166">before</w><n>.</n></toks></s></p>
</div>
        """))
        out = self.cdb.rdb_query("SELECT subset_type, eid, offset_start, offset_end FROM subset").fetchall()
        self.assertEqual(out, [
            (u'quote', 0, 0, 0),
            (u'nonquote', 1, 0, 81),
        ])
