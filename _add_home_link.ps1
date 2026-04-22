$root = "c:\Users\33612\Documents\site_COCOtheaxolotl"
$homeLink = '<a class="home-link" href="/"><span data-lang="en">&larr; Home</span><span data-lang="fr">&larr; Accueil</span><span data-lang="es">&larr; Inicio</span></a>'
$count = 0

Get-ChildItem -Path $root -Recurse -Filter 'index.html' | ForEach-Object {
    if ($_.FullName -eq (Join-Path $root 'index.html')) { return }
    $c = [System.IO.File]::ReadAllText($_.FullName)
    if ($c.Contains('<header>') -and (-not $c.Contains('home-link'))) {
        $c = $c.Replace('<header>', "<header>`r`n$homeLink")
        [System.IO.File]::WriteAllText($_.FullName, $c)
        $count++
        Write-Host "Updated: $($_.FullName)"
    }
}
Write-Host "Total: $count files updated"
