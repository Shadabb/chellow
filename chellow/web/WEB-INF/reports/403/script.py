from net.sf.chellow.monad import Monad
import db
import templater
import utils
import simplejson as json
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GContract = db.GContract
render = templater.render
UserException, form_int = utils.UserException, utils.form_int
form_str, form_bool = utils.form_str, utils.form_bool
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, g_contract, message=None):
    messages = None if message is None else [str(message)]
    return {'g_contract': g_contract, 'messages': messages}


sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        g_contract_id = form_int(inv, 'g_contract_id')
        g_contract = GContract.get_by_id(sess, g_contract_id)
        render(inv, template, make_fields(sess, g_contract))
    else:
        db.set_read_write(sess)
        g_contract_id = form_int(inv, 'g_contract_id')
        g_contract = GContract.get_by_id(sess, g_contract_id)
        if inv.hasParameter('delete'):
            g_contract.delete(sess)
            sess.commit()
            inv.sendSeeOther('/reports/395/output/')
        else:
            name = form_str(inv, 'name')
            charge_script = form_str(inv, 'charge_script')
            properties = form_str(inv, 'properties')
            g_contract.update(
                sess, name, charge_script, json.loads(properties))
            sess.commit()
            inv.sendSeeOther(
                '/reports/399/output/?g_contract_id=' + str(g_contract.id))
except UserException, e:
    sess.rollback()
    if str(e).startswith("There isn't a contract"):
        inv.sendNotFound(str(e))
    else:
        render(inv, template, make_fields(sess, g_contract, e), 400)
finally:
    if sess is not None:
        sess.close()
