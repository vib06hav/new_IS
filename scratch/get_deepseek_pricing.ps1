$content = Get-Content 'scratch\aicredits_models.txt' -Raw

$patterns = @('deepseek/deepseek-chat"', 'deepseek/deepseek-chat-v3-0324"')
foreach ($p in $patterns) {
    Write-Output "=== $p ==="
    $idx = $content.IndexOf($p)
    if ($idx -gt 0) {
        $snippet = $content.Substring($idx, [Math]::Min(800, $content.Length - $idx))
        $snippet | Select-String -Pattern 'input_cost_per_token|output_cost_per_token|context_length|"name"' | ForEach-Object { $_.Line.Trim() }
    }
    Write-Output ""
}
