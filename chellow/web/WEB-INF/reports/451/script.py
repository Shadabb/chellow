from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
GReadType = db.GReadType
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    g_read_types = sess.query(GReadType).order_by(GReadType.code).all()
    templater.render(inv, template, {'g_read_types': g_read_types})
finally:
    if sess is not None:
        sess.close()
