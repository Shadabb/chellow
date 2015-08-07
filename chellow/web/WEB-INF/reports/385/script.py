from net.sf.chellow.monad import Monad
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GEra, GSupply = db.GEra, db.GSupply
UserException, form_date = utils.UserException, utils.form_date
render = templater.render
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, g_supply, message=None):
    messages = [] if message is None else [str(message)]
    g_eras = sess.query(GEra).filter(
        GEra.g_supply == g_supply).order_by(GEra.start_date.desc())
    return {'g_supply': g_supply, 'messages': messages, 'g_eras': g_eras}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        g_supply_id = inv.getLong('g_supply_id')
        g_supply = GSupply.get_by_id(sess, g_supply_id)
        render(inv, template, make_fields(sess, g_supply))
    else:
        db.set_read_write(sess)
        g_supply_id = inv.getLong('g_supply_id')
        g_supply = GSupply.get_by_id(sess, g_supply_id)

        if inv.hasParameter("delete"):
            g_supply.delete(sess)
            sess.commit()
            inv.sendSeeOther("/reports/437/output/")
        elif inv.hasParameter("insert_g_era"):
            start_date = form_date(inv, 'start')
            g_supply.insert_g_era_at(sess, start_date)
            sess.commit()
            inv.sendSeeOther(
                "/reports/423/output/?g_supply_id=" + str(g_supply.id))
        else:
            mprn = inv.getString("mprn")
            name = inv.getString("name")
            g_supply.update(mprn, name)
            sess.commit()
            inv.sendSeeOther(
                "/reports/423/output/?g_supply_id=" + str(g_supply.id))
except UserException, e:
    render(inv, template, make_fields(sess, g_supply, e), 400)
finally:
    if sess is not None:
        sess.close()
