"""Install the v0.5.9 Simplified Chinese runtime into a new Windows directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from zipfile import BadZipFile, ZipFile

ORIGINAL_SHA256 = "1604899373b02b1bf382935de197dd580e9861ec29f313a33e8a4da75d6be7ca"
PATCH_SHA256 = "c575e8c899abf722315ea48802035d1657632d8f4e50955942381c186610c484"
EXE = "Metroid Dread.exe"
DATA = "Metroid Dread_data"
GAME_CODE = "Metroid Dread_code.dll"
BASE_FILES = ("SDL2.dll", "zlib1.dll", "README.txt", "update.txt", "recomplauncher.json",
              "vulkan_native/pipeline_recipes_shipped.bin")
BASE_DIRS = ("licenses", "recompiler")
START = ('@echo off\r\nsetlocal\r\npushd "%~dp0" || exit /b 1\r\n'
         '".\\Metroid Dread.exe"\r\nset "game_exit=%errorlevel%"\r\n'
         'popd\r\nexit /b %game_exit%\r\n')


def file_sha256(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def patch_bytes(path):
    with ZipFile(path) as archive:
        info = archive.getinfo(EXE)
        if info.file_size != 11432902:
            raise ValueError("Archive does not contain the expected v0.5.9 Chinese runtime.")
        content = archive.read(info)
    if hashlib.sha256(content).hexdigest() != PATCH_SHA256:
        raise ValueError("Chinese runtime SHA-256 mismatch.")
    return content


def inspect_source(source):
    if file_sha256(source / EXE) != ORIGINAL_SHA256:
        raise ValueError("Select the original Windows x64 v0.5.9 game directory.")
    for name in BASE_FILES:
        if not (source / name).is_file():
            raise ValueError(f"Missing release file: {name}")
    for name in BASE_DIRS:
        if not (source / name).is_dir():
            raise ValueError(f"Missing release directory: {name}")
    data = source / DATA
    code = source / GAME_CODE
    if not data.exists() and not code.exists():
        return False
    required = (data / "exefs" / "main", data / "exefs" / "main.npdm", code)
    romfs = data / "romfs"
    marker = data / "setup.ok"
    if (not all(path.is_file() for path in (*required, marker))
            or not all((romfs / name).is_dir() for name in ("system", "packs"))):
        raise ValueError("Existing setup is incomplete. Finish setup first or use a fresh upstream folder.")
    with marker.open(encoding="utf-8") as f:
        record = json.load(f)
    if record.get("version") != "2.1.0" or record.get("dll_sha256") != file_sha256(code):
        raise ValueError("The installed game DLL does not match its Metroid Dread 2.1.0 setup marker.")
    return True


def copy_file(source, output, name):
    dest = output / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    with (source / name).open("rb") as src, dest.open("xb") as dst:
        shutil.copyfileobj(src, dst)


def install(source, output, content, ready):
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("Choose a separate output directory outside the source directory.")
    output.mkdir()
    for name in BASE_FILES:
        copy_file(source, output, name)
    for name in BASE_DIRS:
        shutil.copytree(source / name, output / name, ignore=shutil.ignore_patterns("__pycache__"))
    if ready:
        copy_file(source, output, GAME_CODE)
        copy_file(source, output, f"{DATA}/setup.ok")
        for name in ("exefs", "romfs"):
            shutil.copytree(source / DATA / name, output / DATA / name)
    with (output / EXE).open("xb") as f:
        f.write(content)
    with (output / "Metroid Dread.ini").open("xb") as f:
        f.write(b"[Display]\r\nlanguage=6\r\n")
    with (output / "Play Metroid Dread CN.cmd").open("xb") as f:
        f.write(START.encode("ascii"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, type=Path, help="Original v0.5.9 folder containing Metroid Dread.exe")
    ap.add_argument("--patch", required=True, type=Path, help="Chinese Windows x64 patch ZIP from Releases")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="New installation directory; its parent must already exist")
    mode.add_argument("--check", action="store_true", help="Validate the source and patch without writing files")
    args = ap.parse_args()
    try:
        source = args.source.resolve(strict=True)
        ready = inspect_source(source)
        content = patch_bytes(args.patch)
        if args.output is not None:
            install(source, args.output.resolve(), content, ready)
            print(f"Launch: {args.output / 'Play Metroid Dread CN.cmd'}")
        else:
            print("Original v0.5.9 and Chinese runtime checksums match.")
        print("Existing 2.1.0 game build is ready." if ready else "First-time game setup will be required.")
    except (OSError, ValueError, BadZipFile, KeyError) as e:
        ap.exit(1, f"{e}\n")


if __name__ == "__main__":
    main()
