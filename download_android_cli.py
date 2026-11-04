#!/usr/bin/env python3
# Copyright (C) 2026 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

BASE_URL = "https://dl.google.com/android/cli"

# List of each host architecture directory name on dl.google.com/android/cli
# (also used in final output path: android_<arch>).
# TODO(b/582756096): Each standalone OS/ABI binary currently embeds a duplicate copy of main.jar
# (~60 MB) alongside its platform JRE (~90 MB total per binary). Switch to a shared JAR layout if
# Android CLI adds support for externalizing main.jar.
ARCH_LIST = (
    'linux_x86_64',
    'darwin_arm64',
)

# List of CLI packs to download and extract for offline execution (e.g. `android analyze`).
# See b/582756527 for improving offline pack configuration and discovery in Android CLI.
PACK_LIST = (
    'optimization',
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_latest_release_version() -> str:
    url = f"{BASE_URL}/latest/{ARCH_LIST[0]}/METADATA"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            metadata = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Failed to fetch latest release version from {url}: {e}.\n"
            f"Please specify a version explicitly using --version."
        ) from e

    for line in metadata.splitlines():
        if line.startswith("version="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"Could not find 'version=' in METADATA:\n{metadata}")


def download_file(url, output_path):
    print(f"Downloading {url} -> {output_path}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response, open(output_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to download {url}: {e}")


def download_binary(version, cli_arch, root_dir):
    binary_url = f"{BASE_URL}/{version}/{cli_arch}/android-cli"
    out_file_path = os.path.join(root_dir, f"android_{cli_arch}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_file_path = os.path.join(tmp_dir, f"android_{cli_arch}")
        download_file(binary_url, temp_file_path)
        os.chmod(temp_file_path, 0o755)
        shutil.move(temp_file_path, out_file_path)


def download_and_extract_pack(version, pack_name, root_dir):
    # Packs are JVM jars and platform-independent; fetch using the first configured arch.
    cli_arch = ARCH_LIST[0]
    zip_url = f"{BASE_URL}/{version}/{cli_arch}/{pack_name}_pack.zip"
    pack_out_dir = os.path.join(root_dir, "packs", pack_name)
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_zip_path = os.path.join(tmp_dir, f"{pack_name}_pack.zip")
        temp_extract_dir = os.path.join(tmp_dir, pack_name)
        os.makedirs(temp_extract_dir, exist_ok=True)
        download_file(zip_url, temp_zip_path)
        print(f"Extracting {temp_zip_path} to {pack_out_dir}...")
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        os.makedirs(os.path.dirname(pack_out_dir), exist_ok=True)
        if os.path.exists(pack_out_dir):
            shutil.rmtree(pack_out_dir)
        shutil.move(temp_extract_dir, pack_out_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Download Android CLI binaries and packs for offline execution."
    )
    parser.add_argument(
        '--version', '-v',
        help="Android CLI version to download (e.g. '1.1.16717390'). Defaults to fetching the latest release."
    )
    args = parser.parse_args()

    version = args.version
    if not version:
        print("No version specified. Fetching latest release version...")
        version = get_latest_release_version()
    print(f"Using Android CLI version: {version}")

    for cli_arch in ARCH_LIST:
        print(f"\nDownloading Android CLI binary for architecture: {cli_arch}")
        download_binary(version, cli_arch, ROOT_DIR)

    for pack_name in PACK_LIST:
        print(f"\nDownloading and extracting pack: {pack_name}")
        download_and_extract_pack(version, pack_name, ROOT_DIR)

    version_file = os.path.join(ROOT_DIR, "VERSION")
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(f"{version}\n")

    print(f"\nSuccessfully updated Android CLI binaries and packs to version {version}!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
