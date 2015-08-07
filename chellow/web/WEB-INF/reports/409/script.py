from net.sf.chellow.monad import Monad
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GRateScript = db.GRateScript
form_date, NotFoundException = utils.form_date, utils.NotFoundException
UserException, form_json = utils.UserException, utils.form_json
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        rate_script_id = inv.getLong('g_rate_script_id')
        rate_script = GRateScript.get_by_id(sess, rate_script_id)
        render(inv, template, {'rate_script': rate_script})
    else:
        db.set_read_write(sess)
        rate_script_id = inv.getLong('g_rate_script_id')
        rate_script = GRateScript.get_by_id(sess, rate_script_id)
        contract = rate_script.g_contract
        if inv.hasParameter('delete'):
            contract.delete_g_rate_script(sess, rate_script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/399/output/?g_contract_id=' + str(contract.id))
        else:
            script = form_json(inv, 'script')
            start_date = form_date(inv, 'start')
            has_finished = inv.getBoolean('has_finished')
            finish_date = form_date(inv, 'finish') if has_finished else None
            contract.update_g_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/411/output/?g_rate_script_id=' + str(rate_script.id))
except NotFoundException, e:
    inv.sendNotFound(str(e))
except UserException, e:
    sess.rollback()
    render(
        inv, template, {'rate_script': rate_script, 'messages': [str(e)]}, 400)
finally:
    if sess is not None:
        sess.close()
