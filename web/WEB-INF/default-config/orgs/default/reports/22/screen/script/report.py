from net.sf.chellow.monad import Hiber

for dso in Hiber.session().createQuery(
                'from Dso dso order by dso.code.string').list():
    source.appendChild(dso.toXML(doc));
source.appendChild(organization.toXML(doc))
