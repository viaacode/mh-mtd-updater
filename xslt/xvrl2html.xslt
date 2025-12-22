<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:mh="https://zeticon.mediahaven.com/metadata/25.1/mh/"
    xmlns:mhs="https://zeticon.mediahaven.com/metadata/25.1/mhs/"
    xmlns:xvrl="http://www.xproc.org/ns/xvrl"
    xmlns:mets="http://www.loc.gov/METS/"
    xmlns:premis="info:lc/xmlns/premis-v2"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:mm="http://www.meemoo.be/ns"
    exclude-result-prefixes="xsl xs xsi mets premis xlink mhs mh xvrl"
    version="3.0">
  <xsl:output method="xhtml" omit-xml-declaration="yes" include-content-type="no" encoding="UTF-8" html-version="5.0" />
  <xsl:variable name="report-title" as="xs:string*">Report for: <xsl:value-of select="/xvrl:reports/xvrl:metadata/xvrl:supplemental/mh:OrganisationExternalId/text()" /> (<xsl:value-of select="/xvrl:reports/xvrl:metadata/xvrl:supplemental/mh:OrganisationName/text()" />)</xsl:variable>
  <xsl:variable name="issue-url" as="xs:string">https://meemoo.atlassian.net/browse/</xsl:variable>
  <xsl:variable name="issue-reference" as="xs:string"><xsl:value-of select="/xvrl:reports/xvrl:metadata/xvrl:supplemental/mm:UpdateRun/@reference" /></xsl:variable>
  <xsl:variable name="mh-monitoring-url" as="xs:string" select="'https://archief.viaa.be/monitoring/index.php'"></xsl:variable>
  <xsl:variable name="header-html">
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="stylesheet" href="report.css" />
    <link rel="icon" href="https://meemoo.be/favicon.ico" type="image/x-icon" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/default.min.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
  </xsl:variable>

  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
      <head>
        <title><xsl:value-of select="$report-title" /></title>
        <meta property="og:title" content="{$report-title}" />
        <meta property="og:description" content="{$report-title}" />
        <xsl:copy-of select="$header-html" />
      </head>
      <body>
        <header>
          <h1><xsl:value-of select="$report-title" /></h1>
          <h2>Metadata</h2>
          <table>
            <tr>
              <th>Reference (Jira-ticket)</th>
              <td><a href="{$issue-url}{$issue-reference}"><xsl:value-of select="xvrl:reports/xvrl:metadata/xvrl:supplemental/mm:UpdateRun/@reference" /></a></td>
            </tr>
            <tr>
              <th>Description</th>
              <td><xsl:value-of select="xvrl:reports/xvrl:metadata/xvrl:supplemental/mm:UpdateRun/text()" /></td>
            </tr>
            <tr>
              <th>CP/Tenant OR-id</th>
              <td><xsl:value-of select="xvrl:reports/xvrl:metadata/xvrl:supplemental/mh:OrganisationExternalId/text()" /></td>
            </tr>
            <tr>
              <th>IdentifierKey</th>
              <td><xsl:value-of select="xvrl:reports/xvrl:metadata/xvrl:supplemental/mm:RecordIdentifierKey/text()" /></td>
            </tr>
            <tr>
              <th>UpdateFields</th>
              <td><pre><xsl:value-of select="xvrl:reports/xvrl:metadata/xvrl:supplemental/mm:UpdateFields/text()" /></pre></td>
            </tr>
            <tr>
              <th>StartTime</th>
              <td><xsl:value-of select="xvrl:reports/xvrl:metadata/xvrl:supplemental/mm:StartTime/text()" /></td>
            </tr>
            <tr>
              <th>EndTime</th>
              <td><xsl:value-of select="xvrl:reports/xvrl:metadata/xvrl:supplemental/mm:EndTime/text()" /></td>
            </tr>
        </table>
        </header>
        <h2>Records</h2>
        <table>
          <thead>
            <tr>
              <th>Nr</th>
              <th>IdentifierValue</th>
              <th>Type</th>
              <th>Valid?</th>
              <th>MH Monitoring</th>
              <th>Detail</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            <xsl:apply-templates select="xvrl:reports/xvrl:report" mode="overview" />
          </tbody>
        </table>
        <footer>meemoo.be</footer>
      </body>
    </html>

    <xsl:apply-templates select="xvrl:reports/xvrl:report" mode="detail" />
    
  </xsl:template>

  <xsl:template match="xvrl:report" mode="overview">
    <xsl:variable name="output_filename">
      <xsl:value-of select="concat('./', xvrl:metadata/xvrl:supplemental/mm:IdentifierValue/text())" />
      <xsl:text>_</xsl:text>
      <xsl:number count="xvrl:report" />
      <xsl:text>.html</xsl:text>
    </xsl:variable>
    <tr>
      <!-- some attribs -->
      <xsl:attribute name="id"><xsl:value-of select="xvrl:metadata/xvrl:supplemental/mh:ExternalId/text()" /></xsl:attribute>
      <xsl:attribute name="class"><xsl:value-of select="concat('valid-', xvrl:digest/@valid)" /></xsl:attribute>
      <!-- actual table rows -->
      <td><xsl:number count="xvrl:report" /></td>
      <td><xsl:value-of select="xvrl:metadata/xvrl:supplemental/mm:IdentifierValue/text()" /></td>
      <td><xsl:value-of select="xvrl:metadata/xvrl:supplemental/mh:Type/text()" /></td>
      <td><xsl:value-of select="xvrl:digest/@valid" /></td>
      <td>
        <xsl:choose>
            <xsl:when test="xvrl:metadata/xvrl:supplemental/mh:ExternalId/text() != 'N/A'">
              <a><xsl:attribute name="href"><xsl:value-of select="concat($mh-monitoring-url, '?config=default&amp;service=Ingest&amp;values[external_id]=', xvrl:metadata/xvrl:supplemental/mh:ExternalId/text())" /></xsl:attribute>Mh Monitoring</a>
            </xsl:when>
            <xsl:otherwise>N/A</xsl:otherwise>
        </xsl:choose>
      </td>
      <td><a><xsl:attribute name="href"><xsl:value-of select="$output_filename" /></xsl:attribute>Detail</a></td>
      <td><xsl:value-of select="xvrl:detection/xvrl:message/text()" /></td>
    </tr>
  </xsl:template>

  <xsl:template match="xvrl:report" mode="detail">
    <!-- TODO: How to make sure we output these detail reports in the current dir...? -->
    <xsl:variable name="current-report-count"><xsl:number count="xvrl:report" /></xsl:variable>
    <xsl:variable name="output_filename">
      <xsl:value-of select="concat('./', xvrl:metadata/xvrl:supplemental/mm:IdentifierValue/text())" />
      <xsl:text>_</xsl:text>
      <xsl:value-of select="$current-report-count" />
      <xsl:text>.html</xsl:text>
    </xsl:variable>
    <xsl:variable name="thumb-url" as="xs:string"><xsl:value-of select="xvrl:metadata/xvrl:supplemental/mh:PathToKeyframe/text()" /></xsl:variable>
    <xsl:variable name="mh-web-url" as="xs:string"><xsl:value-of select="concat('https://archief.viaa.be/mh/media/search/', xvrl:metadata/xvrl:supplemental/mh:FragmentId/text(), '/details')" /></xsl:variable>
    <xsl:variable name="report-detail-title">Report detail for: <xsl:value-of select="xvrl:metadata/xvrl:supplemental/mm:IdentifierValue/text()" /> (# <xsl:number count="xvrl:report" />)</xsl:variable>
    <xsl:variable name="prev-count"><xsl:value-of select="$current-report-count - 1" /></xsl:variable>
    <xsl:variable name="next-count"><xsl:value-of select="$current-report-count + 1" /></xsl:variable>
    <xsl:variable name="prev-report-url">
      <xsl:value-of select="concat('./', preceding-sibling::xvrl:report[1]/xvrl:metadata/xvrl:supplemental/mm:IdentifierValue/text())" />
      <xsl:text>_</xsl:text>
      <xsl:value-of select="$prev-count" />
      <xsl:text>.html</xsl:text>
    </xsl:variable>
    <xsl:variable name="next-report-url">
      <xsl:value-of select="concat('./', following-sibling::xvrl:report[1]/xvrl:metadata/xvrl:supplemental/mm:IdentifierValue/text())" />
      <xsl:text>_</xsl:text>
      <xsl:value-of select="$next-count" />
      <xsl:text>.html</xsl:text>
    </xsl:variable>
    <xsl:result-document href="{$output_filename}" method="xhtml" omit-xml-declaration="yes" include-content-type="no" encoding="UTF-8" html-version="5.0">
      <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
        <head>
          <title><xsl:value-of select="$report-detail-title" /></title>
          <meta property="og:title" content="{$report-detail-title}" />
          <meta property="og:description" content="{$report-detail-title}" />
          <xsl:copy-of select="$header-html" />
        </head>
        <body>
          <header>
            <h1><xsl:value-of select="$report-detail-title" /></h1>
            <p><a href="{$prev-report-url}">&lt; Previous</a> - <a href="./report.html">Up</a> - <a href="{$next-report-url}">Next &gt;</a></p>
          </header>
          <table>
            <tr>
              <th>Status</th>
              <td><xsl:attribute name="class"><xsl:value-of select="concat('valid-', xvrl:digest/@valid)" /></xsl:attribute>digest/@valid=<xsl:value-of select="xvrl:digest/@valid" /></td>
            </tr>
            <tr>
              <th>ErrorReason</th>
              <td>
                <xsl:choose>
                    <xsl:when test="xvrl:detection/xvrl:message/text()">
                      <pre><xsl:value-of select="xvrl:detection/xvrl:message/text()" /></pre>
                    </xsl:when>
                    <xsl:otherwise>N/A</xsl:otherwise>
                </xsl:choose>
              </td>
            </tr>
            <tr>
              <th>CsvRow</th>
              <td><pre><xsl:value-of select="xvrl:metadata/xvrl:supplemental/mm:CsvRow/text()" /></pre></td>
            </tr>
            <tr>
              <th>MhOriginalRecord</th>
              <td>
                <details>
                  <summary>MhOriginalRecord</summary>
                  <pre lang="xml"><code class="language-xml"><xsl:value-of select="xvrl:metadata/xvrl:supplemental/mm:MhOriginalRecord/text()" /></code></pre>
                </details>
              </td>
            </tr>
            <tr>
              <th>MhUpdateRecord</th>
              <td>
                <details>
                  <summary>MhUpdateRecord</summary>
                  <pre lang="xml"><code class="language-xml"><xsl:value-of select="xvrl:metadata/xvrl:supplemental/mm:MhUpdateRecord/text()" /></code></pre>
                </details>
              </td>
            </tr>
            <tr>
              <th>MHThumbLink</th>
              <td>
                <a href="{$mh-web-url}">
                  <img src="{$thumb-url}" style="max-height: 200px; max-width: 200px" />
                </a>
              </td>
            </tr>
        </table>
        </body>
      </html>
    </xsl:result-document>
  </xsl:template>
    
</xsl:transform>
