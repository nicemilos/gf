"""Build Windows x64 ZIP + optional Inno Setup installer, then hash artifacts."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True, help='e.g. 0.1.0 (without v)')
    parser.add_argument('--iscc', type=Path, help='Path to Inno Setup ISCC.exe')
    args = parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?', args.version):
        parser.error('Expected a semantic version, e.g. 0.1.0')
    if sys.platform != 'win32' or platform.machine().lower() not in ('amd64', 'x86_64'):
        parser.error('Build with 64-bit Python on Windows x64')
    run(sys.executable, '-m', 'PyInstaller', '--noconfirm', 'Xiaoya.spec')
    app = ROOT / 'dist' / 'Xiaoya'
    # A real packaged startup check, with isolated memory storage.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='xiaoya-smoke-') as data:
        subprocess.run([str(app / 'Xiaoya.exe'), '--smoke-test'], cwd=app,
                       env={**os.environ, 'XIAOYA_DATA_DIR': data}, timeout=45, check=True)
    output = ROOT / 'dist' / 'release'
    output.mkdir(parents=True, exist_ok=True)
    (app / '使用说明.txt').write_text(
        '小雅 ' + args.version + '\n\n'
        '请先完整解压，再双击 Xiaoya.exe。不需要安装 Python。\n'
        '请保留 _internal 文件夹。左键说话，拖动跑步，双击跳跃。\n'
        '右键菜单：聊天、模型配置、性格与记忆、切换形象、大小、退出。\n'
        '躲起来：自动跑到最近的左右屏幕边缘探头；快回来：返回屏幕内。\n'
        '也可以拖到屏幕左右外边缘探头，再抓住她往内拖回来。\n'
        '模型 Key 请在本机配置，不要发给他人。聊天会连接配置的厂商。\n'
        '聊天记忆：%LOCALAPPDATA%\\XiaoyaLocal\\Companion\n'
        '升级/卸载不会删除记忆。ZIP 和安装版共用当前用户的记忆。\n'
        '源码和反馈：https://github.com/nicemilos/gf\n', encoding='utf-8-sig')
    artifacts = []
    archive = output / f'Xiaoya-{args.version}-windows-x64-portable.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(app.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(app.parent))
    artifacts.append(archive)
    compiler = args.iscc or shutil.which('iscc')
    if compiler:
        run(compiler, f'/DAppVersion={args.version}', 'packaging/windows.iss')
        artifacts.append(output / f'Xiaoya-{args.version}-windows-x64-setup.exe')
    else:
        print('ISCC not supplied: ZIP only. Pass --iscc to also build setup.exe.')
    checksum = output / 'SHA256SUMS.txt'
    lines = []
    for path in artifacts:
        with path.open('rb') as file:
            lines.append(f'{hashlib.file_digest(file, "sha256").hexdigest()}  {path.name}\n')
    checksum.write_text(''.join(lines), encoding='utf-8')
    for path in artifacts + [checksum]:
        print(f'{path} ({path.stat().st_size / 1024**2:.1f} MiB)')


if __name__ == '__main__':
    main()
