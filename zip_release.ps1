# Zip file will be created next to the script
$ZipName = Join-Path $PSScriptRoot "dissolve_objects-v1.zip"

# Files/folders to include
$ItemsToZip = @(
    "__init__.py"
) | ForEach-Object { Join-Path $PSScriptRoot $_ }

# Remove old zip
if (Test-Path $ZipName) {
    Remove-Item $ZipName -Force
}

Compress-Archive -Path $ItemsToZip -DestinationPath $ZipName

Write-Host "Created $ZipName"