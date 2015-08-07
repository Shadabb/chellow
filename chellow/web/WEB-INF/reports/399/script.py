from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta
import utils
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
HH = utils.HH
GRateScript = db.GRateScript
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()

    contract_id = inv.getLong('g_contract_id')
    contract = db.GContract.get_by_id(sess, contract_id)
    rate_scripts = sess.query(GRateScript).filter(
        GRateScript.g_contract == contract).order_by(
        GRateScript.start_date.desc()).all()

    now = datetime.datetime.utcnow() - relativedelta(months=1)
    month_start = datetime.datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH

    templater.render(
        inv, template, {
            'contract': contract, 'month_start': month_start,
            'month_finish': month_finish, 'rate_scripts': rate_scripts})
finally:
    if sess is not None:
        sess.close()
