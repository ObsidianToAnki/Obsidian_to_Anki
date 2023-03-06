
echo "Starting Obsisidan .... " >> /config/logs/obsidian.log

/squashfs-root/obsidian --no-sandbox --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer --remote-debugging-port=8890 --window-position=400,10 

echo "Obsisidan Ended .... " >> /config/logs/obsidian.log

(sleep 2s && echo "Executing PostTest ss" >> /config/logs/gnome.log && gnome-screenshot >> /config/logs/gnome.log && rename 's/Screenshot from .*/Anki PostTest.png/' /config/*.png) &

# ls -alh >> /config/logs/gnome.log
# ls -alh /config/ >> /config/logs/gnome.log
# ls -alh "/config/.local/share/Anki2/User 1/" >> /config/logs/gnome.log


# echo "abc" | sudo -S chown -R 1000:1000 \
#     /config \
#     /vaults \
#     /squashfs-root

# echo "abc" | sudo -S chmod 775 -R 1000:1000 \
#     /config \
#     /vaults \
#     /squashfs-root

# ls -alh >> /config/logs/gnome.log
# ls -alh /config/ >> /config/logs/gnome.log
# ls -alh "/config/.local/share/Anki2/User 1/" >> /config/logs/gnome.log

sleep 2s

pkill anki
