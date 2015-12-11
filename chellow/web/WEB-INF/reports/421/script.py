from net.sf.chellow.monad import Monad
import db
import templater
import utils

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
GBatch = db.GBatch
UserException = utils.UserException

inv, template = globals()['inv'], globals()['template']


def make_fields(sess, batch, message=None):
    messages = [] if message is None else [str(message)]
    return {'batch': batch, 'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('g_batch_id')
        batch = GBatch.get_by_id(sess, batch_id)
        render(inv, template, make_fields(sess, batch))
    else:
        db.set_read_write(sess)
        batch_id = inv.getLong('g_batch_id')
        batch = GBatch.get_by_id(sess, batch_id)
        if inv.hasParameter('update'):
            reference = inv.getString('reference')
            description = inv.getString('description')
            batch.update(sess, reference, description)
            sess.commit()
            inv.sendSeeOther(
                "/reports/417/output/?g_batch_id=" + str(batch.id))
        elif inv.hasParameter("delete"):
            contract_id = batch.g_contract.id
            batch.delete(sess)
            sess.commit()
            inv.sendSeeOther(
                "/reports/413/output/?g_contract_id=" + str(contract_id))
except UserException, e:
    render(inv, template, make_fields(sess, batch, e), 400)
finally:
    sess.close()