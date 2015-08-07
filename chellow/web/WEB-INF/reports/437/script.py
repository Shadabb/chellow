from net.sf.chellow.monad import Monad
import utils
import templater
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
form_str, form_int = utils.form_str, utils.form_int
render = templater.render
GEra = db.GEra
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.hasParameter('search_pattern'):
        pattern = form_str(inv, "search_pattern")
        pattern = pattern.strip()
        reduced_pattern = pattern.replace(" ", "")
        if inv.hasParameter("max_results"):
            max_results = form_int(inv, 'max_results')
        else:
            max_results = 50

        g_eras = sess.query(GEra).from_statement(
            "select e1.* from g_era as e1 "
            "inner join (select e2.g_supply_id, max(e2.start_date) "
            "as max_start_date from g_era as e2 "
            "join g_supply on (e2.g_supply_id = g_supply.id) "
            "where replace(lower(g_supply.mprn), ' ', '') "
            "like lower(:reducedPattern) "
            "or lower(e2.account) like lower(:pattern) "
            "or lower(e2.msn) like lower(:pattern) "
            "group by e2.g_supply_id) as sq "
            "on e1.g_supply_id = sq.g_supply_id "
            "and e1.start_date = sq.max_start_date limit :max_results").params(
            pattern="%" + pattern + "%",
            reducedPattern="%" + reduced_pattern + "%",
            max_results=max_results).all()
        if len(g_eras) == 1:
            inv.sendTemporaryRedirect(
                "/reports/423/output/?g_supply_id=" +
                str(g_eras[0].g_supply.id))
        else:
            render(
                inv, template, {'g_eras': g_eras, 'max_results': max_results})
    else:
        render(inv, template, {})
finally:
    if sess is not None:
        sess.close()
