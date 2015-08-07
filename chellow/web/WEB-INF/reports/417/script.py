from net.sf.chellow.monad import Monad
import db
import templater
from sqlalchemy.orm import joinedload
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GBatch, GBill, GContract, Report = db.GBatch, db.GBill, db.GContract, db.Report
Contract = db.Contract
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('g_batch_id')
        batch = GBatch.get_by_id(sess, batch_id)
        bills = sess.query(GBill).options(joinedload('g_reads')).filter(
            GBill.g_batch == batch).order_by(
            GBill.reference, GBill.start_date).all()
        if len(bills) > 0:
            max_reads = max([len(bill.g_reads) for bill in bills])
        else:
            max_reads = 0
        config_contract = Contract.get_non_core_by_name(sess, 'configuration')
        properties = config_contract.make_properties()
        fields = {'batch': batch, 'bills': bills, 'max_reads': max_reads}
        if 'batch_reports' in properties:
            batch_reports = []
            for report_id in properties['batch_reports']:
                batch_reports.append(Report.get_by_id(sess, report_id))
            fields['batch_reports'] = batch_reports
        render(inv, template, fields)
finally:
    if sess is not None:
        sess.close()
