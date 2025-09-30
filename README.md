# Linux Arch Dotfiles (EndeavourOS)

# STOW Guide
Guide: https://www.youtube.com/watch?v=y6XCebnB9gs

1. Install git and stow `sudo pacman -S git stow`
1. Git clone this repo `git clone https://github.com/Matte02/EOS-Dotfiles.git` into `~` i.e `home/username/`
1. Move into the directory with `cd`
1. `stow .`
    1. If there are conflicts, either remove/backup conflicting files
    1. OR, `stow . --adopt`, and discard changes