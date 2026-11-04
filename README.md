# Android CLI Prebuilts

This repository contains prebuilt [Android CLI](https://d.android.com/tools/agents/android-cli)
binaries and packs (such as the `optimization` pack used by `android analyze`) for hermetic,
offline execution during AndroidX Gradle builds.

To download the latest release of the Android CLI binaries and packs:

```bash
./download_android_cli.py [--version <version>]
```

By default, the script queries `https://dl.google.com/android/cli/latest/linux_x86_64/METADATA`
to fetch and download the latest release. Alternatively, you can specify a version explicitly:

```bash
./download_android_cli.py --version 1.1.16717390
```

This script:
 - Downloads standalone `android` executables (`android_linux_x86_64`, `android_darwin_arm64`)
   for supported host architectures.
 - Downloads and extracts required packs (including `packs/optimization/optimization.jar`) so
   `android analyze` runs without network access on build machines.
 - Records the downloaded CLI version in `VERSION`.
