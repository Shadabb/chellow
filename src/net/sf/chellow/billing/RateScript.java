/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/

package net.sf.chellow.billing;

import java.util.Calendar;
import java.util.Date;

import javax.script.Invocable;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.script.ScriptException;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.ui.GeneralImport;

import org.python.core.PyException;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RateScript extends PersistentEntity {
	public static void generalImportHhdc(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String contractName = GeneralImport.addField(csvElement,
					"Contract Name", values, 0);
			HhdcContract contract = HhdcContract.getHhdcContract(contractName);
			String idStr = GeneralImport.addField(csvElement, "Id", values, 1);
			Long id = null;
			if (idStr.length() > 0) {
				id = new Long(idStr);
			}
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 2);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String script = GeneralImport.addField(csvElement, "Script",
					values, 3);
			contract.insertRateScript(id, startDate, script);
		} else if (action.equals("update")) {
		}
	}

	public static void generalImportDso(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String dsoCode = GeneralImport.addField(csvElement, "Dso Code",
					values, 0);
			Dso dso = Dso.getDso(dsoCode);
			String contractName = GeneralImport.addField(csvElement,
					"Contract Name", values, 1);
			DsoContract contract = dso.getContract(contractName);
			String idStr = GeneralImport.addField(csvElement, "Id", values, 2);
			Long id = null;
			if (idStr.length() > 0) {
				id = new Long(idStr);
			}
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 3);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String script = GeneralImport.addField(csvElement, "Script",
					values, 4);
			contract.insertRateScript(id, startDate, script);
		} else if (action.equals("update")) {
		}
	}

	public static void generalImportSupplier(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String contractName = GeneralImport.addField(csvElement,
					"Contract Name", values, 0);
			SupplierContract contract = SupplierContract
					.getSupplierContract(contractName);
			String idStr = GeneralImport.addField(csvElement, "Id", values, 1);
			Long id = null;
			if (idStr.length() > 0) {
				id = new Long(idStr);
			}
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 2);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String script = GeneralImport.addField(csvElement, "Script",
					values, 3);
			contract.insertRateScript(id, startDate, script);
		} else if (action.equals("update")) {
		}
	}

	public static void generalImportNonCore(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String contractName = GeneralImport.addField(csvElement,
					"Contract Name", values, 0);
			NonCoreContract contract = NonCoreContract
					.getNonCoreContract(contractName);
			String idStr = GeneralImport.addField(csvElement, "Id", values, 1);
			Long id = null;
			if (idStr.length() > 0) {
				id = new Long(idStr);
			}
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 2);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String script = GeneralImport.addField(csvElement, "Script",
					values, 3);
			contract.insertRateScript(id, startDate, script);
		} else if (action.equals("update")) {
		}
	}

	static public RateScript getRateScript(Long id) {
		return (RateScript) Hiber.session().get(RateScript.class, id);
	}

	private Contract contract;

	private HhStartDate startDate;

	private HhStartDate finishDate;

	private String script;

	public RateScript() {
	}

	public RateScript(Contract contract, Long id, HhStartDate startDate,
			HhStartDate finishDate, String script) throws HttpException {
		Configuration configuration = Configuration.getConfiguration();

		if (id == null) {
			if (contract.isCore()) {
				id = configuration.nextCoreRateScriptId();
			} else {
				id = configuration.nextUserRateScriptId();
			}
		} else {
			if (contract.isCore()) {
				if (id > configuration.getCoreRateScriptId()) {
					configuration.setCoreRateScriptId(id);
				}
			} else {
				if (id > configuration.getUserRateScriptId()) {
					configuration.setUserRateScriptId(id);
				}
			}
		}
		setId(id);
		setContract(contract);
		internalUpdate(startDate, finishDate, script);
	}

	public Contract getContract() {
		return contract;
	}

	void setContract(Contract contract) {
		this.contract = contract;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhStartDate finishDate) {
		this.finishDate = finishDate;
	}

	public String getScript() {
		return script;
	}

	void setScript(String script) {
		this.script = script;
	}

	void internalUpdate(HhStartDate startDate, HhStartDate finishDate,
			String script) throws HttpException {
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (finishDate != null
				&& startDate.getDate().after(finishDate.getDate())) {
			throw new UserException(
					"The start date can't be after the finish date");
		}
		PythonInterpreter interp = new PythonInterpreter();
		try {
			interp.compile(script);
		} catch (Throwable e) {
			throw new UserException(HttpException.getStackTraceString(e));
		}
		setScript(script);
	}

	public void update(HhStartDate startDate, HhStartDate finishDate,
			String script) throws HttpException {
		HhStartDate originalStartDate = getStartDate();
		HhStartDate originalFinishDate = getFinishDate();
		RateScript previousRateScript = contract.getPreviousRateScript(this);
		RateScript nextRateScript = contract.getNextRateScript(this);

		internalUpdate(startDate, finishDate, script);
		if (previousRateScript != null) {
			if (!previousRateScript.getStartDate().getDate().before(
					startDate.getDate())) {
				throw new UserException(
						"The start date must be after the start date of the previous rate script.");
			}
			previousRateScript.internalUpdate(
					previousRateScript.getStartDate(), startDate.getPrevious(),
					previousRateScript.getScript());
		}
		if (nextRateScript != null) {
			if (finishDate == null) {
				throw new UserException(
						"The finish date must be before the finish date of the next rate script.");
			}
			if (nextRateScript.getFinishDate() != null
					&& !finishDate.getDate().before(
							nextRateScript.getFinishDate().getDate())) {
				throw new UserException(
						"The finish date must be before the finish date of the next rate script.");
			}
			nextRateScript.internalUpdate(finishDate.getNext(), nextRateScript
					.getFinishDate(), nextRateScript.getScript());
		}
		Hiber.flush();
		HhStartDate checkFinishDate = null;
		if (originalFinishDate == null) {
			checkFinishDate = getFinishDate();
		} else if (finishDate != null) {
			checkFinishDate = finishDate.getDate().after(
					originalFinishDate.getDate()) ? finishDate
					: originalFinishDate;
		}
		HhStartDate checkStartDate = null;
		if (originalStartDate == null) {
			checkStartDate = getStartDate();
		} else {
			checkStartDate = startDate.getDate().before(
					originalStartDate.getDate()) ? startDate
					: originalStartDate;
		}
		contract.onUpdate(checkStartDate, checkFinishDate);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "rate-script");

		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			finishDate.setLabel("finish");
			element.appendChild(finishDate.toXml(doc));
		}
		element.setAttribute("script", script);
		return element;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}

	public MonadUri getUri() throws HttpException {
		return getContract().rateScriptsInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("test")) {
			String script = inv.getString("script");
			Date startDate = inv.getDate("start-date");
			Date finishDate = null;
			boolean hasFinished = inv.getBoolean("has-finished");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			script = script.replace("\r", "").replace("\t", "    ");
			if (hasFinished) {
				finishDate = inv.getDate("finish-date");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
			}
			Long billId = inv.getLong("bill-id");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			Bill bill = Bill.getBill(billId);
			Document doc = document();
			Element source = doc.getDocumentElement();
			update(HhStartDate.roundDown(startDate).getNext(),
					finishDate == null ? null : HhStartDate
							.roundDown(finishDate), script);
			source.appendChild(bill.virtualBillXml(doc));
			inv.sendOk(doc);
		} else if (inv.hasParameter("delete")) {
			try {
				contract.delete(this);
				Hiber.commit();
			} catch (UserException e) {
				Hiber.rollBack();
				e.setDocument(document());
				throw e;
			}
			inv.sendSeeOther(contract.rateScriptsInstance().getUri());
		} else {
			String script = inv.getString("script");
			Date startDate = inv.getDate("start-date");
			HhStartDate finishDate = null;
			boolean hasFinished = inv.getBoolean("has-finished");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			script = script.replace("\r", "").replace("\t", "    ");
			if (hasFinished) {
				Date finishDateRaw = inv.getDate("finish-date");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
				Calendar cal = MonadDate.getCalendar();
				cal.setTime(finishDateRaw);
				cal.add(Calendar.DAY_OF_MONTH, 1);
				finishDate = HhStartDate.roundDown(cal.getTime()).getPrevious();
			}
			try {
				update(HhStartDate.roundDown(startDate), finishDate, script);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc, new XmlTree("contract",
				new XmlTree("party"))));
		sourceElement.appendChild(MonadDate.getMonthsXml(doc));
		sourceElement.appendChild(MonadDate.getDaysXml(doc));
		sourceElement.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public Invocable invocableEngine() throws HttpException {
		ScriptEngineManager engineMgr = new ScriptEngineManager();
		ScriptEngine scriptEngine = engineMgr.getEngineByName("jython");
		Invocable invocableEngine = null;
		try {
			scriptEngine.eval(script);
			invocableEngine = (Invocable) scriptEngine;
		} catch (ScriptException e) {
			throw new UserException(e.getMessage());
		}
		return invocableEngine;
	}

	public Object getRate(String rateName) throws HttpException {
		Object rate = null;
		try {
			rate = invocableEngine().invokeFunction(rateName, new Object[0]);
		} catch (ScriptException e) {
			throw new UserException(e.getMessage());
		} catch (NoSuchMethodException e) {
			throw new UserException("The rate script " + getUri()
					+ " has no such method: " + e.getMessage());
		} catch (PyException e) {
			Object obj = e.value.__tojava__(HttpException.class);
			if (obj instanceof HttpException) {
				throw (HttpException) obj;
			} else {
				throw new UserException(e.toString());
			}
		}
		return rate;
	}
}
