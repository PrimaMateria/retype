# -*- mode: python ; coding: utf-8 -*-
import os

from setup.config import data, binaries, imports, builddate

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs
from PyInstaller.building.datastruct import Tree


def _force_str(x):
    """If x is nested tuple/list, take first element; then stringify."""
    if isinstance(x, (list, tuple)):
        x = x[0] if len(x) > 0 else ""
    return str(x)


def normalize_datas(items):
    """
    PyInstaller wants datas items as:
      - (src, dest) where BOTH are strings
      - or TOC objects like Tree(...)
    Project helpers sometimes return crazy shapes:
      - (src, dest, type)
      - [src, dest, type]
      - ( (src, ...), (dest, ...) )
    We coerce hard into (str(src), str(dest)).
    """
    out = []
    for x in items:
        # Leave TOC objects (Tree, etc.) alone
        if not isinstance(x, (list, tuple)):
            out.append(x)
            continue

        # flatten one level if needed
        if len(x) == 1 and isinstance(x[0], (list, tuple)):
            x = x[0]

        if len(x) >= 2:
            src = _force_str(x[0])
            dest = _force_str(x[1])
            out.append((src, dest))
        else:
            out.append(tuple(_force_str(i) for i in x))

    return out


# Initial datas from helper, normalize immediately
datas = normalize_datas(builddate.saveDateToFile(os.path.abspath(".")))

# --- MANUAL PyQt5 + Qt bundling for Nix/WSL ---
hidden = imports.addn + collect_submodules("PyQt5")
extra_bins = collect_dynamic_libs("PyQt5")

import PyQt5
pyqt5_pkg = PyQt5.__path__[0]
datas += [Tree(pyqt5_pkg, prefix="PyQt5")]

qt_plugins = os.environ.get("QT_PLUGIN_PATH")
if qt_plugins:
    datas += [Tree(qt_plugins, prefix="PyQt5/Qt5/plugins")]

qt_qml = os.environ.get("QML2_IMPORT_PATH")
if qt_qml:
    datas += [Tree(qt_qml, prefix="PyQt5/Qt5/qml")]
# --- end manual bundling ---

# Normalize again after all additions
datas = normalize_datas(datas)

# Drop bogus datas entries whose source file doesn't exist.
# Safe because PyQt5 is already bundled via Tree(pyqt5_pkg, ...)
_filtered = []
for d in datas:
    if isinstance(d, tuple) and len(d) == 2:
        src, dest = d
        if os.path.exists(src):
            _filtered.append(d)
        else:
            print("Skipping missing data file:", src)
    else:
        _filtered.append(d)  # keep Tree(...)
datas = _filtered


a = Analysis(
    ['../retype-target.py'],  # noqa: F821
    pathex=[],
    binaries=extra_bins,
    datas=datas,
    hiddenimports=hidden,
    hookspath=['./setup/pyinstaller-hooks'],  # keep hook override
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

a.binaries = binaries.filterBinaries(a.binaries)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)  # noqa: F821

exe = EXE(
    pyz,  # noqa: F821
    a.scripts,
    [],
    exclude_binaries=True,
    name=data.name,
    icon=data.icon,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,  # noqa: F821
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=data.name,
)
