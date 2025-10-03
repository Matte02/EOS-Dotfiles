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
complete -c marcyra -n $not_seen -a 'shell' -d 'Start the shell or message it'
#############
### SHELL ###
#############

set -l commands mpris drawers wallpaper notifs
set -l not_seen "$seen shell && not $seen $commands"

complete -c marcyra -n $not_seen -s 'd' -l 'daemon' -d 'Start the shell detached'
complete -c marcyra -n $not_seen -s 'k' -l 'kill' -d 'Kill the shell'

##################
### Wallpapers ###
##################



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



# marcyra scheme completions

# -------------
# Helper loaders
# -------------
function __marcyra_scheme_names --description 'List scheme names'
    marcyra scheme list --names 2>/dev/null
end

function __marcyra_scheme_flavours --description 'List scheme flavours'
    marcyra scheme list --flavours 2>/dev/null
end

function __marcyra_scheme_modes --description 'List scheme modes'
    # Parser only allows dark/light, so keep static for speed
    printf '%s\n' dark light
end

function __marcyra_scheme_variants --description 'List scheme variants'
    marcyra scheme list --variants 2>/dev/null
end

# -----------------
# Subcommand parent
# -----------------
# Offer "scheme" when no subcommand has been chosen yet
complete -c marcyra -n 'not __fish_seen_subcommand_from scheme' \
  -a scheme -d 'manage the colour scheme'

# Inside "scheme", offer its subcommands when none picked
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and not __fish_seen_subcommand_from list get set' \
  -a 'list get set' -d 'list/get/set scheme data'

# ----
# list
# ----
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from list' \
  -s n -l names -d 'list scheme names'

complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from list' \
  -s f -l flavours -d 'list scheme flavours'

complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from list' \
  -s m -l modes -d 'list scheme modes'

complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from list' \
  -s v -l variants -d 'list scheme variants'

# ---
# get
# ---
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from get' \
  -s n -l name -d 'print the current scheme name'

complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from get' \
  -s f -l flavour -d 'print the current scheme flavour'

complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from get' \
  -s m -l mode -d 'print the current scheme mode'

complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from get' \
  -s v -l variant -d 'print the current scheme variant'


# Flags without arguments (unchanged)
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from set' \
  -l notify -d 'send a notification on error'
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from set' \
  -s r -l random -d 'switch to a random scheme'

# Arguments with required values and no file completion
# Use -x as shorthand for: --require-parameter (-r) + --no-files (-f)
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from set' \
  -s n -l name -x -a '(__marcyra_scheme_names)' -d 'the scheme name to switch to'
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from set' \
  -s f -l flavour -x -a '(__marcyra_scheme_flavours)' -d 'the flavour to switch to'
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from set' \
  -s m -l mode -x -a '(__marcyra_scheme_modes)' -d 'the mode to switch to'
complete -c marcyra -n '__fish_seen_subcommand_from scheme; and __fish_seen_subcommand_from set' \
  -s v -l variant -x -a '(__marcyra_scheme_variants)' -d 'the variant to switch to'
