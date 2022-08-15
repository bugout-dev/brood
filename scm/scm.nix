with builtins;
let
    scm_repos = [
        (getEnv "SCM_GIT")
        (fetchGit {
            url = "git@gitlab.com:deltaex/schematic.git";
            rev = "ba5d7b40255e5da9a74e666dd88e309dae40fbd2";
        })
    ];
    scm_repo = head (filter (x: x != "") scm_repos);
    scm = (import scm_repo {
        verbose = true;
        repos = [
            "."
            (getEnv "MDP_GIT")
            (fetchGit {
                url = "git@github.com:bugout-dev/brood.git";
                rev = "19d8581965d035cee9918bbb1e6b333a39422c2a";
            })
        ] ++ scm_repos;
    });
in rec {
    schematic = scm.shell.overrideAttrs ( oldAttrs : {
        shellHook = oldAttrs.shellHook + ''
            [ -n "$ENV" -a "$ENV" != "dev" ]
            source /home/moonstream/brood-secrets/pg.env
        '';
    });
}
