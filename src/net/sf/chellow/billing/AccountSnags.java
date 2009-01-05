package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;
import net.sf.chellow.physical.Snag;

import org.hibernate.ScrollMode;
import org.hibernate.ScrollableResults;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class AccountSnags extends EntityList {
	static private final int PAGE_SIZE = 20;

	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("account-snags");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Contract contract;

	public AccountSnags(Contract contract) {
		this.contract = contract;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return contract.getUri().resolve(getUriId()).append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element snagsElement = toXml(doc);
		source.appendChild(snagsElement);
		if (contract instanceof SupplierContract) {
			snagsElement.appendChild(contract.toXml(doc, new XmlTree("party")));
		}
		for (AccountSnag snag : (List<AccountSnag>) Hiber
				.session()
				.createQuery(
						"from AccountSnag snag where snag.dateResolved is null and snag.contract = :contract order by snag.account.reference, snag.description, snag.startDate.date")
				.setEntity("contract", contract).setMaxResults(PAGE_SIZE)
				.list()) {
			snagsElement.appendChild(snag.toXml(doc, new XmlTree("account")));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	@SuppressWarnings("unchecked")
	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("ignore")) {
			MonadDate ignoreDate = inv.getMonadDate("ignore-date");

			ScrollableResults snags = Hiber
					.session()
					.createQuery(
							"from AccountSnag snag where snag.contract = :contract and snag.finishDate < :ignoreDate")
					.setEntity("contract", contract).setTimestamp("ignoreDate",
							ignoreDate.getDate()).scroll(
							ScrollMode.FORWARD_ONLY);
			while (snags.next()) {
				AccountSnag snag = (AccountSnag) snags.get(0);
				snag.setIsIgnored(true);
				Hiber.session().flush();
				Hiber.session().clear();
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		return Snag.getSnag(urlId.getString());
	}

	public MonadUri getMonadUri() throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("account-snags");
	}
}