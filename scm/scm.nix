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
                rev = "1de7440ed3d4dc00f125be390e6b64ebe5e242e6";
            })
        ] ++ scm_repos;
    });
in rec {
    schematic = scm.shell.overrideAttrs ( oldAttrs : {
        shellHook = oldAttrs.shellHook + ''
            [ -n "$ENV" -a "$ENV" != "dev" ] && export BUGSNAG=2b987ca13cd93a4931bb746aace204fb
        '';
    });
}