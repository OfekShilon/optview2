This is an example showing the capabilities of `opt-viewer`.
For gathering the relevant information from the optimizer, you first need to build the
project in Release mode and with a special clang compiler argument set:
```bash
$ cmake -E env CXX=clang++ CXXFLAGS=-fsave-optimization-record cmake -B build -DCMAKE_BUILD_TYPE=Release
$ cmake --build build
```
This should produce a `main.cc.opt.yaml` file somewhere inside of the `build` directory.
`opt-viewer` can then be used to view this data:
```bash
$  python ../opt-viewer.py --open-browser --output-dir html_output build
```