from net.sf.chellow.monad import Monad
from dateutil.relativedelta import relativedelta
import datetime
import pytz
import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import db
import utils
import computer
import g_engine
Monad.getUtils()['impt'](globals(), 'utils', 'db', 'g_engine')
GContract, GEra, Site, SiteGEra = db.GContract, db.GEra, db.Site, db.SiteGEra
HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format
inv = globals()['inv']

report_context = {}
sess = None
start_date = utils.form_date(inv, 'start')
finish_date = utils.form_date(inv, 'finish')
contract_id = inv.getLong('g_contract_id')


def content():
    try:
        sess = db.session()

        contract = GContract.get_by_id(sess, contract_id)
        forecast_date = computer.forecast_date()

        month_start = datetime.datetime(
            start_date.year, start_date.month, 1, tzinfo=pytz.utc)

        month_finish = month_start + relativedelta(months=1) - HH

        bill_titles = computer.contract_func(
            report_context, contract, 'virtual_bill_titles', None)()
        yield ','.join(
            [
                'MPRN', 'Site Code', 'Site Name', 'Account', 'From', 'To'] +
            bill_titles) + '\n'

        while not month_start > finish_date:
            period_start = start_date \
                if month_start < start_date else month_start

            if month_finish > finish_date:
                period_finish = finish_date
            else:
                period_finish = month_finish

            for g_era in sess.query(GEra).distinct().filter(
                    or_(
                        GEra.imp_g_contract == contract,
                        GEra.exp_g_contract == contract),
                    GEra.start_date <= period_finish,
                    or_(
                        GEra.finish_date == null(),
                        GEra.finish_date >= period_start)):

                g_era_start = g_era.start_date
                if period_start < g_era_start:
                    chunk_start = g_era_start
                else:
                    chunk_start = period_start
                g_era_finish = g_era.finish_date
                if hh_after(period_finish, g_era_finish):
                    chunk_finish = g_era_finish
                else:
                    chunk_finish = period_finish

                polarities = []
                if g_era.imp_g_contract == contract:
                    polarities.append(True)
                if g_era.exp_g_contract == contract:
                    polarities.append(False)
                for polarity in polarities:
                    data_source = g_engine.DataSource(
                        sess, chunk_start, chunk_finish, forecast_date, g_era,
                        polarity, None, report_context)

                    site = sess.query(Site).join(SiteGEra).filter(
                        SiteGEra.g_era == g_era,
                        SiteGEra.is_physical == true()).one()

                    yield ','.join('"' + str(value) + '"' for value in [
                        data_source.mprn, site.code, site.name,
                        data_source.supplier_account,
                        hh_format(data_source.start_date),
                        hh_format(data_source.finish_date)])

                    computer.contract_func(
                        report_context, contract, 'virtual_bill',
                        None)(data_source)
                    bill = data_source.bill
                    for title in bill_titles:
                        if title in bill:
                            val = str(bill[title])
                            del bill[title]
                        else:
                            val = ''
                        yield ',"' + val + '"'

                    for k in sorted(bill.keys()):
                        yield ',"' + k + '","' + str(bill[k]) + '"'
                    yield '\n'

            month_start += relativedelta(months=1)
            month_finish = month_start + relativedelta(months=1) - HH
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name='gas_virtual_bills.csv')
