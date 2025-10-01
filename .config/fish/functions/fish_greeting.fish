function fish_greeting
    echo -ne '\x1b[38;5;16m'  # Set colour to primary
echo "  __  __                                ";
echo " |  \/  |                               ";
echo " | \  / | __ _ _ __ ___ _   _ _ __ __ _ ";
echo " | |\/| |/ _` | '__/ __| | | | '__/ _` |";
echo " | |  | | (_| | | | (__| |_| | | | (_| |";
echo " |_|  |_|\__,_|_|  \___|\__, |_|  \__,_|";
echo "                         __/ |          ";
echo "                        |___/           ";
set_color normal
fastfetch --key-padding-left 0
end

