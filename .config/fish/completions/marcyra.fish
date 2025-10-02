set -l seen '__fish_seen_subcommand_from'
set -l has_opt '__fish_contains_opt'

set -l commands shell toggle scheme screenshot record clipboard emoji-picker wallpaper resizer
set -l not_seen "not $seen $commands"



# Disable file completions
complete -c marcyra -f

# Add help for any command
complete -c marcyra -s 'h' -l 'help' -d 'Show help'

# Subcommands
complete -c marcyra -n $not_seen -a 'wallpaper' -d 'Manage the wallpapers'

# Wallpaper
complete -c marcyra -n "$seen wallpaper" -s 'p' -l 'print' -d 'Print the scheme for a wallpaper' -rF
# Base dir resolver: $XDG_PICTURES_DIR/Wallpapers or ~/Pictures/Wallpapers
function __marcyra_wall_base --description 'Default wallpapers base'
    if set -q XDG_PICTURES_DIR
        echo "$XDG_PICTURES_DIR/Wallpapers"
    else
        echo "$HOME/Pictures/Wallpapers"
    end
end

# Detect if user is typing an explicit path (/, ~, ., or contains '/')
function __marcyra_token_is_path
    set -l tok (commandline --current-token)
    test -n "$tok"; or return 1
    string match -rq '^(~|/|\.)' -- "$tok"; and return 0
    string match -q '*/*' -- "$tok"; and return 0
    return 1
end

# List image files under the base (shallow scan); adjust extensions as needed
function __marcyra_list_wall_files --description 'List wallpaper files in default base'
    set -l base (__marcyra_wall_base)
    test -d "$base"; or return 0
    # Find common image types one per line
    find "$base" -maxdepth 2 -type f \( \
        -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.tif' -o -iname '*.tiff' \
    \) -print 2>/dev/null
end

# List directories under the base (for -r/--random directory arg)
function __marcyra_list_wall_dirs --description 'List directories in default base'
    set -l base (__marcyra_wall_base)
    test -d "$base"; or return 0
    # Include the base itself as a candidate
    printf '%s\n' "$base"
    # And some immediate subdirectories
    find "$base" -mindepth 1 -maxdepth 2 -type d -print 2>/dev/null
end

# -----------------------
# Completions for marcyra
# -----------------------

# Dynamic output names (kept from earlier)
complete -c marcyra -n "$seen wallpaper" -s o -l output -r \
  -a '(hyprctl -j monitors | jq -r ".[].name")' \
  -d 'The output monitor'

# -f/--file: suggest files from default base unless user started a path
complete -c marcyra -n "$seen wallpaper; and not __marcyra_token_is_path" \
  -s f -l file -r -a '(__marcyra_list_wall_files)' -d 'The file to switch to'

# -f/--file fallback: normal path completion once a path is started
complete -c marcyra -n "$seen wallpaper; and __marcyra_token_is_path" \
  -s f -l file -rF -d 'The file to switch to'

# -r/--random: suggest directories from default base unless user started a path
complete -c marcyra -n "$seen wallpaper; and not __marcyra_token_is_path" \
  -s r -l random -r -a '(__marcyra_list_wall_dirs)' -d 'Switch to a random wallpaper'

# -r/--random fallback: normal path completion once a path is started
complete -c marcyra -n "$seen wallpaper; and __marcyra_token_is_path" \
  -s r -l random -rF -d 'Switch to a random wallpaper'
function __marcyra_list_outputs --description 'List Hyprland outputs'
    hyprctl -j monitors | jq -r '.[].name'
end

# Produce “name<TAB>description” for each active output
function __marcyra_list_outputs_tsv --description 'Hyprland outputs with descriptions'
    hyprctl -j monitors | jq -r '
        .[] | [
            .name,
            (.description // ((.make // "") + " " + (.model // "")) // .name)
        ] | @tsv
    '
end

# -o/--output: insert name, display description
complete -c marcyra -n "$seen wallpaper" -s o -l output \
  -a '(__marcyra_list_outputs_tsv)' \
  -d 'The output monitor'

