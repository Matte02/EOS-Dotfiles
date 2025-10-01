set -l seen '__fish_seen_subcommand_from'
set -l has_opt '__fish_contains_opt'

set -l commands shell toggle scheme screenshot record clipboard emoji-picker wallpaper resizer
set -l not_seen "not $seen $commands"


# Disable file completions
complete -c marcyra -f

# Add help for any command
complete -c marcyra -s 'h' -l 'help' -d 'Show help'