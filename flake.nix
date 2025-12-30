{
  description = "retype dev shell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux"; # change if you’re not on x86_64
    pkgs = import nixpkgs {inherit system;};
    py = pkgs.python311;
    pyPkgs = pkgs.python311Packages;
    qt = pkgs.libsForQt5;
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = [
        (py.withPackages (ps:
          with ps; [
            pip

            pyqt5
            ebooklib
            tinycss2

            pyinstaller
            setuptools
          ]))

        # Qt runtime tools sometimes needed by PyQt apps
        qt.qt5.qtbase
        qt.qt5.qttools
        qt.qt5.qtsvg
        qt.qt5.qtdeclarative # needed for QML path
      ];

      shellHook = ''
        # Real Qt paths from Nix store (no qtpaths/qmake metadata involved)
        export QT_PLUGIN_PATH="$(ls -d ${qt.qt5.qtbase}/lib/qt-*/plugins | head -n1)"

        export QML2_IMPORT_PATH="$(
          find ${qt.qt5.qtdeclarative} ${qt.qt5.qtdeclarative.bin} \
            -type d -path "*/lib/qt-*/qml" 2>/dev/null | head -n1
        )"

        export QT_QPA_PLATFORM_PLUGIN_PATH="$QT_PLUGIN_PATH/platforms"

        # Tell PyInstaller explicitly
        export PYINSTALLER_QT5_PLUGIN_PATH="$QT_PLUGIN_PATH"
        export PYINSTALLER_QT5_QML_PATH="$QML2_IMPORT_PATH"

        echo "QT_PLUGIN_PATH=$QT_PLUGIN_PATH"
        echo "QML2_IMPORT_PATH=$QML2_IMPORT_PATH"

        # pyqt stubs for pyright
        rm -rf .pyqt5-stubs-dir typings
        pip install --target=.pyqt5-stubs-dir PyQt5-stubs
        mkdir -p typings/PyQt5
        cp -r .pyqt5-stubs-dir/PyQt5-stubs/* typings/PyQt5/
        touch typings/PyQt5/py.typed

        echo "Python: $(python --version)"
        echo "PyQt5 available: $(python -c 'import PyQt5; print(PyQt5.__file__)')"
      '';
    };
  };
}
