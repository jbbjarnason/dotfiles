sudo pacman -S --needed base-devel devtools git
git clone https://aur.archlinux.org/decman.git
cd decman
makepkg -i

cd ..
git clone https://github.com/jbbjarnason/dotfiles
cp -r dotfiles/decman ~/

sudo decman --source ~/decman/source.py
sudo decman
