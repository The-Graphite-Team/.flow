# Verifying .flow releases

A downloaded executable should be checked before running. There are three separate questions:

1. **Integrity:** Is this file byte-for-byte the file published in the release?
2. **Provenance:** Was it built by the repository's GitHub Actions workflow from the expected source revision?
3. **Publisher identity:** Has a trusted certificate verified who signed the executable?

The release workflow publishes SHA-256 checksums and a GitHub build-provenance attestation. The executable is currently **not Authenticode code-signed**, so Windows may still display an unknown-publisher or SmartScreen warning.

## 1. Check the SHA-256 checksum

Download `flow-runner-windows.zip` and `SHA256SUMS.txt` from the same GitHub Release.

In PowerShell, run:

```powershell
Get-FileHash .\\flow-runner-windows.zip -Algorithm SHA256
```

Compare the displayed hash with the line for `flow-runner-windows.zip` in `SHA256SUMS.txt`. They must match exactly.

You can check the standalone executable too:

```powershell
Get-FileHash .\\flow_runner.exe -Algorithm SHA256
```

A checksum downloaded from the same release detects accidental corruption and mismatched downloads. By itself, it does **not** prove who created the file, because an attacker who replaces both files could also replace the checksum.

## 2. Verify the GitHub build attestation

The release workflow creates a GitHub artifact attestation for the executable and ZIP package.

Install the GitHub CLI (`gh`), sign in, and run:

```powershell
gh attestation verify .\\flow_runner.exe -R The-Graphite-Team/.flow
gh attestation verify .\\flow-runner-windows.zip -R The-Graphite-Team/.flow
```

A successful verification means GitHub can validate the artifact's recorded build provenance against the repository and workflow identity. Check that the repository is `The-Graphite-Team/.flow` and that the workflow is the project's release workflow.

If verification fails, reports the wrong repository/workflow, or no attestation is found, do not run the file. Check that you downloaded it from the official Releases page.

## 3. Check Authenticode signing status

In PowerShell:

```powershell
Get-AuthenticodeSignature .\\flow_runner.exe | Format-List Status,StatusMessage,SignerCertificate
```

At present, the expected status is `NotSigned`. That is because the project has not configured a code-signing certificate. It is not a checksum or build failure.

A future signed release should show a valid signature and a trusted publisher certificate. A self-signed certificate does not provide the same public trust as a certificate issued by a trusted code-signing authority.

## 4. Scan the download

- Keep Microsoft Defender real-time protection enabled and scan the extracted executable.
- You may submit the file to VirusTotal for an additional multi-engine scan. Files submitted there may be shared with security vendors and researchers, so do not upload private or confidential files.
- If Defender reports a detection, stop and investigate it. Do not add an exclusion just to make the warning disappear.

## What would make Windows trust it more?

For the familiar verified-publisher experience, the project needs an Authenticode code-signing certificate from a trusted certificate authority, secure storage for its private key, and a signing step in the release workflow. A certificate costs money and must be protected carefully. A certificate does not replace reproducible builds, checksums, or provenance attestations.

## Official project links

- Releases: https://github.com/The-Graphite-Team/.flow/releases
- Source code: https://github.com/The-Graphite-Team/.flow
- Build workflow: https://github.com/The-Graphite-Team/.flow/actions
