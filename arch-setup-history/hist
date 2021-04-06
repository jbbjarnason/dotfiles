$ systemctl start iwd
$ iwctl # connect to wifi
$ timedatectl set-ntp true
$ timedatectl status
$ fdisk -l # lookup the drives and partitions
# Note: this does not show how to reorganize partitions in terminal, 
# I used gparted before I began this installation.
$ mount /dev/nvme0n1p3 /mnt
$ mkdir /mnt/boot
$ mount /dev/nvme0n1p1 /mnt/boot
$ swapon /dev/nvme0n1p2
$ pacstrap /mnt base linux linux-firmware # TODO just install all my wanted packages
$ genfstab -U /mnt >> /mnt/etc/fstab # Set partitions unique ids to fstab
$ cat /mnt/etc/fstab # check if everything is in order


$ arch-chroot /mnt

$ ln -sf /usr/share/zoneinfo/Iceland /etc/localtime
$ hwclock --systohc
$ vim /etc/locale.gen
# Uncomment en_US.UTF-8 UTF-8 AND/OR is_IS ISO-8859-1
$ locale-gen
$ vim /etc/locale.conf
LANG=en_US.UTF-8

$ pacman -S vim
$ vim /etc/hostname # add your desired hostname ex. jonb-vinna
$ vim /etc/hosts
127.0.0.1	localhost
::1		localhost
127.0.1.1	jonb-vinna.local	jonb-vinna
$ mkinitcpio -P
$ passwd # set root password
$ bootctl install # USE systemd-boot as bootloader, https://wiki.archlinux.org/index.php/Systemd-boot
$ pacman -S intel-ucode # if you have intel processor
$ vim /boot/loader/entries/arch.conf
title	Arch Linux
linux	/vmlinuz-linux
initrd	/intel-ucode.img
initrd	/initramfs-linux.img
options	root="LABEL=root" rw  # NOTE: the label can be seen in fstab

$ vim /boot/loader/entries/arch-fallback.conf
title   Arch Linux (fallback initramfs)
linux   /vmlinuz-linux
initrd  /intel-ucode.img
initrd  /initramfs-linux-fallback.img
options root="LABEL=root" rw

$ useradd -m jonb
$ passwd jonb
password ...
$ visudo
# add jonb with same privileges as root
$ pacman -S base-devel git
$ su jonb
$ cd /opt
$ git clone https://aur.archlinux.org/yay.git # yay is a package manager for AUR
$ cd yay
$ makepkg -si

$ yay -S mkinitcpio-numlock
$ sudo vim /etc/mkinitcpio.conf
# Add to HOOK=(base ... keyboard numlock fsck)
# if encryption is used numlock needs to be before that hook

$ yay -S systemd-boot-pacman-hook # automates the boot update process, basicly runs bootctl update :)

$ sudo pacman -S xorg

$ sudo pacman -S nvidia nvidia-settings # refer to https://wiki.archlinux.org/index.php/NVIDIA if in doubt

$ sudo pacman -S plasma plasma-wayland-session
$ sudo pacman -S kde-applications
$ sudo pacman -S sddm
$ sudo systemctl enable sddm.service
$ sudo pacman -S xdg-user-dirs
$ xdg-user-dirs-update

$ sudo pacman -S thermald # for intel cpus
$ sudo systemctl enable thermald.service
# TODO cpu frequency scaling https://wiki.archlinux.org/index.php/CPU_frequency_scaling

$ sudo pacman -S ufw
$ sudo systemctl enable ufw.service

$ sudo pacman -S print-manager cups system-config-printer
$ sudo systemctl enable cups.service

$ sudo systemctl enable NetworkManager

$ sudo pacman -S bash-completion

$ yay -S brave-bin
$ yay -S optimus-manager optimus-manager-qt

# start system

$ 
