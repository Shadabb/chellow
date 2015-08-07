from net.sf.chellow.monad import Monad
import operator
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, Site, Era, SiteEra = db.Contract, db.Site, db.Era, db.SiteEra
MarketRole, GEra, SiteGEra = db.MarketRole, db.GEra, db.SiteGEra
HH = utils.HH
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    configuration_contract = Contract.get_non_core_by_name(
        sess, 'configuration')
    site_id = inv.getLong("site_id")
    site = Site.get_by_id(sess, site_id)

    eras = sess.query(Era).join(SiteEra).filter(
        SiteEra.site_id == site.id).order_by(
        Era.supply_id, Era.start_date.desc()).all()

    groups = []
    for idx, era in enumerate(eras):
        if idx == 0 or eras[idx - 1].supply_id != era.supply_id:
            if era.pc.code == '00':
                meter_cat = 'HH'
            elif len(era.channels) > 0:
                meter_cat = 'AMR'
            elif era.mtc.meter_type.code in ['UM', 'PH']:
                meter_cat = 'Unmetered'
            else:
                meter_cat = 'NHH'

            groups.append(
                {
                    'last_era': era, 'is_ongoing': era.finish_date is None,
                    'meter_category': meter_cat})

        if era == eras[-1] or era.supply_id != eras[idx + 1]:
            groups[-1]['first_era'] = era

    groups = sorted(
        groups, key=operator.itemgetter('is_ongoing'), reverse=True)

    g_eras = sess.query(GEra).join(SiteGEra).filter(
        SiteGEra.site == site).order_by(
        GEra.g_supply_id, GEra.start_date.desc()).all()

    g_groups = []
    for idx, g_era in enumerate(g_eras):
        if idx == 0 or g_eras[idx - 1].g_supply_id != g_era.g_supply_id:
            g_groups.append(
                {
                    'last_g_era': g_era,
                    'is_ongoing': g_era.finish_date is None})

        if g_era == g_eras[-1] or g_era.g_supply_id != g_eras[idx + 1]:
            g_groups[-1]['first_g_era'] = g_era

    g_groups = sorted(
        g_groups, key=operator.itemgetter('is_ongoing'), reverse=True)

    now = datetime.now(pytz.utc)
    month_start = datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH
    last_month_start = month_start - relativedelta(months=1)
    last_month_finish = month_start - HH

    properties = configuration_contract.make_properties()
    other_sites = [
        s for s in site.groups(sess, now, now, False)[0].sites if s != site]
    scenarios = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'X', Contract.name.like('scenario_%')).order_by(
        Contract.name).all()
    templater.render(
        inv, template, {
            'site': site, 'groups': groups, 'g_groups': g_groups,
            'properties': properties, 'other_sites': other_sites,
            'month_start': month_start, 'month_finish': month_finish,
            'last_month_start': last_month_start,
            'last_month_finish': last_month_finish, 'scenarios': scenarios})
finally:
    if sess is not None:
        sess.close()
