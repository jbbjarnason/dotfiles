# ~/decman/source.py
# Arch declarative setup with Decman, transposed from your NixOS config.
# Requires: decman (AUR), base-devel, devtools (for AUR builds).
#
# Run: sudo decman --source ~/decman/source.py
# Later: sudo decman

import os, shutil, time
import subprocess
import decman
from decman import File, Directory, Module, prg

# -------------------------
# Core packages (pacman)
# -------------------------
decman.packages += [
    # Base quality-of-life & dev
    "vim","wget","cmake","gcc","ninja","automake","autoconf","autoconf-archive","libtool","pkgconf","make","htop",
    "rustup","musl","clang","mold","graphviz","rustfmt","pavucontrol","git","procps-ng","vcpkg",
    "direnv","unzip","socat","lsof","usbutils","android-tools","gnome-terminal","ntfs-3g","nodejs",
    "jq","yarn","inkscape","lld","jdk-openjdk","qemu-desktop","parted","debootstrap","ethtool","tcpdump","lldb",

    # Wayland / Sway desktop
    "sway","swaylock","mako","waybar","grim","slurp","wf-recorder","wl-clipboard","network-manager-applet","blueman",
    "wofi","wdisplays","alacritty","zenity",

    # Apps
    "remmina","discord","signal-desktop","vlc","kicad","d-spy","iperf3","libreoffice-fresh","hunspell","hunspell-en_us",

    # Networking & services
    "networkmanager","iwd","openssh","ufw","zerotier-one","openfortivpn",

    # Virtualization
    "docker","virt-manager","libvirt","qemu-img","dnsmasq","bridge-utils","edk2-ovmf","usbredir","spice-gtk",

    # Bluetooth & Thunderbolt
    "bluez","bluez-utils","bolt",

    # Fonts
    "noto-fonts","noto-fonts-cjk","noto-fonts-emoji","ttf-font-awesome",
    "adobe-source-han-sans-otc-fonts","adobe-source-han-serif-otc-fonts",

    # Wireshark CLI (Qt GUI optional: wireshark-qt)
    "wireshark-cli",

    # Firmware & microcode
    "linux","linux-headers","linux-firmware","intel-ucode",

    # Sway extras (optional)
    # "swayidle",
]

# -------------------------
# AUR packages
# -------------------------
decman.aur_packages += [
    "bambu-studio",
    # Bitwarden desktop often lives in AUR; if official repo has it for you, remove this line.
    "bitwarden",
    "google-chrome",
    "spotify",
    "teamviewer",
    "realvnc-vnc-viewer",
    "clion",
    "jetbrains-toolbox",
    "vcpkg",       # present in AUR on many mirrors
    "ltunify",
    "eww-wayland",
    # Decman (manage itself):
    "decman",
]

# Keep your AUR helper un-managed if you use one
decman.ignored_packages += ["yay","paru","visual-studio-code-bin","code-cursor"]

# -------------------------
# Hostname, locale, timezone
# -------------------------
decman.files["/etc/hostname"] = File(content="jonb-work-laptop\n")
decman.files["/etc/locale.conf"] = File(content="LANG=en_US.UTF-8\n")
# We'll uncomment en_US.UTF-8 in /etc/locale.gen during on_enable
# Timezone will be set with timedatectl during on_enable

# -------------------------
# NetworkManager (iwd backend + disable wifi powersave)
# -------------------------
decman.files["/etc/NetworkManager/conf.d/wifi_backend.conf"] = File(
    content="[device]\nwifi.backend=iwd\n"
)
decman.files["/etc/NetworkManager/conf.d/wifi_powersave.conf"] = File(
    content="[connection]\nwifi.powersave = 2\n"  # 2 = disable powersave
)

# /etc/hosts helper – append line idempotently via module (safer than replacing whole file)
EXTRA_HOSTS_LINE = "10.11.13.4 tempservo.local"

# -------------------------
# tmpfiles & D-Bus policy
# -------------------------
decman.files["/etc/tmpfiles.d/tfc.conf"] = File(
    content="d /var/run/tfc 0755 jonb users - -\n"
)
decman.files["/etc/dbus-1/system.d/is.centroid.conf"] = File(content="""\
<!DOCTYPE busconfig PUBLIC
"-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
"http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <policy context="default">
    <allow own_prefix="is.centroid"/>
    <allow send_destination_prefix="is.centroid"/>
  </policy>
</busconfig>
""")

# -------------------------
# Systemd units to enable (system-wide)
# -------------------------
decman.enabled_systemd_units += [
    # Networking
    "NetworkManager.service",
    "iwd.service",
    "sshd.service",

    # Audio stack is user units (see module), nothing to enable here

    # Bluetooth / Bolt
    "bluetooth.service",
    "boltd.service",

    # Virtualization
    "libvirtd.service",
    "docker.service",

    # ZeroTier
    "zerotier-one.service",

    # Firewall
    "ufw.service",

    # TeamViewer daemon
    "teamviewerd.service",
]

# -------------------------
# Modules
# -------------------------
class SystemTuning(Module):
    """Locale, timezone, groups, /etc/hosts, fish shell."""
    def __init__(self):
        super().__init__(name="system", enabled=True, version="1")

    def on_enable(self):
        # Locale
        prg(["sed","-i","s/^#\\s*en_US.UTF-8/en_US.UTF-8/","/etc/locale.gen"])
        prg(["locale-gen"])

        # Timezone
        prg(["timedatectl","set-timezone","Atlantic/Reykjavik"])

        # Ensure /etc/hosts includes your extra mapping
        self.ensure_hosts_line(EXTRA_HOSTS_LINE)

        # Add jonb to groups similar to NixOS config
        prg(["usermod","-aG","wheel,network,lp,docker,dialout,wireshark,libvirt","jonb"])

        # Default shell = fish
        fish = "/usr/bin/fish"
        if os.path.exists(fish):
            prg(["chsh","-s",fish,"jonb"])

        # UFW rules (match your open ports)
        # TCP: 22, 5900, 1040, 5201 ; UDP: 9993 (zerotier), 51820 (wireguard future)
        prg(["ufw","default","deny"])
        for p in ["22","5900","1040","5201"]:
            prg(["ufw","allow",p])
        for p in ["9993/udp","51820/udp"]:
            prg(["ufw","allow",p])
        prg(["ufw","--force","enable"])

    def ensure_hosts_line(self, line: str):
        try:
            with open("/etc/hosts","r+",encoding="utf-8") as f:
                content = f.read()
                if line not in content:
                    f.write(("\n" if not content.endswith("\n") else "") + line + "\n")
        except FileNotFoundError:
            with open("/etc/hosts","w",encoding="utf-8") as f:
                f.write("127.0.0.1 localhost\n::1 localhost\n" + line + "\n")

class AudioPipeWire(Module):
    """Enable user pipewire services for jonb."""
    def __init__(self):
        super().__init__(name="audio", enabled=True, version="1")

    def on_enable(self):
        # Enable user units for jonb
        self.enable_user_units("jonb", [
            "pipewire.service",
            "pipewire-pulse.service",
            "wireplumber.service",
            # GNOME Keyring user service socket (for secrets/SSH agent)
            "gnome-keyring-daemon.socket",
        ])

    def enable_user_units(self, user, units):
        for u in units:
            prg(["runuser","-l",user,"-c",f"systemctl --user enable --now {u}"])

class PolkitAgentSway(Module):
    """Start a polkit agent under the user session (sway)."""
    def __init__(self):
        super().__init__(name="polkit-agent", enabled=True, version="1")

    def on_enable(self):
        unit_path = f"/home/jonb/.config/systemd/user/polkit-gnome-agent.service"
        os.makedirs(os.path.dirname(unit_path), exist_ok=True)
        with open(unit_path,"w",encoding="utf-8") as f:
            f.write("""\
[Unit]
Description=Polkit GNOME authentication agent
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1
Restart=on-failure

[Install]
WantedBy=default.target
""")
        prg(["chown","jonb:jonb",unit_path])
        prg(["runuser","-l","jonb","-c","systemctl --user daemon-reload"])
        prg(["runuser","-l","jonb","-c","systemctl --user enable --now polkit-gnome-agent.service"])

class ZerotierJoin(Module):
    """Optional: auto-join networks on first enable (edit NETWORK_IDS)."""
    NETWORK_IDS = []  # e.g. ["8056c2e21c000001"]

    def __init__(self):
        super().__init__(name="zerotier", enabled=True, version="1")

    def on_enable(self):
        for nid in self.NETWORK_IDS:
            prg(["zerotier-cli","join",nid])

class EFISTUB(Module):
    """
    Create an EFISTUB boot entry with efibootmgr.
    Edit DISK/PART/ROOT_UUID appropriately.
    """
    # --- EDIT THESE THREE VALUES FOR YOUR MACHINE ---
    DISK = "/dev/nvme0n1"     # The disk containing the ESP
    PART = "1"                 # The ESP partition number
    ROOT_UUID = "96686dae-0f82-408b-a3dd-9409502addd2"  # Your root FS UUID (ext4 from Nix config)
    # ------------------------------------------------

    LABEL = "Arch (EFISTUB)"
    # Kernel params: swap in your own extras as needed
    KERNEL_PARAMS = [
        f"root=UUID={ROOT_UUID}",
        "rw",
        "quiet",
        "loglevel=3",
        # From your Nix config:
        "kvm.enable_virt_at_load=0",
    ]

    def __init__(self):
        super().__init__(name="efistub", enabled=True, version="1")

    def on_enable(self):
        # We assume ESP is mounted at /boot (recommended for EFISTUB + pacman updates)
        # Add ucode + initramfs paths using backslashes per EFI standard.
        # Reference: ArchWiki "EFI boot stub".
        params = " ".join(self.KERNEL_PARAMS + [
            r"initrd=\intel-ucode.img",
            r"initrd=\initramfs-linux.img",
        ])
        prg([
            "efibootmgr","--create",
            "--disk", self.DISK, "--part", self.PART,
            "--label", self.LABEL,
            "--loader", "/vmlinuz-linux",
            "--unicode", params
        ])

        # Optional hook to re-create entry after kernel updates:
        hook = "/etc/pacman.d/hooks/90-efistub.hook"
        os.makedirs(os.path.dirname(hook), exist_ok=True)
        with open(hook,"w",encoding="utf-8") as f:
            f.write(f"""\
[Trigger]
Type = Path
Operation = Install
Operation = Upgrade
Target = /boot/vmlinuz-linux
Target = /boot/initramfs-linux.img
Target = /boot/intel-ucode.img

[Action]
Description = Refresh EFISTUB NVRAM entry
When = PostTransaction
Exec = /usr/bin/efibootmgr --create --disk {self.DISK} --part {self.PART} --label "{self.LABEL}" --loader /vmlinuz-linux --unicode "{' '.join(self.KERNEL_PARAMS)} initrd=\\intel-ucode.img initrd=\\initramfs-linux.img"
""")
        prg(["chmod","0644",hook])


class Dotfiles(Module):
    """
    Symlink (or copy) files from ./dotfiles into jonb's home.
    Put your files under a directory named 'dotfiles' next to source.py.
    """
    OWNER = "jonb"
    GROUP = "jonb"
    BASE  = os.path.join(os.path.dirname(__file__), "dotfiles")

    # Choose behavior: "link" (symlink) or "copy"
    MODE = "link"

    # Map: relative_path_in_dotfiles -> destination_path (use ~)
    MAP = {
        "sway/config":                "~/.config/sway/config",
        "waybar/config":              "~/.config/waybar/config",
        "fish/config.fish":           "~/.config/fish/config.fish",
        "alacritty/alacritty.toml":   "~/.config/alacritty/alacritty.toml",
        "git/.gitconfig":             "~/.gitconfig",
        # add more here...
    }

    # Optional file mode overrides for sensitive files (only used when MODE="copy")
    MODES = {
        "~/.gitconfig": 0o644,
        "~/.ssh/config": 0o600,   # example if you add it
    }

    def __init__(self):
        super().__init__(name="dotfiles", enabled=True, version="1")

    def on_enable(self):
        for rel_src, dest in self.MAP.items():
            src = os.path.join(self.BASE, rel_src)
            dst = os.path.expanduser(dest)
            self._install(src, dst)

    # ---------------- internal helpers ----------------

    def _install(self, src, dst):
        if not os.path.exists(src):
            raise FileNotFoundError(f"Dotfile missing: {src}")

        os.makedirs(os.path.dirname(dst), exist_ok=True)

        if self.MODE == "link":
            self._ensure_symlink(src, dst)
        else:
            self._ensure_copy(src, dst)

        # Make sure ownership is correct
        prg(["chown", f"{self.OWNER}:{self.GROUP}", dst], check=False)

    def _ensure_symlink(self, src, dst):
        if os.path.islink(dst):
            # if it points somewhere else, replace it
            if os.readlink(dst) != src:
                os.remove(dst)
                os.symlink(src, dst)
        elif os.path.exists(dst):
            self._backup(dst)
            os.remove(dst)
            os.symlink(src, dst)
        else:
            os.symlink(src, dst)

    def _ensure_copy(self, src, dst):
        if os.path.isdir(src):
            # copytree with merge semantics
            if os.path.exists(dst) and not os.path.isdir(dst):
                self._backup(dst)
                os.remove(dst)
            if not os.path.exists(dst):
                shutil.copytree(src, dst)
            else:
                # merge copy
                for root, _, files in os.walk(src):
                    rel = os.path.relpath(root, src)
                    ddir = os.path.join(dst, rel) if rel != "." else dst
                    os.makedirs(ddir, exist_ok=True)
                    for f in files:
                        s = os.path.join(root, f)
                        d = os.path.join(ddir, f)
                        if os.path.exists(d) and not os.path.islink(d):
                            self._backup(d)
                        shutil.copy2(s, d)
        else:
            if os.path.exists(dst) and not os.path.islink(dst):
                # only back up if contents differ
                with open(src, "rb") as a, open(dst, "rb") as b:
                    if a.read() != b.read():
                        self._backup(dst)
            shutil.copy2(src, dst)

        # mode overrides
        mode = self.MODES.get(self._tilde_collapse(dst))
        if mode is not None:
            os.chmod(dst, mode)

    def _backup(self, path):
        ts = time.strftime("%Y%m%d-%H%M%S")
        bak = f"{path}.bak-{ts}"
        shutil.move(path, bak)

    def _tilde_collapse(self, path):
        home = os.path.expanduser("~")
        return path.replace(home, "~", 1) if path.startswith(home) else path

# Register modules
decman.modules += [
    SystemTuning(),
    AudioPipeWire(),
    PolkitAgentSway(),
    ZerotierJoin(),
    EFISTUB(),
    Dotfiles(),
]

