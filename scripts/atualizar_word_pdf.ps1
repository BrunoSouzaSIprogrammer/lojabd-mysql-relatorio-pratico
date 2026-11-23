param(
    [Parameter(Mandatory = $true)]
    [string]$DocxPath,

    [Parameter(Mandatory = $true)]
    [string]$PdfPath
)

$ErrorActionPreference = "Stop"
$word = $null
$doc = $null

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0

    $doc = $word.Documents.Open($DocxPath)
    $doc.Repaginate()

    foreach ($toc in $doc.TablesOfContents) {
        $toc.Update()
    }

    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    $doc.Save()
    $doc.SaveAs([ref]$PdfPath, [ref]17)

    Write-Output ("TOC_COUNT=" + $doc.TablesOfContents.Count)
}
finally {
    if ($null -ne $doc) {
        $doc.Close($false)
    }
    if ($null -ne $word) {
        $word.Quit()
    }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
