# ~/.profile: executed by the command interpreter for login shells.
# This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# exists.
# see /usr/share/doc/bash/examples/startup-files for examples.
# the files are located in the bash-doc package.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
    fi
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
export PATH="/home/mayum/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib:/mnt/c/WINDOWS/system32:/mnt/c/WINDOWS:/mnt/c/WINDOWS/System32/Wbem:/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/:/mnt/c/WINDOWS/System32/OpenSSH/:/mnt/c/Program Files/nodejs/:/mnt/c/Program Files/Git/cmd:/mnt/c/Users/mayum/AppData/Roaming/Python/Python313/Scripts:/mnt/c/Program Files/Docker/Docker/resources/bin:/mnt/c/Users/mayum/scoop/shims:/mnt/c/Ruby34-x64/bin:/mnt/c/Users/mayum/AppData/Local/Programs/Python/Python313/Scripts/:/mnt/c/Users/mayum/AppData/Local/Programs/Python/Python313/:/mnt/c/Users/mayum/AppData/Local/Programs/Python/Launcher/:/mnt/c/Users/mayum/AppData/Local/Microsoft/WindowsApps:/mnt/c/Users/mayum/AppData/Local/Programs/cursor/resources/app/bin:/mnt/c/Users/mayum/AppData/Local/Programs/Python/Python313/Scripts:/mnt/c/Users/mayum/AppData/Roaming/npm:/mnt/c/Users/mayum/AppData/Local/Programs/Microsoft VS Code/bin:/mnt/c/Users/mayum/AppData/Local/Programs/Windsurf/bin:/mnt/c/Users/mayum/ffmpeg-7.1.1-essentials_build/bin:/mnt/c/src/flutter/bin:/mnt/c/Ruby34-x64/bin:/mnt/c/Users/mayum/AppData/Local/Programs/Ollama:/mnt/c/Users/mayum/AppData/Roaming/Code/User/globalStorage/github.copilot-chat/debugCommand"
