# gesture_control.spec
import sys
import os
import mediapipe as mp
import cv2

mediapipe_path = os.path.dirname(mp.__file__)
cv2_path = os.path.dirname(cv2.__file__)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (mediapipe_path, 'mediapipe'),
        (cv2_path, 'cv2'),
    ],
    hiddenimports=[
        'mediapipe',
        'mediapipe.python.solutions.hands',
        'mediapipe.python.solutions.drawing_utils',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFilter',
        'screen_brightness_control',
        'numpy',
        'pycaw',
        'comtypes',
        'comtypes.client',
        'pystray',
        'pystray._darwin',
        'pystray._win32',
        'pystray._xorg',
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

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='GestureControl.app',
        icon=None,
        bundle_identifier='com.gesturecontrol.app',
        info_plist={
    'NSCameraUsageDescription': 'Gesture Control necesita acceso a la cámara para detectar gestos de mano.',
    'NSHighResolutionCapable': True,
    'LSMinimumSystemVersion': '11.0',
    'LSUIElement': True,  # ← permite tray sin dock icon
    'NSPrincipalClass': 'NSApplication',
    'NSAppleScriptEnabled': False,
        },
    )
