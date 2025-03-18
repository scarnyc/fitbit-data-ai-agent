
{ pkgs }: {
  deps = [
    pkgs.python39
    pkgs.playwright-driver
    pkgs.chromium
    pkgs.firefox
    pkgs.xorg.libX11
    pkgs.xorg.libXcomposite
    pkgs.xorg.libXdamage
    pkgs.xorg.libXext
    pkgs.xorg.libXfixes
    pkgs.xorg.libXrandr
    pkgs.at-spi2-core
    pkgs.at-spi2-atk
    pkgs.dbus
    pkgs.expat
    pkgs.nspr
    pkgs.nss
    pkgs.cups
    pkgs.libdrm
    pkgs.mesa
    pkgs.pango
    pkgs.cairo
    pkgs.alsa-lib
    pkgs.atk
    pkgs.gtk3
    pkgs.libuuid
    pkgs.libxkbcommon
    pkgs.libxcb
    pkgs.xorg.xauth
  ];
}
