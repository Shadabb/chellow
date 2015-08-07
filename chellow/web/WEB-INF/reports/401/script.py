from sqlalchemy import null
from net.sf.chellow.monad import Monad
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GContract = db.GContract
UserException, form_date = utils.UserException, utils.form_date
validate_hh_start, form_json = utils.validate_hh_start, utils.form_json
form_bool = utils.form_bool
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, message=None):
    contracts = sess.query(GContract).filter(
        GContract.charge_script == null()).order_by(GContract.name)
    messages = [] if message is None else [str(e)]
    return {'contracts': contracts, 'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        templater.render(inv, template, make_fields(sess))
    else:
        db.set_read_write(sess)
        is_system = form_bool(inv, "is_system")
        name = inv.getString("name")
        start_date = form_date(inv, "start")
        validate_hh_start(start_date)
        charge_script = inv.getString("charge_script")
        properties = form_json(inv, "properties")

        contract = GContract.insert(
            sess, name, charge_script, properties, start_date, None, {})
        sess.commit()
        inv.sendSeeOther(
            "/reports/399/output/?g_contract_id=" + str(contract.id))
except UserException, e:
    sess.rollback()
    templater.render(inv, template, make_fields(sess, e), 400)
finally:
    if sess is not None:
        sess.close()
