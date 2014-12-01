from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract = db.Contract
render = templater.render
UserException = utils.UserException

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('non_core_contract_id')
        contract = Contract.get_non_core_by_id(sess, contract_id)
        render(inv, template, {'contract': contract})
    else:
        db.set_read_write(sess)
        contract_id = inv.getLong('non_core_contract_id')
        contract = Contract.get_non_core_by_id(sess, contract_id)
        if inv.hasParameter('delete'):
            contract.delete(sess)
            sess.commit()
            inv.sendSeeOther('/reports/259/output/')
        else:
            name = inv.getString('name')
            charge_script = inv.getString('charge_script')
            properties = inv.getString('properties')
            contract.update(
                sess, contract.is_core, name, contract.party, charge_script,
                properties)
            sess.commit()
            inv.sendSeeOther(
                '/reports/267/output/?non_core_contract_id=' +
                str(contract.id))
except UserException, e:
    render(inv, template, {'contract': contract, 'messages': [str(e)]}, 400)
finally:
    if sess is not None:
        sess.close()
