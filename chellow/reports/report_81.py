from datetime import datetime as Datetime
import pytz
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from dateutil.relativedelta import relativedelta
import traceback
from chellow.models import Session, Contract, Era
import chellow.computer
from chellow.utils import HH, hh_before, hh_format, req_int
from werkzeug.exceptions import BadRequest
import os
from flask import g
import threading
from chellow.views import chellow_redirect
import csv
import chellow.dloads


def content(contract_id, end_year, end_month, months, user):
    caches = {}
    sess = f = None
    try:
        sess = Session()
        contract = Contract.get_hhdc_by_id(sess, contract_id)

        finish_date = Datetime(end_year, end_month, 1, tzinfo=pytz.utc) + \
            relativedelta(months=1) - HH

        start_date = Datetime(end_year, end_month, 1, tzinfo=pytz.utc) - \
            relativedelta(months=months - 1)

        forecast_date = chellow.computer.forecast_date()
        running_name, finished_name = chellow.dloads.make_names(
            'hhdc_virtual_bills.csv', user)

        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')

        bill_titles = chellow.computer.contract_func(
            caches, contract, 'virtual_bill_titles', None)()
        header_titles = [
            'Import MPAN Core', 'Export MPAN Core', 'Start Date',
            'Finish Date']

        writer.writerow(header_titles + bill_titles)

        for era in sess.query(Era).distinct().filter(
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date,
                Era.hhdc_contract == contract).order_by(Era.supply_id):
            vals = []
            imp_mpan_core = era.imp_mpan_core
            if imp_mpan_core is None:
                imp_mpan_core_str = ''
                is_import = False
            else:
                is_import = True
                imp_mpan_core_str = imp_mpan_core

            exp_mpan_core = era.exp_mpan_core
            exp_mpan_core_str = '' if exp_mpan_core is None else exp_mpan_core

            if era.start_date > start_date:
                chunk_start = era.start_date
            else:
                chunk_start = start_date

            if hh_before(era.finish_date, finish_date):
                chunk_finish = era.finish_date
            else:
                chunk_finish = finish_date

            vals.append(imp_mpan_core_str)
            vals.append(exp_mpan_core_str)
            vals.append(hh_format(chunk_start))
            vals.append(hh_format(chunk_finish))

            supply_source = chellow.computer.SupplySource(
                sess, chunk_start, chunk_finish, forecast_date, era, is_import,
                None, caches)
            supply_source.contract_func(contract, 'virtual_bill')(
                supply_source)
            bill = supply_source.dc_bill
            for title in bill_titles:
                vals.append(str(bill.get(title, '')))
                if title in bill:
                    del bill[title]

            for k in sorted(bill.keys()):
                vals.append(k)
                vals.append(str(bill[k]))
            writer.writerow(vals)
    except BadRequest as e:
        f.write("Problem " + e.description + traceback.format_exc() + '\n')
    except:
        msg = "Problem " + traceback.format_exc() + '\n'
        f.write(msg)
    finally:
        f.close()
        os.rename(running_name, finished_name)
        if sess is not None:
            sess.close()


def do_get(sess):
    end_year = req_int("end_year")
    end_month = req_int("end_month")
    months = req_int("months")
    contract_id = req_int('hhdc_contract_id')

    user = g.user

    threading.Thread(
        target=content, args=(contract_id, end_year, end_month, months, user)
        ).start()
    return chellow_redirect("/downloads", 303)
