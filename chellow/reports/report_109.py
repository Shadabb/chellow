from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
import pytz
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import traceback
from chellow.models import (
    Contract, Site, SiteEra, Era, Supply, Source, Session)
from chellow.utils import HH, hh_format, req_int
import chellow.computer
import chellow.dloads
import csv
import sys
import os
from flask import g
import threading
from chellow.views import chellow_redirect


def content(contract_id, end_year, end_month, months, user):
    caches = {}
    sess = f = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'displaced.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        titles = [
            'Site Code', 'Site Name', 'Associated Site Ids', 'From', 'To',
            'Gen Types', 'CHP kWh', 'LM kWh', 'Turbine kWh', 'PV kWh']

        finish_date = Datetime(end_year, end_month, 1, tzinfo=pytz.utc) + \
            relativedelta(months=1) - HH

        start_date = Datetime(end_year, end_month, 1, tzinfo=pytz.utc) - \
            relativedelta(months=months-1)

        forecast_date = chellow.computer.forecast_date()

        contract = Contract.get_supplier_by_id(sess, contract_id)
        sites = sess.query(Site).join(SiteEra).join(Era).join(Supply). \
            join(Source).filter(
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date,
                or_(
                    Source.code.in_(('gen', 'gen-net')),
                    Era.exp_mpan_core != null())).distinct()
        bill_titles = chellow.computer.contract_func(
            caches, contract, 'displaced_virtual_bill_titles', None)()

        for title in bill_titles:
            if title == 'total-msp-kwh':
                title = 'total-displaced-msp-kwh'
            titles.append(title)
        writer.writerow(titles)

        for site in sites:
            month_start = start_date
            month_finish = month_start + relativedelta(months=1) - HH
            while not month_finish > finish_date:
                for site_group in site.groups(
                        sess, month_start, month_finish, True):
                    if site_group.start_date > month_start:
                        chunk_start = site_group.start_date
                    else:
                        chunk_start = month_start
                    if site_group.finish_date > month_finish:
                        chunk_finish = month_finish
                    else:
                        chunk_finish = site_group.finish_date

                    displaced_era = chellow.computer.displaced_era(
                        sess, site_group, chunk_start, chunk_finish)
                    if displaced_era is None:
                        continue
                    supplier_contract = displaced_era.imp_supplier_contract
                    if contract is not None and contract != supplier_contract:
                        continue

                    linked_sites = ','.join(
                        a_site.code for a_site in site_group.sites
                        if not a_site == site)
                    generator_types = ' '.join(
                        sorted(
                            [
                                supply.generator_type.code for supply in
                                site_group.supplies
                                if supply.generator_type is not None]))
                    vals = [
                        site.code, site.name, linked_sites,
                        hh_format(chunk_start), hh_format(chunk_finish),
                        generator_types]

                    total_gen_breakdown = {}

                    results = iter(
                        sess.execute(
                            "select supply.id, hh_datum.value, "
                            "hh_datum.start_date, channel.imp_related, "
                            "source.code, generator_type.code as "
                            "gen_type_code from hh_datum, channel, source, "
                            "era, supply left outer join generator_type on "
                            "supply.generator_type_id = generator_type.id "
                            "where hh_datum.channel_id = channel.id and "
                            "channel.era_id = era.id and era.supply_id = "
                            "supply.id and supply.source_id = source.id and "
                            "channel.channel_type = 'ACTIVE' and not "
                            "(source.code = 'net' and channel.imp_related "
                            "is true) and hh_datum.start_date >= "
                            ":chunk_start and hh_datum.start_date "
                            "<= :chunk_finish and "
                            "supply.id = any(:supply_ids) order "
                            "by hh_datum.start_date, supply.id",
                            params={
                                'chunk_start': chunk_start,
                                'chunk_finish': chunk_finish,
                                'supply_ids': [
                                    s.id for s in site_group.supplies]}))

                    (
                        sup_id, hh_val, hh_start, imp_related, source_code,
                        gen_type_code) = next(
                        results, (None, None, None, None, None, None))

                    hh_date = chunk_start

                    while hh_date <= finish_date:
                        gen_breakdown = {}
                        exported = 0
                        while hh_start == hh_date:
                            if not imp_related and source_code in (
                                    'net', 'gen-net'):
                                exported += hh_val
                            if (imp_related and source_code == 'gen') or \
                                    (not imp_related and
                                        source_code == 'gen-net'):
                                gen_breakdown[gen_type_code] = \
                                    gen_breakdown.setdefault(
                                        gen_type_code, 0) + hh_val

                            if (
                                    not imp_related and
                                    source_code == 'gen') or (
                                    imp_related and
                                    source_code == 'gen-net'):
                                gen_breakdown[gen_type_code] = \
                                    gen_breakdown.setdefault(
                                        gen_type_code, 0) - hh_val

                            (
                                sup_id, hh_val, hh_start, imp_related,
                                source_code, gen_type_code) = next(
                                results, (None, None, None, None, None, None))

                        displaced = sum(gen_breakdown.values()) - exported
                        added_so_far = 0
                        for key in sorted(gen_breakdown.keys()):
                            kwh = gen_breakdown[key]
                            if kwh + added_so_far > displaced:
                                total_gen_breakdown[key] = \
                                    total_gen_breakdown.get(key, 0) + \
                                    displaced - added_so_far
                                break
                            else:
                                total_gen_breakdown[key] = \
                                    total_gen_breakdown.get(key, 0) + kwh
                                added_so_far += kwh

                        hh_date += HH

                    for title in ['chp', 'lm', 'turb', 'pv']:
                        vals.append(str(total_gen_breakdown.get(title, '')))

                    site_ds = chellow.computer.SiteSource(
                        sess, site, chunk_start, chunk_finish, forecast_date,
                        None, caches, displaced_era)
                    disp_func = chellow.computer.contract_func(
                        caches, supplier_contract, 'displaced_virtual_bill',
                        None)
                    disp_func(site_ds)
                    bill = site_ds.supplier_bill
                    for title in bill_titles:
                        if title in bill:
                            val = bill[title]
                            if isinstance(val, Datetime):
                                val = hh_format(val)
                            else:
                                val = str(val)
                            vals.append(val)
                            del bill[title]
                        else:
                            vals.append('')

                    for k in sorted(bill.keys()):
                        vals.append(k)
                        vals.append(str(bill[k]))
                    writer.writerow(vals)

                month_start += relativedelta(months=1)
                month_finish = month_start + relativedelta(months=1) - HH
    except:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    end_year = req_int('finish_year')
    end_month = req_int('finish_month')
    months = req_int('months')
    contract_id = req_int('supplier_contract_id')
    args = (contract_id, end_year, end_month, months, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
