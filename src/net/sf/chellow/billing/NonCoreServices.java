/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.billing;

import java.util.Date;
import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

@SuppressWarnings("serial")
public class NonCoreServices implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("non-core-services");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public NonCoreServices() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return new MonadUri("/").resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		String participantCode = inv.getString("participant-code");
		String name = inv.getString("name");
		Date startDate = inv.getDate("start-date");
		String chargeScript = inv.getString("charge-script");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		Provider provider = Provider.getProvider(participantCode,
				MarketRole.NON_CORE_ROLE);
		NonCoreService service = NonCoreService.insertNonCoreService(provider,
				name, HhEndDate.roundDown(startDate), chargeScript);
		Hiber.commit();
		inv.sendCreated(document(), service.getUri());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element servicesElement = (Element) toXml(doc);
		source.appendChild(servicesElement);
		for (NonCoreService service : (List<NonCoreService>) Hiber
				.session()
				.createQuery(
						"from NonCoreService service where order by service.finishRateScript.finishDate.date desc, service.provider.code")
				.list()) {
			servicesElement.appendChild(service.toXml(doc, new XmlTree(
					"provider")));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	public NonCoreService getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		NonCoreService service = (NonCoreService) Hiber.session().createQuery(
				"from NonCoreService service where service.id = :serviceId")
				.setLong("serviceId", Long.parseLong(uriId.getString()))
				.uniqueResult();
		if (service == null) {
			throw new NotFoundException();
		}
		return service;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element contractsElement = doc.createElement("government-services");
		return contractsElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}