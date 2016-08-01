import collections
import pytz
from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import traceback
from chellow.models import (
    Batch, Bill, Session, Era, Site, SiteEra, Contract, MarketRole)
import chellow.computer
import chellow.dloads
import sys
import os
import threading
from werkzeug.exceptions import BadRequest
from chellow.utils import HH, hh_format, hh_before, req_int
from chellow.views import chellow_redirect
from flask import request, g
import csv
from itertools import combinations


def content(batch_id, bill_id, user):
    caches = {}
    tmp_file = sess = None
    forecast_date = Datetime.max.replace(tzinfo=pytz.utc)
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'bill_check.csv', user)
        tmp_file = open(running_name, mode='w', newline='')
        writer = csv.writer(tmp_file, lineterminator='\n')
        if batch_id is not None:
            batch = Batch.get_by_id(sess, batch_id)
            bills = sess.query(Bill).filter(
                Bill.batch_id == batch.id).order_by(Bill.reference)
        elif bill_id is not None:
            bill = Bill.get_by_id(sess, bill_id)
            bills = sess.query(Bill).filter(Bill.id == bill.id)
            batch = bill.batch

        contract = batch.contract
        market_role_code = contract.market_role.code

        vbf = chellow.computer.contract_func(
            caches, contract, 'virtual_bill', None)
        if vbf is None:
            raise BadRequest(
                'The contract ' + contract.name +
                " doesn't have a function virtual_bill.")

        virtual_bill_titles_func = chellow.computer.contract_func(
            caches, contract, 'virtual_bill_titles', None)
        if virtual_bill_titles_func is None:
            raise BadRequest(
                'The contract ' + contract.name +
                " doesn't have a function virtual_bill_titles.")
        virtual_bill_titles = virtual_bill_titles_func()

        titles = [
            'batch', 'bill-reference', 'bill-type', 'bill-kwh', 'bill-net-gbp',
            'bill-vat-gbp', 'bill-start-date', 'bill-finish-date',
            'bill-mpan-core', 'site-code', 'site-name', 'covered-from',
            'covered-to', 'covered-bills', 'metered-kwh']
        for t in virtual_bill_titles:
            titles.append('covered-' + t)
            titles.append('virtual-' + t)
            if t.endswith('-gbp'):
                titles.append('difference-' + t)

        writer.writerow(titles)

        for bill in bills:
            problem = ''
            supply = bill.supply

            read_dict = {}
            for read in bill.reads:
                gen_start = read.present_date.replace(hour=0).replace(minute=0)
                gen_finish = gen_start + relativedelta(days=1) - HH
                msn_match = False
                read_msn = read.msn
                for read_era in supply.find_eras(sess, gen_start, gen_finish):
                    if read_msn == read_era.msn:
                        msn_match = True
                        break

                if not msn_match:
                    problem += "The MSN " + read_msn + \
                        " of the register read " + str(read.id) + \
                        " doesn't match the MSN of the era."

                for dt, type in [
                        (read.present_date, read.present_type),
                        (read.previous_date, read.previous_type)]:
                    key = str(dt) + "-" + read.msn
                    try:
                        if type != read_dict[key]:
                            problem += " Reads taken on " + str(dt) + \
                                " have differing read types."
                    except KeyError:
                        read_dict[key] = type

            bill_start = bill.start_date
            bill_finish = bill.finish_date

            era = supply.find_era_at(sess, bill.finish_date)
            if era is None:
                raise BadRequest(
                    "Extraordinary! There isn't an era for the bill " +
                    str(bill.id) + ".")

            values = [
                batch.reference, bill.reference, bill.bill_type.code,
                bill.kwh, bill.net, bill.vat, hh_format(bill_start),
                hh_format(bill_finish), era.imp_mpan_core]

            covered_start = bill_start
            covered_finish = bill_finish
            covered_bill_ids = []
            covered_bdown = {'sum-msp-kwh': 0, 'net-gbp': 0, 'vat-gbp': 0}
            covered_primary_bill = None
            enlarged = True

            while enlarged:
                enlarged = False
                covered_bills = []
                cand_bills = dict(
                    (b.id, b) for b in sess.query(Bill).join(Batch).
                    join(Contract).join(MarketRole).filter(
                        Bill.supply == supply,
                        Bill.start_date <= covered_finish,
                        Bill.finish_date >= covered_start,
                        MarketRole.code == market_role_code).order_by(
                        Bill.issue_date.desc(), Bill.start_date))
                while True:
                    to_del = None
                    for a, b in combinations(cand_bills.values(), 2):
                        if all(
                                (
                                    a.start_date == b.start_date,
                                    a.finish_date == b.finish_date,
                                    a.kwh == -1 * b.kwh, a.net == -1 * b.net,
                                    a.vat == -1 * b.vat,
                                    a.gross == -1 * b.gross)):
                            to_del = (a.id, b.id)
                            break
                    if to_del is None:
                        break
                    else:
                        for k in to_del:
                            del cand_bills[k]
                for cand_bill_id in sorted(cand_bills.keys()):
                    cand_bill = cand_bills[cand_bill_id]
                    if covered_primary_bill is None and \
                            len(cand_bill.reads) > 0:
                        covered_primary_bill = cand_bill
                    if cand_bill.start_date < covered_start:
                        covered_start = cand_bill.start_date
                        enlarged = True
                        break
                    if cand_bill.finish_date > covered_finish:
                        covered_finish = cand_bill.finish_date
                        enlarged = True
                        break
                    covered_bills.append(cand_bill)

            for covered_bill in covered_bills:
                covered_bill_ids.append(covered_bill.id)
                covered_bdown['net-gbp'] += float(covered_bill.net)
                covered_bdown['vat-gbp'] += float(covered_bill.vat)
                covered_bdown['sum-msp-kwh'] += float(covered_bill.kwh)
                if len(covered_bill.breakdown) > 0:
                    covered_rates = collections.defaultdict(set)
                    for k, v in eval(covered_bill.breakdown, {}).items():

                        if k.endswith('rate'):
                            covered_rates[k].add(v)
                        elif k != 'raw-lines':
                            try:
                                covered_bdown[k] += v
                            except KeyError:
                                covered_bdown[k] = v
                            except TypeError as detail:
                                raise BadRequest(
                                    "For key " + str(k) + " the value " +
                                    str(v) +
                                    " can't be added to the existing value " +
                                    str(covered_bdown[k]) + ". " + str(detail))
                    for k, v in covered_rates.items():
                        covered_bdown[k] = v.pop() if len(v) == 1 else None

            virtual_bill = {}
            metered_kwh = 0
            for era in sess.query(Era).filter(
                    Era.supply_id == supply.id, Era.imp_mpan_core != null(),
                    Era.start_date <= covered_finish,
                    or_(
                        Era.finish_date == null(),
                        Era.finish_date >= covered_start)).distinct():
                site = sess.query(Site).join(SiteEra).filter(
                    SiteEra.is_physical == true(),
                    SiteEra.era_id == era.id).one()

                if covered_start > era.start_date:
                    chunk_start = covered_start
                else:
                    chunk_start = era.start_date

                if hh_before(covered_finish, era.finish_date):
                    chunk_finish = covered_finish
                else:
                    chunk_finish = era.finish_date

                data_source = chellow.computer.SupplySource(
                    sess, chunk_start, chunk_finish, forecast_date, era, True,
                    None, caches, covered_primary_bill)

                if data_source.measurement_type == 'hh':
                    metered_kwh += sum(
                        h['msp-kwh'] for h in data_source.hh_data)
                else:
                    ds = chellow.computer.SupplySource(
                        sess, chunk_start, chunk_finish, forecast_date, era,
                        True, None, caches)
                    metered_kwh += sum(h['msp-kwh'] for h in ds.hh_data)

                vbf(data_source)

                if market_role_code == 'X':
                    vb = data_source.supplier_bill
                elif market_role_code == 'C':
                    vb = data_source.dc_bill
                elif market_role_code == 'M':
                    vb = data_source.mop_bill
                else:
                    raise BadRequest("Odd market role.")

                for k, v in vb.items():
                    if k.endswith('-rate'):
                        if k not in virtual_bill:
                            virtual_bill[k] = set()
                        virtual_bill[k].add(v)
                    else:
                        try:
                            virtual_bill[k] += v
                        except KeyError:
                            virtual_bill[k] = v
                        except TypeError as detail:
                            raise BadRequest(
                                "For key " + str(k) + " and value " + str(v) +
                                ". " + str(detail))

            values += [
                site.code, site.name, hh_format(covered_start),
                hh_format(covered_finish),
                ','.join(str(id).replace(',', '') for id in covered_bill_ids),
                metered_kwh]
            for title in virtual_bill_titles:
                try:
                    cov_val = covered_bdown[title]
                    values.append(cov_val)
                    del covered_bdown[title]
                except KeyError:
                    cov_val = None
                    values.append('')

                try:
                    virt_val = virtual_bill[title]
                    if isinstance(virt_val, set):
                        virt_val = ', '.join(str(v) for v in virt_val)
                    elif isinstance(virt_val, Datetime):
                        virt_val = hh_format(virt_val)
                    values.append(virt_val)
                    del virtual_bill[title]
                except KeyError:
                    virt_val = None
                    values.append('')

                if title.endswith('-gbp'):
                    if all(isinstance(val, (int, float)) for val in [
                            cov_val, virt_val]):
                        values.append(cov_val - virt_val)
                    else:
                        values.append('')

            for title in sorted(virtual_bill.keys()):
                virt_val = virtual_bill[title]
                if isinstance(virt_val, set):
                    virt_val = ', '.join(str(v) for v in virt_val)
                elif isinstance(virt_val, Datetime):
                    virt_val = hh_format(virt_val)
                values += ['virtual-' + title, virt_val]
                if title in covered_bdown:
                    values += ['covered-' + title, covered_bdown[title]]
                else:
                    values += ['', '']

            writer.writerow(values)
    except BadRequest as e:
        tmp_file.write("Problem: " + e.description)
    except:
        msg = traceback.format_exc()
        sys.stderr.write(msg + '\n')
        tmp_file.write("Problem " + msg)
    finally:
        if sess is not None:
            sess.close()
        tmp_file.close()
        os.rename(running_name, finished_name)


def do_get(sess):
    if 'batch_id' in request.values:
        batch_id = req_int("batch_id")
        bill_id = None
    elif 'bill_id' in request.values:
        bill_id = req_int("bill_id")
        batch_id = None
    else:
        raise BadRequest("The bill check needs a batch_id or bill_id.")

    user = g.user
    threading.Thread(target=content, args=(batch_id, bill_id, user)).start()
    return chellow_redirect('/downloads', 303)
