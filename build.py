"""Build the Windows x64 Simplified Chinese runtime against upstream v0.5.9."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
SOURCE_SHA256 = "043f4a99b3c4280b5952347747458474308b3fc22bd14b9326b2f4fc3c804804"

LINK = """
import os
import switchrecomp

original_run_cc = switchrecomp.run_cc

def run_ucrt(args, compiler, **kwargs):
    # The UCRT loader already provides the __intrinsic_setjmpex used by libvpx.
    args = [arg for arg in args if arg != '-Wl,--defsym,__intrinsic_setjmpex=_setjmpex']
    return original_run_cc(args, compiler, **kwargs)

switchrecomp.run_cc = run_ucrt
switchrecomp.build_runtime(os.environ['DREAD_ZH_GCC'], os.environ['DREAD_ZH_OUT'], True, 'win32', print)
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream-zip", required=True, type=Path)
    ap.add_argument("--gcc-bin", required=True, type=Path, help="WinLibs GCC 14.2 UCRT mingw64/bin")
    ap.add_argument("--glslang", required=True, type=Path, help="Khronos glslang.exe 16.6.0")
    ap.add_argument("--work", required=True, type=Path, help="New build directory with an ASCII path")
    args = ap.parse_args()
    gcc, glslang, work = (p.resolve() for p in (args.gcc_bin, args.glslang, args.work))
    if any(not str(p).isascii() for p in (gcc, glslang, work)):
        ap.error("Use ASCII-only paths for the toolchain and build directory.")
    for exe in (gcc / "gcc.exe", gcc / "g++.exe", glslang):
        if not exe.is_file():
            ap.error(f"Missing tool: {exe}")
    with args.upstream_zip.open("rb") as f:
        if hashlib.file_digest(f, "sha256").hexdigest() != SOURCE_SHA256:
            ap.error("Unexpected upstream source archive SHA-256.")
    work.mkdir()
    with ZipFile(args.upstream_zip) as archive:
        archive.extractall(work)
    source = work / "Metroid-Dread-Recomp-0.5.9"
    generated = work / "localized-ui"
    subprocess.run([sys.executable, "-B", str(HERE / "localize_ui.py"), "--upstream", str(source),
                    "--output", str(generated)], check=True)
    for path in generated.iterdir():
        shutil.copyfile(path, source / "runtime" / "dread_ui" / path.name)
    out = work / "Metroid Dread.exe"
    env = dict(os.environ, SWR_GCC_BIN=str(gcc), GLSLANG=str(glslang), SWR_RELEASE="1",
               DREAD_ZH_GCC=str(gcc / "gcc.exe"), DREAD_ZH_OUT=str(out))
    env.pop("SWR_NO_DLSS", None)
    env.pop("SWR_NO_FRONTEND", None)
    env.pop("SWR_NO_SNXVK", None)
    for script in ("build_imgui.py", "build_snxvk2.py"):
        subprocess.run([sys.executable, "-B", "work-profiler/" + script], cwd=source, env=env, check=True)
    subprocess.run([sys.executable, "-B", "-c", LINK], cwd=source, env=env, check=True)
    print(out)


if __name__ == "__main__":
    main()
