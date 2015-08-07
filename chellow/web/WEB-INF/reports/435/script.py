from net.sf.chellow.monad import Monad
import db
import utils
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GBatch, GBill, GSupply = db.GBatch, db.GBill, db.GSupply
render = templater.render
UserException, parse_mpan_core = utils.UserException, utils.parse_mpan_core
form_date, validate_hh_start = utils.form_date, utils.validate_hh_start
form_decimal = utils.form_decimal

inv, template = globals()['inv'], globals()['template']


def make_fields(sess, batch, message=None):
    bills = sess.query(GBill).filter(GBill.g_batch == batch).order_by(
        GBill.start_date)
    messages = [] if message is None else [str(e)]
    return {'batch': batch, 'messages': messages, 'bills': bills}

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
        mprn = inv.getString("mprn")
        account = inv.getString("account")
        reference = inv.getString("reference")
        issue_date = form_date(inv, "issue")
        start_date = form_date(inv, "start")
        validate_hh_start(start_date)
        finish_date = form_date(inv, "finish")
        validate_hh_start(finish_date)
        kwh = form_decimal(inv, "kwh")
        net = form_decimal(inv, "net")
        vat = form_decimal(inv, "vat")
        gross = form_decimal(inv, "gross")
        breakdown_str = inv.getString("breakdown")

        breakdown = eval(breakdown_str)
        bill = batch.insert_bill(
            sess, account, reference, issue_date, start_date, finish_date, kwh,
            net, vat, gross, breakdown, GSupply.get_by_mprn(sess, mprn))
        sess.commit()
        inv.sendSeeOther(
            "/reports/417/output/?g_batch_id=" + str(batch.id))

except UserException, e:
    sess.rollback()
    render(inv, template, make_fields(sess, batch, e), 400)
finally:
    if sess is not None:
        sess.close()
