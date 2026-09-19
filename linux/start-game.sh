#!/bin/sh
cd ..

read -p "Login Token: " token

export LOGIN_TOKEN=$token

python3 -m toontown.launcher.QuickStartLauncher
