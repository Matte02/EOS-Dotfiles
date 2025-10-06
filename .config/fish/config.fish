if status is-interactive
    fish_add_path -m ~/.local/bin
    # Commands to run in interactive sessions can go here


    # Starship custom prompt
    starship init fish | source


    command -v zoxide &> /dev/null && zoxide init fish --cmd cd | source


    # Better ls
    alias ls='eza --icons --group-directories-first -1'

    # Custom colours
    cat ~/.local/state/marcyra/sequences.txt 2> /dev/null

    # For jumping between prompts in foot terminal
    function mark_prompt_start --on-event fish_prompt
        echo -en "\e]133;A\e\\"
    end
end
