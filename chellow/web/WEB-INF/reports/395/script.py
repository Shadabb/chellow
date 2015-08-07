from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GContract = db.GContract
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    contracts = sess.query(GContract).order_by(GContract.name)
    render(inv, template, {'contracts': contracts})
finally:
    if sess is not None:
        sess.close()
