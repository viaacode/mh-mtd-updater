<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:mh="https://zeticon.mediahaven.com/metadata/25.1/mh/"
    xmlns:mhs="https://zeticon.mediahaven.com/metadata/25.1/mhs/"
    exclude-result-prefixes="xsl"
    version="3.0">
  <xsl:output method="xml" indent="yes" omit-xml-declaration="yes" encoding="UTF-8" />

  <!-- Identity template: copy over everything to the result tree except... -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>

  <!-- ... except these nodes: they are explicitly matched to not copy them over to the result tree. -->
  <xsl:template match="/mhs:Sidecar/mhs:Administrative" />
  <xsl:template match="/mhs:Sidecar/mhs:Technical" />
  <xsl:template match="/mhs:Sidecar/mhs:Internal" />
  <xsl:template match="/mhs:Sidecar/mhs:Structural" />
  <xsl:template match="/mhs:Sidecar/mhs:RightsManagement" />

</xsl:transform>
