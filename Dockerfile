# Fixed and Derived from https://github.com/sytone/obsidian-remote and https://gist.github.com/ondrik/95850021e9046483df91c46d9a23ad2b

FROM ghcr.io/linuxserver/baseimage-rdesktop-web:focal-1.2.0-ls101

RUN \
    echo "**** install packages ****" && \
    # Update and install extra packages.
    apt-get update && \
    apt-get install -y --force-yes --no-install-recommends \
    # Packages needed to download and extract obsidian.
        curl \
        libnss3 \
        aptitude \
        xz-utils zstd xdg-utils libxcb-xinerama0 libxkbcommon-x11-0\
        software-properties-common \
        # Install Chrome dependencies.
        dbus-x11 \
        uuid-runtime \
        locales locales-all \ 
        dbus-x11 x11-xkb-utils rename

# Credits: https://wiki.debian.org/Locale
# RUN apt-get install -y aptitude
# RUN add-apt-repository "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) main universe restricted multiverse"
# RUN aptitude install -y locales locales-all
# RUN aptitude install -y libzstd1
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && locale-gen

# fonts-vlgothic is for Japanese fonts. Depending on what you study with
# Anki, you might want to install other packages.
# RUN aptitude install -y fonts-vlgothic
# RUN aptitude install -y fonts-arphic-uming fonts-wqy-zenhei
# RUN aptitude install -y fcitx fcitx-chewing
# RUN aptitude install -y dbus-x11 x11-xkb-utils
# RUN aptitude install -y anki

# Might only work if your host user and group IDs are both 1000.

RUN \
    echo "**** install runtime packages ****" && \
    apt-get update && \
    apt-get install -y \
    logrotate \
    nano \
    netcat-openbsd sshpass \
    sudo && \
    echo "**** install openssh-server ****" && \
    apt-get install -y \
    openssh-client \
    openssh-server && \
    ## openssh-sftp-server && \
    echo "**** setup openssh environment ****" && \
    ## sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config && \
    usermod --shell /bin/bash abc && \
    rm -rf \
    /tmp/*

RUN apt-get install -y '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev libxcb-xinerama0 libxcb-image0 libxcb-icccm4 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 gnome-screenshot

RUN echo "**** download anki ****" && curl https://github.com/ankitects/anki/releases/download/2.1.60/anki-2.1.60-linux-qt6.tar.zst -L -o anki.tar.zst
RUN chmod +x ./anki.tar.zst && \
    mkdir anki && \
    mkdir /usr/share/desktop-directories && \
    tar --use-compress-program=unzstd -xvf ./anki.tar.zst -C ./anki/ && \ 
    cd anki/anki-2.1.60-linux-qt6/ && \ 
    chmod +x ./install.sh && \
    ./install.sh

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8 

RUN update-locale LANG=en_US.UTF-8
ENV QT_DEBUG_PLUGINS 1
# ENV XMODIFIERS @im=fcitx
# ENV XMODIFIERS @im=ibus
# CMD /bin/bash -c "(/usr/bin/ibus-daemon -xd; /usr/bin/anki;)"
# CMD /bin/bash -c "/usr/bin/fcitx-autostart ; /usr/bin/anki"
# CMD /bin/bash -c "/usr/bin/anki"
# CMD /bin/bash -c "anki"

# # set version label
ARG OBSIDIAN_VERSION=1.5.3

RUN \
    echo "**** download obsidian ****" && \
    curl \
    https://github.com/obsidianmd/obsidian-releases/releases/download/v$OBSIDIAN_VERSION/Obsidian-$OBSIDIAN_VERSION.AppImage \
    -L \
    -o ./obsidian.AppImage

RUN \
    echo "**** extract obsidian ****" && \
    chmod +x ./obsidian.AppImage && \
    ./obsidian.AppImage --appimage-extract

ENV \
    CUSTOM_PORT="8080" \
    GUIAUTOSTART="true" \
    HOME="/vaults" \
    TITLE="Obsidian v$OBSIDIAN_VERSION"

RUN echo "**** cleanup ****" && \
    apt-get autoclean && \
    rm -rf \
    /var/lib/apt/lists/* \
    /var/tmp/* \
    /tmp/*


# add local files
COPY root/ /

EXPOSE 8080
EXPOSE 8888

VOLUME ["/config","/vaults"]