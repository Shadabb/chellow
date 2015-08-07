from net.sf.chellow.monad import Monad
import templater
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
GBatch, GContract = db.GBatch, db.GContract
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('g_contract_id')
        contract = GContract.get_by_id(sess, contract_id)
        batches = sess.query(GBatch).filter(GBatch.g_contract == contract) \
            .order_by(GBatch.reference.desc())
        render(inv, template, {'contract': contract, 'batches': batches})
finally:
    if sess is not None:
        sess.close()
