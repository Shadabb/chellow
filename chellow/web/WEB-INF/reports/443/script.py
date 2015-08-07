from net.sf.chellow.monad import Monad
import utils
import templater
import db
import json

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
UserException = utils.UserException
render = templater.render
GBill, BillType = db.GBill, db.BillType
form_date, form_decimal = utils.form_date, utils.form_decimal
form_int, form_str = utils.form_int, utils.form_str
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, g_bill, message=None):
    bill_types = sess.query(BillType).order_by(BillType.code).all()
    messages = [] if message is None else [str(message)]
    return {'g_bill': g_bill, 'bill_types': bill_types, 'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        g_bill_id = form_int(inv, 'g_bill_id')
        g_bill = GBill.get_by_id(sess, g_bill_id)
        render(inv, template, make_fields(sess, g_bill))
    else:
        db.set_read_write(sess)
        g_bill_id = inv.getLong('g_bill_id')
        g_bill = GBill.get_by_id(sess, g_bill_id)
        if inv.hasParameter("delete"):
            g_batch_id = g_bill.g_batch.id
            g_bill.delete(sess)
            sess.commit()
            inv.sendSeeOther(
                "/reports/417/output/?g_batch_id=" + str(g_batch_id))
        else:
            account = inv.getString("account")
            reference = inv.getString("reference")
            issue_date = form_date(inv, "issue")
            start_date = form_date(inv, "start")
            finish_date = form_date(inv, "finish")
            kwh = form_decimal(inv, "kwh")
            net_gbp = form_decimal(inv, 'net_gbp')
            vat_gbp = form_decimal(inv, 'vat_gbp')
            gross_gbp = form_decimal(inv, 'gross_gbp')
            type_id = inv.getLong("bill_type_id")
            raw_lines = form_str(inv, 'raw_lines')
            breakdown_str = inv.getString('breakdown')
            breakdown = json.loads(breakdown_str)
            bill_type = BillType.get_by_id(sess, type_id)

            g_bill.update(
                bill_type, reference, account, issue_date, start_date,
                finish_date, kwh, net_gbp, vat_gbp, gross_gbp, raw_lines,
                breakdown)
            sess.commit()
            inv.sendSeeOther(
                "/reports/427/output/?g_bill_id=" + str(g_bill.id))

except UserException, e:
    render(inv, template, make_fields(sess, g_bill, e))
finally:
    if sess is not None:
        sess.close()
