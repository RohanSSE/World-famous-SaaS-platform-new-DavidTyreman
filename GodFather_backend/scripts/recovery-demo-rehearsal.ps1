param(
  [string]$BaseUrl = "http://localhost:8000/api",
  [Parameter(Mandatory = $true)] [string]$Token,
  [Parameter(Mandatory = $true)] [string]$UserId,
  [string]$OutputDir = "recovery-demo-evidence-2026-06-22",
  [string]$CampaignSessionId = ""
)

$ErrorActionPreference = "Stop"
$Headers = @{ Authorization = "Bearer $Token"; "Content-Type" = "application/json" }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Save-JsonEvidence {
  param([string]$Name, [object]$Value)
  $Path = Join-Path $OutputDir $Name
  $Value | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 -Path $Path
}

function Invoke-DemoJson {
  param([string]$Method, [string]$Uri, [object]$Body = $null)
  try {
    if ($null -eq $Body) {
      return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers
    }
    $JsonBody = $Body | ConvertTo-Json -Depth 20
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body $JsonBody
  } catch {
    $StatusCode = $null
    if ($_.Exception.Response) {
      $StatusCode = [int]$_.Exception.Response.StatusCode
    }
    return @{ demo_request_failed = $true; status_code = $StatusCode; error = $_.Exception.Message; uri = $Uri }
  }
}

function New-OrbSession {
  param([string]$Label)
  $Body = @{
    user_id = $UserId
    context_data = @{
      source = "recovery-demo"
      source_session_id = "recovery-demo-$Label-2026-06-22"
    }
  }
  return Invoke-DemoJson -Method "Post" -Uri "$BaseUrl/brandgodfather/session/start/" -Body $Body
}

function Submit-OrbAnswer {
  param([string]$SessionId, [string]$QId, [string]$Answer)
  $Body = @{ session_id = $SessionId; q_id = $QId; answer = $Answer; "async" = $false }
  return Invoke-DemoJson -Method "Post" -Uri "$BaseUrl/brandgodfather/answer/" -Body $Body
}

$Orb = New-OrbSession -Label "orb"
Save-JsonEvidence -Name "01-session-start.json" -Value $Orb
$OrbSessionId = $Orb.session_id
Save-JsonEvidence -Name "02-live-orb-experience.json" -Value (Submit-OrbAnswer -SessionId $OrbSessionId -QId "Q1" -Answer "I want people to trust themselves more when they are making hard choices.")

$Strategic = New-OrbSession -Label "strategic-challenge"
Save-JsonEvidence -Name "03-strategic-challenge.json" -Value (Submit-OrbAnswer -SessionId $Strategic.session_id -QId "Q1" -Answer "We help everyone grow.")

$Vendor = New-OrbSession -Label "vendor-interruption"
Save-JsonEvidence -Name "04-vendor-interruption.json" -Value (Submit-OrbAnswer -SessionId $Vendor.session_id -QId "Q1" -Answer "We provide quality professional service.")

$Contradiction = New-OrbSession -Label "contradiction"
Save-JsonEvidence -Name "05-contradiction-setup.json" -Value (Submit-OrbAnswer -SessionId $Contradiction.session_id -QId "Q2" -Answer "We are premium and not price-led because our best clients hire us when clarity matters more than saving money.")
Save-JsonEvidence -Name "06-contradiction-detection.json" -Value (Submit-OrbAnswer -SessionId $Contradiction.session_id -QId "Q3" -Answer "Our edge is being cheaper than everyone.")

$Adaptive = New-OrbSession -Label "adaptive-coaching"
Save-JsonEvidence -Name "07-adaptive-coaching-1.json" -Value (Submit-OrbAnswer -SessionId $Adaptive.session_id -QId "Q1" -Answer "I help people.")
Save-JsonEvidence -Name "07-adaptive-coaching-2.json" -Value (Submit-OrbAnswer -SessionId $Adaptive.session_id -QId "Q1" -Answer "I help people.")
Save-JsonEvidence -Name "07-adaptive-coaching-3.json" -Value (Submit-OrbAnswer -SessionId $Adaptive.session_id -QId "Q1" -Answer "I help people.")

$Breakthrough = New-OrbSession -Label "breakthrough"
$BreakthroughResult = Submit-OrbAnswer -SessionId $Breakthrough.session_id -QId "Q1" -Answer "I built this because founders like me hide behind expertise when they are afraid to be seen."
Save-JsonEvidence -Name "08-breakthrough-recognition.json" -Value $BreakthroughResult
Save-JsonEvidence -Name "08-breakthrough-session-detail.json" -Value (Invoke-DemoJson -Method "Get" -Uri "$BaseUrl/brandgodfather/session/$($Breakthrough.session_id)/")

$CampaignSourceSessionId = $CampaignSessionId
if ([string]::IsNullOrWhiteSpace($CampaignSourceSessionId)) {
  $CampaignSourceSessionId = $Breakthrough.session_id
}
Save-JsonEvidence -Name "09-campaign-output.json" -Value (Invoke-DemoJson -Method "Get" -Uri "$BaseUrl/brandgodfather/output/$CampaignSourceSessionId/campaign/")

$Notes = @"
# Complete Journey Notes

- Evidence generated at: $(Get-Date -Format o)
- ORB session: $OrbSessionId
- Strategic challenge session: $($Strategic.session_id)
- Vendor interruption session: $($Vendor.session_id)
- Contradiction session: $($Contradiction.session_id)
- Adaptive coaching session: $($Adaptive.session_id)
- Breakthrough session: $($Breakthrough.session_id)
- Campaign source session: $CampaignSourceSessionId

Review every JSON file before the client demo. Do not claim a capability complete if the JSON shows `demo_request_failed`, missing fields, or generic output.
"@
$Notes | Set-Content -Encoding UTF8 -Path (Join-Path $OutputDir "10-complete-journey-notes.md")

Write-Host "Recovery demo evidence written to $OutputDir"