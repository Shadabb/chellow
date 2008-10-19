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
				<title>Chellow</title>
			</head>
			<body>
				<p>
					<img src="{/source/request/@context-path}/logo/" />
					<span class="logo">Chellow</span>
				</p>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li class="error">
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/reports/1/output/">
							Viewer's Home
						</a>
					</li>

					<li>
						<a href="http://chellow.wikispaces.com/"
							target="_blank">
							Docs
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/sites/">
							Sites
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/supplies/">
							Supplies
						</a>
					</li>

					<li>
						<a
							href="{/source/request/@context-path}/supplier-contracts/">
							Supplier Contracts
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/hhdc-contracts/">
							HHDC Contracts
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/non-core-contracts/">
							Non-core Contracts
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/reports/">
							Reports
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/general-imports/">
							General CSV Imports
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/users/">
							Users
						</a>
						<ul>
							<li>
								<a
									href="{/source/request/@context-path}/users/me/">
									Me
								</a>
							</li>
						</ul>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/configuration/">
							Configuration
						</a>
					</li>
				</ul>
				<h2>Industry Info</h2>
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/read-types/">
							Read types
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/market-roles/">
							Market Roles
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/dsos/">
							DSOs
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/providers/">
							Providers
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/participants/">
							Market Participants
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/sources/">
							Sources
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/pcs/">
							Profile Classes
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/meter-types/">
							Meter Types
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/meter-payment-types/">
							Meter Payment Types
						</a>
					</li>

					<li>
						<a
							href="{/source/request/@context-path}/mtcs/">
							MTCs
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/tprs/">
							TPRs
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/sscs/">
							SSCs
						</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>