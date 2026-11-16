#!/usr/bin/env bash
set -e

APP=Handify
rm -rf build dist AppDir

# 1) Binário com PyInstaller (onedir)
pyinstaller --noconfirm --clean --windowed --onedir --name $APP \
  --add-data "handify_1024.png:." \
  --collect-all mediapipe --collect-all PySide6 --collect-all cv2 \
  main.py

# 2) Estrutura do AppDir
mkdir -p AppDir/usr/bin
cp -r dist/$APP/* AppDir/usr/bin/

python3 -c "
from PIL import Image
im = Image.open('handify_1024.png').resize((512, 512), Image.LANCZOS)
im.save('AppDir/handify.png', format='PNG')
im.save('AppDir/.DirIcon', format='PNG')
"

# 4) Arquivo .desktop
cat > AppDir/handify.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Handify
Comment=Gestos personalizados
Exec=Handify
Icon=handify
Categories=Utility;
Terminal=false
EOF

# 5) AppRun
cat > AppDir/AppRun <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/Handify" "$@"
EOF
chmod +x AppDir/AppRun

# 6) Empacotar
if [ ! -f appimagetool-x86_64.AppImage ]; then
  wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x appimagetool-x86_64.AppImage
fi

ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir Handify-x86_64.AppImage
