# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=copy_metadata('pymupdf') + copy_metadata('pypdf'),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PreviewCleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
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
    name='PreviewCleaner',
)
app = BUNDLE(
    coll,
    name='PreviewCleaner.app',
    icon=None,
    bundle_identifier='local.previewcleaner.app',
    version='0.1.0',
    info_plist={
        'CFBundleDisplayName': 'Preview Cleaner',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '26.0',
        'NSHighResolutionCapable': True,
    },
)
