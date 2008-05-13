from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import Account

def create_item_element(doc, mpan, finish_generation):
    item_element = doc.createElement('item')
    account_element.appendChild(item_element)
    item_element.appendChild(mpan.getMpanCore().toXML(doc))
    start_generation = mpan.getSupplyGeneration()
    start_generation.setLabel('start')
    item_element.appendChild(start_generation.toXML(doc))
    finish_generation.setLabel('finish')
    item_element.appendChild(finish_generation.toXML(doc))
    return item_element

account_id = inv.getLong('account-id')
account = Account.getAccount(account_id)
if not account.getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such an account doesn't exist in this organization")
account_element = account.getXML(XmlTree('provider'), doc)
source.appendChild(account_element)

mpans = Hiber.session().createQuery("from Mpan mpan where mpan.supplierAccount = :account order by mpan.mpanCore, mpan.supplyGeneration.startDate.date").setEntity('account', account).list()
current_mpan = mpans[0]
finish_generation = current_mpan.getSupplyGeneration()
for i in range(1, len(mpans)):
    mpan = mpans[i]
    if current_mpan.getMpanCore().equals(mpan.getMpanCore()) and finish_generation.getFinishDate().getNext().getDate().equals(mpan.getSupplyGeneration().getStartDate().getDate()):
        finish_generation = mpan.getSupplyGeneration()
    else:
        account_element.appendChild(create_item_element(doc, current_mpan, finish_generation))
        current_mpan = mpan
        finish_generation = current_mpan.getSupplyGeneration()
account_element.appendChild(create_item_element(doc, current_mpan, finish_generation))
source.appendChild(organization.toXML(doc))