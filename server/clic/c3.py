# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(__file__)
CLIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

from cheshire3.baseObjects import Session
from cheshire3.server import SimpleServer

session = Session()
session.database = 'db_dickens'

server = SimpleServer(
    session,
    os.path.join(CLIC_DIR, 'cheshire3-server', 'configs', 'serverConfig.xml')
)
db = server.get_object(session, session.database)
qf = db.get_object(session, 'defaultQueryFactory')
recStore = db.get_object(session, 'recordStore')
idxStore = db.get_object(session, 'indexStore')
#logger = db.get_object(session, 'concordanceLogger')
