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
						select="/source/batches/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/batches/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/batches/supplier-service/@name" />
					&gt; Batches
				</title>
			</head>

			<body>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>

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
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/">
						<xsl:value-of
							select="/source/batches/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/suppliers/{/source/batches/supplier-service/supplier/@id}/">
						<xsl:value-of
							select="/source/batches/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/suppliers/{/source/batches/supplier-service/supplier/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/suppliers/{/source/batches/supplier-service/supplier/@id}/services/{/source/batches/supplier-service/@id}/">
						<xsl:value-of
							select="/source/batches/supplier-service/@name" />
					</a>
					&gt; Batches
				</p>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new batch'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<ul>
							<xsl:for-each
								select="/source/batches/batch">
								<li>
									<a href="{@id}/">
										<xsl:value-of
											select="@reference" />
									</a>
								</li>
							</xsl:for-each>
						</ul>
						<br />
						<hr />
						<form action="." method="post">
							<fieldset>
								<legend>Add a batch</legend>
								<label>
									<xsl:value-of select="'Reference '" />
									<input name="reference"
										value="{/source/request/parameter[@name = 'reference']/value}" />
								</label>
								<br />
								<br />
								<input type="submit" value="Add" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>