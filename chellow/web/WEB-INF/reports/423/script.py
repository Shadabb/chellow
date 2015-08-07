from net.sf.chellow.monad import Monad
from dateutil.relativedelta import relativedelta
from sqlalchemy.sql.expression import true
from datetime import datetime
import utils
import db
import templater
import sys
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')


UserException = utils.UserException
GSupply, GEra, Site, SiteGEra = db.GSupply, db.GEra, db.Site, db.SiteGEra
GBill, GContract, Tpr = db.GBill, db.GContract, db.Tpr
MeasurementRequirement, Report = db.MeasurementRequirement, db.Report
RegisterRead = db.RegisterRead
Contract = db.Contract
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
rate_scripts = None
debug = ''
try:
    sess = db.session()
    g_era_bundles = []
    g_supply_id = inv.getLong('g_supply_id')
    g_supply = GSupply.get_by_id(sess, g_supply_id)
    g_eras = sess.query(GEra).filter(GEra.g_supply == g_supply).order_by(
        GEra.start_date.desc()).all()
    for g_era in g_eras:
        physical_site = sess.query(Site).join(SiteGEra).filter(
            SiteGEra.is_physical == true(), SiteGEra.g_era == g_era).one()
        other_sites = sess.query(Site).join(SiteGEra).filter(
            SiteGEra.is_physical != true(), SiteGEra.g_era == g_era).all()
        g_era_bundle = {
            'g_era': g_era, 'physical_site': physical_site,
            'other_sites': other_sites, 'g_bills': {'g_bill_dicts': []}}
        g_era_bundles.append(g_era_bundle)

        g_era_bundle['shared_accounts'] = \
            sess.query(GSupply).distinct().join(GEra).filter(
                GSupply.id != g_supply.id, GEra.account == g_era.account,
                GEra.g_contract == g_era.g_contract).all()

        g_bills = sess.query(GBill).filter(
            GBill.g_supply == g_supply).order_by(
                GBill.start_date.desc(), GBill.issue_date.desc(),
                GBill.reference.desc())
        if g_era.finish_date is not None:
            g_bills = g_bills.filter(GBill.start_date <= g_era.finish_date)
        if g_era != g_eras[-1]:
            g_bills = g_bills.filter(GBill.start_date >= g_era.start_date)

    RELATIVE_YEAR = relativedelta(years=1)

    now = datetime.utcnow()
    triad_year = (now - RELATIVE_YEAR).year if now.month < 3 else now.year
    this_month_start = datetime(now.year, now.month, 1)
    last_month_start = this_month_start - relativedelta(months=1)
    last_month_finish = this_month_start - relativedelta(minutes=30)

    batch_reports = []
    config_contract = Contract.get_non_core_by_name(sess, 'configuration')
    properties = config_contract.make_properties()
    if 'supply_reports' in properties:
        for report_id in properties['supply_reports']:
            batch_reports.append(Report.get_by_id(sess, report_id))

    truncated_note = None
    is_truncated = False
    note = None
    if len(g_supply.note.strip()) == 0:
        note_str = "{'notes': []}"
    else:
        note_str = g_supply.note

    supply_note = eval(note_str)
    notes = supply_note['notes']
    if len(notes) > 0:
        note = notes[0]
        lines = note['body'].splitlines()
        if len(lines) > 0:
            trunc_line = lines[0][:50]
            if len(lines) > 1 or len(lines[0]) > len(trunc_line):
                is_truncated = True
                truncated_note = trunc_line
    sys.stderr.write("g supply is" + str(g_supply))
    templater.render(
        inv, template, {
            'triad_year': triad_year, 'now': now,
            'last_month_start': last_month_start,
            'last_month_finish': last_month_finish,
            'g_era_bundles': g_era_bundles, 'g_supply': g_supply,
            'system_properties': properties, 'is_truncated': is_truncated,
            'truncated_note': truncated_note, 'note': note,
            'this_month_start': this_month_start,
            'batch_reports': batch_reports, 'debug': debug})

except UserException, e:
    sess.rollback()
    render(inv, template, {'messages': [str(e)]})
finally:
    if sess is not None:
        sess.close()
