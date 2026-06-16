# gesture_control.spec
# PyInstaller spec file — usado por GitHub Actions para los 3 sistemas operativos.
import sys
import os
from pathlib import Path
import mediapipe as mp

mediapipe_path = os.path.dirname(mp.__file__)

block_cipher = None
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (mediapipe_path, 'mediapipe'),
    ],
    hiddenimports=[
        'mediapipe',
        'mediapipe.python.solutions.hands',
        'mediapipe.python.solutions.drawing_utils',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'screen_brightness_control',
        'numpy',
        # Windows
        'pycaw',
        'comtypes',
        'comtypes.client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GestureControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GestureControl',
)
# macOS: genera un .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='GestureControl.app',
        icon=None,
        bundle_identifier='com.gesturecontrol.app',
        info_plist={
            'NSCameraUsageDescription': 'Gesture Control necesita acceso a la cámara para detectar gestos de mano.',
            'NSHighResolutionCapable': True,
        },
    )
