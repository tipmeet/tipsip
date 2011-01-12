from twisted.trial import unittest
from twisted.internet import defer


from tipsip.sip import Message, Request, Response
from tipsip.sip import AddressHeader, ViaHeader
from tipsip.sip import URI
from tipsip.sip import MessageParsingError


class RequestTest(unittest.TestCase):
    def test_constructRequest(self):
        aq = self.assertEqual
        r = Request('NOTIFY', 'sip:echo@tipmeet.com')
        s = str(r).split('\r\n', 1)
        aq(s[0], 'NOTIFY sip:echo@tipmeet.com SIP/2.0')
        aq(s[1], '\r\n')

    def test_createResponse(self):
        aq = self.assertEqual
        at = self.assertTrue
        req = Request('NOTIFY', 'sip:echo@tipmeet.com')
        req.headers['f'] = AddressHeader.parse('Carol <sip:carol@example.com> ;tag=abvgde123')
        req.headers['t'] = AddressHeader.parse("Echo <sip:echo@tipmeet.com>")
        req.headers['via'] = ViaHeader.parse("SIP/2.0/TCP 193.168.0.1:5061; received=10.10.10.10")
        req.headers['call-id'] = '1234@localhost'
        req.headers['cseq'] = '1'
        r = req.createResponse('180', 'Ringing')
        aq(str(r.headers['from']), 'Carol <sip:carol@example.com> ;tag=abvgde123')
        aq(str(r.headers['To'].uri), 'sip:echo@tipmeet.com')
        aq(r.headers['To'].display_name, 'Echo')
        aq(str(r.headers['Via']), 'SIP/2.0/TCP 193.168.0.1:5061 ;received=10.10.10.10')
        aq(r.headers['Call-Id'], '1234@localhost')
        aq(r.headers['CSeq'], '1')
        at('tag' in r.headers['To'].params)
        t1 = r.headers['to'].params['tag']
        at(isinstance(t1, basestring))
        r = req.createResponse('200', 'OK')
        t2 = r.headers['t'].params['tag']
        aq(t1, t2)

    def test_isValid(self):
        at = self.assertTrue
        af = self.assertFalse
        r = Request('NOTIFY', 'sip:echo@tipmeet.com')
        h = r.headers
        af(r.isValid())
        h['f'] = AddressHeader.parse('sip:echo@tipmeet.com')
        af(r.isValid())
        h['To'] = 'sip:echo@tipmeet.com'
        af(r.isValid())
        h['v'] = 'via'
        af(r.isValid())
        h['call-id'] = 'abracadabra'
        af(r.isValid())
        h['CSEQ'] = '1'
        af(r.isValid())
        h['Max-Forwards'] = '30'
        af(r.isValid())
        r.headers['from'].params['tag'] = 'cadabra'
        at(r.isValid())

    def test_malformed_parsing(self):
        ar = self.assertRaises
        ar(MessageParsingError, Message.parse, "")
        ar(MessageParsingError, Message.parse, "\r\n")
        ar(MessageParsingError, Message.parse, "SIP/2.0 200 OK")
        ar(MessageParsingError, Message.parse, "INVITE SIP/2.0\r\n")
        ar(MessageParsingError, Message.parse, "SIP/2.0\r\n")
        ar(MessageParsingError, Message.parse, "TEST 200 OK\r\n")
        ar(MessageParsingError, Message.parse, "INVITE sip:echo@tipmeet.com SIP/2.0\r\nMax-Forwards: 2\r\n")

    def test_request_parsing(self):
        at = self.assertTrue
        aq = self.assertEqual
        r = Message.parse("INVITE sip:echo@tipmeet.com SIP/2.0\r\n\r\n")
        at(isinstance(r, Request))
        aq(r.method, "INVITE")
        aq(str(r.ruri), 'sip:echo@tipmeet.com')
        aq(str(r), "INVITE sip:echo@tipmeet.com SIP/2.0\r\n\r\n")
        r = Message.parse("INVITE sip:echo@tipmeet.com;transport=TCP SIP/2.0\r\nMax-Forwards: 30\r\n\r\nabacaba")
        at(isinstance(r, Request))
        aq(r.method, "INVITE")
        aq(str(r.ruri), 'sip:echo@tipmeet.com;transport=TCP')
        aq(r.content, 'abacaba')
        aq(str(r), "INVITE sip:echo@tipmeet.com;transport=TCP SIP/2.0\r\nMax-Forwards: 30\r\n\r\nabacaba")
        r = Message.parse("REGISTER sip:tipmeet.com SIP/2.0\r\nContact: *\r\nExpires: 0\r\n\r\n")
        at(isinstance(r, Request))
        aq(r.method, 'REGISTER')
        aq(str(r.ruri), 'sip:tipmeet.com')
        aq(r.headers['contact'], '*')
        aq(r.headers['expires'], '0')
        r = Message.parse('PUBLISH sip:resource@tipmeet.com SIP/2.0\r\nFrom: ivaxer <sip:echo@tipmeet.com> ;tag=123\r\n\r\n')
        at(isinstance(r, Request))
        aq(r.method, 'PUBLISH')
        aq(str(r.ruri), 'sip:resource@tipmeet.com')
        aq(str(r.headers['from'].uri), 'sip:echo@tipmeet.com')
        aq(r.headers['from'].display_name, 'ivaxer')
        aq(r.headers['from'].params['tag'], '123')
        aq(str(r), 'PUBLISH sip:resource@tipmeet.com SIP/2.0\r\nFrom: ivaxer <sip:echo@tipmeet.com> ;tag=123\r\n\r\n')
        r = Message.parse('ACK sip:echo@192.168.1.0:5066;transport=TCP SIP/2.0\r\nVia: SIP/2.0/UDP server10.biloxi.com ;branch=z9hG4bKnashds8\r\nVia: SIP/2.0/TCP bigbox3.site3.atlanta.com ;branch=z9hG4bK77ef4c2312983.1\r\n\r\n')
        aq(r.method, 'ACK')
        aq(str(r.ruri), 'sip:echo@192.168.1.0:5066;transport=TCP')
        aq(r.headers['via'][0].transport, 'UDP')
        aq(r.headers['via'][0].host, 'server10.biloxi.com')
        aq(r.headers['via'][1].transport, 'TCP')
        aq(r.headers['via'][1].host, 'bigbox3.site3.atlanta.com')
        aq(str(r), 'ACK sip:echo@192.168.1.0:5066;transport=TCP SIP/2.0\r\nVia: SIP/2.0/UDP server10.biloxi.com ;branch=z9hG4bKnashds8\r\nVia: SIP/2.0/TCP bigbox3.site3.atlanta.com ;branch=z9hG4bK77ef4c2312983.1\r\n\r\n')
        r = Message.parse('NOTIFY sip:echo@tipmeet.com SIP/2.0\r\nRecord-Route: <sip:server10.biloxi.com;lr>,\r\n\t<sip:bigbox3.site3.atlanta.com;lr>\r\n\r\n')
        aq(str(r.headers['record-route'][0].uri), 'sip:server10.biloxi.com;lr')
        aq(str(r.headers['record-route'][1].uri), 'sip:bigbox3.site3.atlanta.com;lr')
        aq(str(r), 'NOTIFY sip:echo@tipmeet.com SIP/2.0\r\nRecord-Route: <sip:server10.biloxi.com;lr>\r\nRecord-Route: <sip:bigbox3.site3.atlanta.com;lr>\r\n\r\n')

    def test_response_parsing(self):
        at = self.assertTrue
        aq = self.assertEqual
        r = Message.parse('SIP/2.0 200 OK\r\n\r\n')
        at(isinstance(r, Response))
        aq(r.code, 200)
        aq(r.reason, 'OK')
        r = Message.parse('SIP/2.0 100 Trying\r\nTo: Bob <sip:bob@biloxi.com>\r\nCSeq: 314159 INVITE\r\nContent-Length: 0\r\n\r\n')
        aq(r.code, 100)
        aq(r.reason, 'Trying')
        aq(r.headers['t'].display_name, 'Bob')
        aq(str(r.headers['t'].uri), 'sip:bob@biloxi.com')
        aq(str(r.headers['t']), 'Bob <sip:bob@biloxi.com>')
        aq(r.headers['cseq'], '314159 INVITE')
        aq(r.headers['content-length'], '0')
        r = Message.parse('SIP/2.0 180 Ringing\r\nContact: <sip:bob@192.0.2.4>\r\n\r\nblabla')
        aq(str(r), 'SIP/2.0 180 Ringing\r\nContact: <sip:bob@192.0.2.4>\r\n\r\nblabla')

