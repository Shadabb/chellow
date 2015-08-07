from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GContract = db.GContract
SiteGEra, GEra, Site, GContract = db.SiteGEra, db.GEra, db.Site, db.GContract
render = templater.render
UserException, parse_mpan_core = utils.UserException, utils.parse_mpan_core
form_date, validate_hh_start = utils.form_date, utils.validate_hh_start
form_int, form_bool, form_str = utils.form_int, utils.form_bool, utils.form_str
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, g_era, message=None):
    messages = [] if message is None else [str(message)]
    supplier_g_contracts = sess.query(GContract).order_by(GContract.name)
    site_g_eras = sess.query(SiteGEra).join(Site).filter(
        SiteGEra.g_era == g_era).order_by(Site.code).all()
    return {
        'g_era': g_era, 'messages': messages,
        'supplier_g_contracts': supplier_g_contracts,
        'site_g_eras': site_g_eras}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        g_era_id = form_int(inv, 'g_era_id')
        g_era = GEra.get_by_id(sess, g_era_id)
        render(inv, template, make_fields(sess, g_era))
    else:
        db.set_read_write(sess)
        g_era_id = form_int(inv, 'g_era_id')
        g_era = GEra.get_by_id(sess, g_era_id)

        if inv.hasParameter("delete"):
            g_supply = g_era.supply
            g_supply.delete_g_era(sess, g_era)
            sess.commit()
            inv.sendSeeOther(
                "/reports/423/output/?g_supply_id=" + str(g_supply.id))
        elif inv.hasParameter("attach"):
            site_code = form_str(inv, "site_code")
            site = Site.get_by_code(sess, site_code)
            g_era.attach_site(sess, site)
            sess.commit()
            inv.sendSeeOther(
                "/reports/423/output/?g_supply_id=" + str(g_era.g_supply.id))
        elif inv.hasParameter("detach"):
            site_id = form_int(inv, "site_id")
            site = Site.get_by_id(sess, site_id)
            g_era.detach_site(sess, site)
            sess.commit()
            inv.sendSeeOther(
                "/reports/423/output/?g_supply_id=" + str(g_era.g_supply.id))
        elif inv.hasParameter("locate"):
            site_id = form_int(inv, "site_id")
            site = Site.get_by_id(sess, site_id)
            g_era.set_physical_location(sess, site)
            sess.commit()
            inv.sendSeeOther(
                "/reports/423/output/?g_supply_id=" + str(g_era.g_supply.id))
        else:
            start_date = form_date(inv, 'start')
            is_ended = form_bool(inv, "is_ended")
            if is_ended:
                finish_date = form_date(inv, "finish")
                validate_hh_start(finish_date)
            else:
                finish_date = None
            msn = form_str(inv, "msn")

            g_contract_id = form_int(inv, "g_contract_id")
            g_contract = GContract.get_by_id(sess, g_contract_id)
            account = form_str(inv, "account")
            g_era.g_supply.update_g_era(
                sess, g_era, start_date, finish_date, msn, g_contract, account)
            sess.commit()
            inv.sendSeeOther(
                "/reports/423/output/?g_supply_id=" + str(g_era.g_supply.id))
except UserException, e:
    render(inv, template, make_fields(sess, g_era, e), 400)
finally:
    if sess is not None:
        sess.close()
