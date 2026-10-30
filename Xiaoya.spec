# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pet.py'],
    pathex=[],
    binaries=[],
    # Ship runtime artwork only, never local previews or abandoned rig drafts.
    datas=[('assets/' + name, 'assets') for name in
           ('open.png', 'blink.png', 'q-open.png', 'natural-open.png')]
          + [('assets/whole-run/' + style + '/' + name, 'assets/whole-run/' + style)
             for style in ('q', 'natural')
             for name in ['frames.json'] + [f'{i:02}.png' for i in range(1, 9)]],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.binaries = [entry for entry in a.binaries if entry[0].lower() not in ('icuuc.dll', 'icudt78.dll')]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Xiaoya',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Xiaoya',
)
