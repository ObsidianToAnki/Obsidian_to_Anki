
echo "Starting Obsisidan .... " >> /config/logs/obsidian.log

# permissions
echo "abc" | sudo -S chown -R abc:abc /vaults

/squashfs-root/obsidian --no-sandbox --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer --remote-debugging-port=8890 --window-position=400,10 

echo "Obsisidan Ended .... " >> /config/logs/obsidian.log

# ss_dir = 
for file in /vaults/**/*.md; do test_name=$(basename $file); done
test_name=$(echo $test_name | awk -F [.] '{print $1}')

echo "Executing PostTest ss" >> /config/logs/gnome.log && gnome-screenshot >> /config/logs/gnome.log && rename "s/Screenshot from .*/Anki PostTest_${test_name}.png/" /config/*.png
rename "s/Anki PreTest.*/Anki PreTest_${test_name}.png/" /config/*.png

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

sleep 2s # permissions denied since, anki would be still tearning down and locking sqlite db

test_name_anki="${test_name}_Anki"

# echo "abc" | sudo chown -R abc:abc /config

echo "abc" | sudo -S mv /config/.local/share/Anki2 "/config/.local/share/$test_name_anki"
echo "abc" | sudo -S mkdir -p /config/.local/share/Anki2
echo "abc" | sudo -S cp -Raf /config/.local/share/Anki2default/* /config/.local/share/Anki2

# sleep 3s 
# Let wdio complete its post test checks or other checks with obsidian files
while [ ! -f /vaults/unlock ]
do
    sleep 0.1
done

echo "abc" | sudo -S mkdir -p "/config/.local/share/$test_name_anki/Obsidian/"
echo "abc" | sudo -S mv -f "/vaults/$test_name" "/config/.local/share/$test_name_anki/Obsidian/$test_name"
echo "abc" | sudo -S rm -rf /vaults/*

echo "abc" | sudo chown -R abc:abc /config

sleep 5s # Let wdio copy test_vault_suite

/defaults/autostart