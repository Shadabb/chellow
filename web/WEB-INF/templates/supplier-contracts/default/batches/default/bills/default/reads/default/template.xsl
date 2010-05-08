<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN"
		doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes" />

	<xsl:template match="/">
		<html>
			<head>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />

				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/register-read/invoice/batch/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/register-read/invoice/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of
						select="/source/register-read/invoice/batch/@name" />
					&gt; Invoices &gt;
					<xsl:value-of
						select="/source/register-read/invoice/@id" />
					&gt; Reads &gt;
					<xsl:value-of select="/source/register-read/@id" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/batch/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/supplier-contracts/{/source/register-read/invoice/batch/supplier-contract/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/supplier-contracts/{/source/register-read/invoice/batch/supplier-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/supplier-contracts/{/source/register-read/invoice/batch/supplier-contract/@id}/batches/{/source/register-read/invoice/batch/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/supplier-contracts/{/source/register-read/invoice/batch/supplier-contract/@id}/batches/{/source/register-read/invoice/batch/@id}/invoices/">
						<xsl:value-of select="'Invoices'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/supplier-contracts/{/source/register-read/invoice/batch/supplier-contract/@id}/batches/{/source/register-read/invoice/batch/@id}/invoices/{/source/register-read/invoice/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/supplier-contracts/{/source/register-read/invoice/batch/supplier-contract/@id}/batches/{/source/register-read/invoice/batch/@id}/invoices/{/source/register-read/invoice/@id}/reads/">
						<xsl:value-of select="'Reads'" />
					</a>
					&gt;
					<xsl:value-of select="/source/register-read/@id" />
				</p>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>
									Are you sure you want to delete this
									register read?
								</legend>
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<form action="." method="post">
							<fieldset>
								<legend>Update this read</legend>
								<br />
								<label>
									<xsl:value-of select="'MPAN '" />
									<input name="mpan">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='mpan']">
											<xsl:value-of
														select="/source/request/parameters[@name='mpan']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/register-read/mpan/@mpan" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-contract/org/@id}/supplies/{/source/register-read/mpan/supply-generation/supply/@id}/generations/{/source/register-read/mpan/supply-generation/@id}/">
										<xsl:value-of
											select="/source/register-read/mpan/@mpan" />
									</a>
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of
										select="'Coefficient '" />
									<input name="coefficient">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='coefficient']">
											<xsl:value-of
														select="/source/request/parameters[@name='coefficient']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/register-read/@coefficient" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>

								</label>
								<br />
								<label>
									<xsl:value-of select="'Units '" />
									<input name="units">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='units']">
											<xsl:value-of
														select="/source/request/parameters[@name='units']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/register-read/@units" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									<xsl:value-of select="'TPR '" />
									<input name="tpr">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='tpr']">
											<xsl:value-of
														select="/source/request/parameters[@name='tpr']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/register-read/tpr/@code" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/tprs/{/source/register-read/tpr/@id}/">
										<xsl:value-of
											select="/source/register-read/tpr/@code" />
									</a>
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Previous Read Date</legend>
									<input
										name="previous-read-date-year" size="4" maxlength="4">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameter[@name='previous-read-date-year']">
											<xsl:value-of
														select="/source/request/parameter[@name='previous-read-date-year']/value/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/register-read/day-finish-date[@label='previous']/@year" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
									-
									<select
										name="previous-read-date-month">
										<xsl:for-each
											select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='previous-read-date-month']">
														<xsl:if
															test="/source/request/parameter[@name='previous-read-date-month']/value/text() = number(@number)">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/register-read/day-finish-date[@label='previous']/@month = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="@number" />
											</option>
										</xsl:for-each>
									</select>
									-
									<select
										name="previous-read-date-day">
										<xsl:for-each
											select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='previous-read-date-day']">
														<xsl:if
															test="/source/request/parameter[@name='previous-read-date-day']/value/text() = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/register-read/day-finish-date[@label='previous']/@day = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="@number" />
											</option>
										</xsl:for-each>
									</select>
								</fieldset>
								<br />
								<label>
									<xsl:value-of
										select="'Previous value '" />
									<input name="previous-value">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='previous-value']">
											<xsl:value-of
														select="/source/request/parameters[@name='previous-value']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="concat(/source/register-read/@previous-value)" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									<xsl:value-of
										select="'Previous type '" />
									<input name="previous-type">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='previous-type']">
											<xsl:value-of
														select="/source/request/parameters[@name='previous-type']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/register-read/read-type[@label='previous']/@code" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Present Read Date</legend>
									<input name="present-read-date-year"
										size="4" maxlength="4">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameter[@name='present-read-date-year']">
											<xsl:value-of
														select="/source/request/parameter[@name='present-read-date-year']/value/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/register-read/day-finish-date[@label='present']/@year" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
									-
									<select
										name="present-read-date-month">
										<xsl:for-each
											select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='present-read-date-month']">
														<xsl:if
															test="/source/request/parameter[@name='present-read-date-month']/value/text() = number(@number)">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/register-read/day-finish-date[@label='present']/@month = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="@number" />
											</option>
										</xsl:for-each>
									</select>
									-
									<select
										name="present-read-date-day">
										<xsl:for-each
											select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='present-read-date-day']">
														<xsl:if
															test="/source/request/parameter[@name='present-read-date-day']/value/text() = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/register-read/day-finish-date[@label='present']/@day = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="@number" />
											</option>
										</xsl:for-each>
									</select>
								</fieldset>
								<br />
								<label>
									<xsl:value-of
										select="'Present value '" />
									<input name="present-value">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='present-value']">
											<xsl:value-of
														select="/source/request/parameters[@name='present-value']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="concat(/source/register-read/@present-value)" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									<xsl:value-of
										select="'Present type '" />
									<input name="present-type">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='present-type']">
											<xsl:value-of
														select="/source/request/parameters[@name='present-type']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/register-read/read-type[@label='present']/@code" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<legend>Delete this read</legend>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>