from net.sf.chellow.monad import Monad
import db
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
GReadType = db.GReadType
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    g_read_type_id = inv.getLong('g_read_type_id')
    g_read_type = GReadType.get_by_id(sess, g_read_type_id)
    render(inv, template, {'g_read_type': g_read_type})
finally:
    if sess is not None:
        sess.close()
