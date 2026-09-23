{
  description = "javli — Minecraft Command-Line Launcher";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in {
      packages = forAllSystems (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          default = pkgs.python3Packages.buildPythonApplication {
            pname = "javli";
            version = "1.0.0";
            format = "pyproject";
            src = ./.;
            nativeBuildInputs = with pkgs.python3Packages; [ setuptools wheel ];
            propagatedBuildInputs = with pkgs.python3Packages; [ requests ];
          };
        });
      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/javli";
        };
      });
    };
}
