param(
    [Parameter(Mandatory=$true)]
    [string]$RepoUrl
)

$ErrorActionPreference = "Stop"

$existingOrigin = git -c "safe.directory=*" remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0 -and $existingOrigin) {
    Write-Host "Atualizando remote 'origin' para: $RepoUrl"
    git -c "safe.directory=*" remote set-url origin $RepoUrl
} else {
    Write-Host "Adicionando remote 'origin': $RepoUrl"
    git -c "safe.directory=*" remote add origin $RepoUrl
}

Write-Host "Enviando branch 'main' para o GitHub..."
git -c "safe.directory=*" push -u origin main

Write-Host "Concluído! Repositório publicado em: $RepoUrl"
