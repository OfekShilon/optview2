# OptView2 - User-oriented fork of LLVM's opt-viewer

## Video Introduction 
https://www.youtube.com/watch?v=nVc439dnMTk

The slides (with links) are avaiable at https://www.slideshare.net/ofekshilon/optview2-muc-meetup-slides .

This is still the best way to start, as the talk includes example script outputs and recommendations on handling them. The text below still surveys only background and technical usage.

## Text Introduction

In the beginning there was the compiler switch [`-Rpass`](https://clang.llvm.org/docs/UsersManual.html#options-to-emit-optimization-reports), and it was good. Sorta. Clang users who wanted visibility into compiler optimization decisions could dump a wall of text and sift through it trying to make up what's important and what's actionable.
Then, Adam Nemet et. al. added a compiler switch (`clang -fsave-optimization-record`) and the [opt-viewer python script](https://github.com/llvm/llvm-project/tree/main/llvm/tools/opt-viewer), as part of LLVM. He [presented it at the 2016 LLVM Developers’ Meeting](https://www.youtube.com/watch?v=qq0q1hfzidg), and lo it was good. Now users could generate and inspect HTMLs of their C/C++ sources, annotated with "optimization-remarks" in place. 

Alas, these tools were explicitly designed for use by compiler writers wishing to investigate and imporve optimization code, with only a mention of future adaptation for usage by developers wishing to understand and improve their application's optimization.

Hence the birth of OptView2. We aim to make this wonderful optimization data accessible and _actionable_ by developers.

### Main changes w.r.t. the LLVM origin
1) Ignore system headers,
2) Collect only optimization _failures_, 
3) Display in index.html only a single entry per type/source loc,
4) Replace ‘pass’ with ‘optimization name’,
5) Make the index table sortable & resizable (Thanks [Ilan Ben-Hagai](https://github.com/supox))
6) Use abridged func names.
7) Create option to split processing into subfolders ('--split-top-folders') to enable processing of large projects
8) Trim repeated remarks in source - keep only 5 per line.
9) Enable filtering by remark name/text, preferrably via config file (but possible via command line too). Check `config.yaml` for some examples.


### Versioning
I can't see any future potential compatibility considerations, and these are essentially just 5 python scripts and some html+javascript - so at this point there won't be any versioning or releases structure. Just download/clone and use - and please report any problems you come across.

### Performance
It is not uncommon for an analysis of a ~1000 file project to take an hour or more. Two things can help mitigate the burden:
 1) The `-j[N]` command line switch to opt-viewer.py controls the number of jobs to spawn for YAML processing. A rule of thumb that worked best for my PC was to set `N` to 1.5 times the number of physical cores (for an 8 core machine, set tot 12), but there's no real alternative to experimentation.
 2) The script uses the python package PyYaml - which uses the C++ package libyaml if available, and if not - falls back to a much, much slower python implementation. In such a case you'd see this line in the script output:
> For faster parsing, you may want to install libyaml for PyYAL

  One way to install and use libyaml is:
  ```
  $ sudo apt install libyaml-dev
  $ pip --no-cache-dir install --verbose --force-reinstall -I pyyaml
  ```

### Usage examples
First, build your C/C++ project with Clang + `-fsave-optimization-record`. Note that by default this generates YAMLs alongside the obj files. Then -

#### Basic usage
```
./optview2/opt-viewer.py --output-dir <HTMLs destination> --source-dir <source location> <YAMLs location>
```
Note that `<source-dir>` needs to be the original root of the build which included `-fsave-optimization-record`, even if you're interested only in part of the tree. Express this filter through the `<YAML location>` argument. 
#### Parallelize to 10 jobs:
```
./optview2/opt-viewer.py -j10 --output-dir <...> --source-dir <...> <YAML dir>
```

#### Split top level folders:
When working on large projects optview2's memory consumption easily gets out of hand. As a quick workaround, you can separate the work to build-subfolders (only first-level subfolders are supported).  For example:
```
./optview2/opt-viewer.py --split-top-folders --output-dir <...> --source-dir <...> <YAMLs dir>
```
If, for example, the build dir includes subfolders "core", "utils" and "plugins" - the script would process them separately, and create 3 identically named subfolders under output-dir (with separate index files).
If this doesn't work for you - you can also filter out comment types via remarks-filter.
#### Sample projects
A dummy project with a few optimization issues is placed under `cpp_optimization_example`. To compile, generate HTML files and open in browser, use the wrapper script:
```
./optview2/cpp_optimization_example/run_optview2.sh
```
Note to WSL users: you'd [probably need to manually open the resulting HTML](https://github.com/OfekShilon/optview2/issues/11).

Two real life projects were analyzed and the results pushed online - check [CPython](https://ofekshilon.github.io/optview2-cpython/) and [OpenCV](https://ofekshilon.github.io/optview2-opencv/) pages.