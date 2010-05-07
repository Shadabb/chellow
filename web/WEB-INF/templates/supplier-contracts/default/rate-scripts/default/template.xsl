<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd"
		indent="yes" />
	<xsl:template match="/">
		<html>
			<head>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />
				<title>
					Chellow &gt; Supplier Contracts &gt;
					<xsl:value-of select="/source/rate-script/supplier-contract/@name" />
					&gt; Rate Scripts &gt;
					<xsl:value-of select="/source/rate-script/@id" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/rate-script/supplier-contract/@id}/">
						<xsl:value-of select="/source/rate-script/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/rate-script/supplier-contract/@id}/rate-scripts/">
						<xsl:value-of select="'Rate Scripts'" />
					</a>
					&gt;
					<xsl:value-of select="concat(/source/rate-script/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/reports/79/output/?rate-script-id={/source/rate-script/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>
									Are you sure you want to delete this
									rate script?
								</legend>
								<input type="submit" name="delete" value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<form action="." method="post">
							<fieldset>
								<legend>Update rate-script</legend>
								<br />
								<fieldset>
									<legend>Start date</legend>
									<input name="start-date-year" size="4" maxlength="4">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='start-date-year']">
												<xsl:attribute name="value">
													<xsl:value-of
													select="/source/request/parameter[@name='start-date-year']/value/text()" />
												</xsl:attribute>
											</xsl:when>
											<xsl:otherwise>
												<xsl:attribute name="value">
													<xsl:value-of
													select="/source/rate-script/hh-start-date[@label='start']/@year" />
												</xsl:attribute>
											</xsl:otherwise>
										</xsl:choose>
									</input>
									-
									<select name="start-date-month">
										<xsl:for-each select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='start-date-month']">
														<xsl:if
															test="/source/request/parameter[@name='start-date-month']/value/text() = number(@number)">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/rate-script/hh-start-date[@label='start']/@month = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									-
									<select name="start-date-day">
										<xsl:for-each select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='start-date-day']">
														<xsl:if
															test="/source/request/parameter[@name='start-date-day']/value/text() = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/rate-script/hh-start-date[@label='start']/@day = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									<xsl:value-of
										select="concat(' ', /source/rate-script/hh-start-date[@label='start']/@hour, ':', /source/rate-script/hh-start-date[@label='start']/@minute, ' Z')" />
								</fieldset>
								<br />
								<fieldset>
									<legend>Finish date</legend>
									<label>
										Ended?
										<input type="checkbox" name="has-finished" value="true">
											<xsl:choose>
												<xsl:when test="/source/request/@method='post'">
													<xsl:if test="/source/request/parameter[@name='has-finished']">
														<xsl:attribute name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/rate-script/hh-start-date[@label='finish']">
														<xsl:attribute name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<input name="finish-date-year" size="4" maxlength="4">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
											test="/source/request/parameter[@name='finish-date-year']">
													<xsl:value-of
											select="/source/request/parameter[@name='finish-date-year']/value/text()" />
												</xsl:when>
												<xsl:when
											test="/source/rate-script/hh-start-date[@label='finish']">
													<xsl:value-of
											select="/source/rate-script/hh-start-date[@label='finish']/@year" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>

									-
									<select name="finish-date-month">
										<xsl:for-each select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='finish-date-month']">

														<xsl:if
															test="/source/request/parameter[@name='finish-date-month']/value/text() = number(@number)">

															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/rate-script/hh-start-date[@label='finish']">
														<xsl:if
															test="/source/rate-script/hh-start-date[@label='finish']/@month = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/date/@month = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>

												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>

									-
									<select name="finish-date-day">
										<xsl:for-each select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='finish-date-day']">

														<xsl:if
															test="/source/request/parameter[@name='finish-date-day']/value/text() = @number">

															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/rate-script/hh-start-date[@label='finish']">
														<xsl:if
															test="/source/rate-script/hh-start-date[@label='finish']/@day = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/date/@day = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									<xsl:choose>
										<xsl:when test="/source/rate-script/hh-start-date[@label='finish']">
											<xsl:value-of
												select="concat(' ', /source/rate-script/hh-start-date[@label='finish']/@hour, ':', /source/rate-script/hh-start-date[@label='finish']/@minute, ' Z')" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="' 00:30 Z'" />
										</xsl:otherwise>
									</xsl:choose>
								</fieldset>
								<br />
								Script
								<br />
								<textarea name="script" rows="40" cols="80">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='script']">
											<xsl:value-of
												select="translate(/source/request/parameter[@name='script']/value, '&#xD;','')" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/rate-script/@script" />
										</xsl:otherwise>
									</xsl:choose>
								</textarea>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
								<br />
								<br />
								<fieldset>
									<legend>Test</legend>
									<label>
										<xsl:value-of select="'Bill id '" />
										<input name="bill-id"
											value="{/source/request/parameter[@name='bill-id']/value}" />
									</label>
									<xsl:value-of select="' '" />
									<input type="submit" value="Test without saving" />
								</fieldset>
							</fieldset>
						</form>
						<br/>
						<form action=".">
							<fieldset>
								<input type="hidden" name="view" value="confirm-delete" />
								<legend>Delete this Rate Script</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>