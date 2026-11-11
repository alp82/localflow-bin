FROM archlinux:base
RUN pacman -Syu --noconfirm --needed base-devel namcap desktop-file-utils python git \
    && useradd -m builder \
    && printf 'builder ALL=(ALL) NOPASSWD: /usr/bin/pacman\n' > /etc/sudoers.d/builder
COPY container-check.sh /usr/local/bin/container-check
ENTRYPOINT ["bash", "/usr/local/bin/container-check"]
