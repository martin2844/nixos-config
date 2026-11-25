{ pkgs ? import ../../nix/pkgs.nix { } }:

pkgs.trayscale.overrideAttrs (old: {
  patches = (old.patches or [ ]) ++ [ ./peer-presence.patch ];
  postPatch = (old.postPatch or "") + ''
    cp ${./presence.go} internal/tsutil/presence.go
    cp ${./presence_test.go} internal/tsutil/presence_test.go
  '';
  doCheck = true;
  checkPhase = ''
    runHook preCheck
    go test ./internal/tsutil
    runHook postCheck
  '';
})
