# Builds and releases

GitHub Actions builds javli after every pushed commit and can also be run manually.

Targets: Windows x64/x86, Linux x64/x86, macOS Intel/Apple Silicon.

Each successful workflow uploads Actions artifacts and creates a GitHub Release tagged with the workflow build number and short commit SHA containing all six packaged binaries.
