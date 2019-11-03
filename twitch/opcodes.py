from collections import namedtuple

"""
connection management opcodes
----------------------------
PING = 'PING'
PONG = 'PONG'
NICK = 'NICK'
PASS = 'PASS'


capability request opcodes
----------------------------
CAP = 'CAP'
ACK = 'ACK'
REQ = 'REQ'

general opcodes
----------------------------
PRIVMSG = 'PRIVMSG'

membership opcodes
----------------------------
JOIN = 'JOIN' 
PART = 'PART'
MODE = 'MODE'
NAMES ='NAMES' 

commands opcodes
----------------------------
CLEARCHAT = 'CLEARCHAT'
CLEARMSG = 'CLEARMSG'
HOSTTARGET = 'HOSTTARGET'
NOTICE = 'NOTICE'
RECONNECT = 'RECONNECT' 
ROOMSTATE = 'ROOMSTATE'
USERNOTICE = 'USERNOTICE'
USERSTATE = 'USERSTATE'
"""

OpCodeDef = namedtuple('OpCodeDef', 'PING '
                                    'PONG '
                                    'NICK '
                                    'PASS '
                                    'PRIVMSG '
                                    'JOIN '
                                    'PART '
                                    'MODE '
                                    'CLEARCHAT '
                                    'CLEARMSG '
                                    'HOSTTARGET '
                                    'NOTICE '
                                    'RECONNECT '
                                    'ROOMSTATE '
                                    'USERNOTICE '
                                    'USERSTATE '
                                    'CAP '
                                    'ACK '
                                    'REQ')

OpCode = OpCodeDef(PING='PING',
                   PONG='PONG',
                   NICK='NICK',
                   PASS='PASS',
                   PRIVMSG='PRIVMSG',
                   JOIN='JOIN',
                   PART='PART',
                   MODE='MODE',
                   CLEARCHAT='CLEARCHAT',
                   CLEARMSG='CLEARMSG',
                   HOSTTARGET='HOSTTARGET',
                   NOTICE='NOTICE',
                   RECONNECT='RECCONNECT',
                   ROOMSTATE='ROOMSTATE',
                   USERNOTICE='USERNOTICE',
                   USERSTATE='USERSTATE',
                   CAP='CAP',
                   ACK='ACK',
                   REQ='REQ')
