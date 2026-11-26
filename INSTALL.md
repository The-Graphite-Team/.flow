# Installing .flow on Windows

## Quick install

1. Open the **Releases** page: https://github.com/The-Graphite-Team/.flow/releases
2. Download the latest `flow-runner-windows.zip`.
3. Extract the ZIP to a normal folder, for example `Documents\\Flow`.
4. Open the extracted folder.
5. Double-click `flow_runner.exe`, or run it from PowerShell with a file path:

   ```powershell
   .\\flow_runner.exe .\\examples\\startup-demo.flow
   ```

6. The runner generates an HTML flowchart. Open the generated HTML file in your browser.

You can also download the standalone `flow_runner.exe` release asset. The ZIP is recommended because it includes examples, the licence, and the verification instructions.

## Run a flow file

From PowerShell, change to the folder containing the executable and your `.flow` file:

```powershell
.\\flow_runner.exe .\\examples\\startup-demo.flow
```

To choose the output file and avoid automatically opening it:

```powershell
.\\flow_runner.exe .\\examples\\startup-demo.flow --output .\\startup-demo.html --no-open
```

## Windows SmartScreen

The release executable is currently **not code-signed**. Windows may show a Microsoft Defender SmartScreen warning because the publisher is unverified or the file has not built up reputation.

Do not treat that warning as proof that the program is malicious, but do not blindly bypass it either. First verify the SHA-256 checksum using [VERIFYING.md](VERIFYING.md), inspect the release provenance, and scan the file with Microsoft Defender. If the checksum does not match the release, delete the file and download it again.

## Build from source instead

If you would rather not run a prebuilt executable:

1. Install Python 3.10 or newer.
2. Download the source code from the repository.
3. Open PowerShell in the source folder.
4. Run:

   ```powershell
   python flow_runner.py examples/startup-demo.flow
   ```

The source runner has no third-party runtime dependencies. PyInstaller is only needed if you want to build your own Windows executable.
