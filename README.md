# OptView2 - User-oriented fork of LLVM's opt-viewer

Video Introduction: https://www.twitch.tv/videos/1267918755 - including example applications.

In the beginning there was the compiler switch [`-Rpass`](https://clang.llvm.org/docs/UsersManual.html#options-to-emit-optimization-reports), and it was good. Sorta. Clang users who wanted visibility into compiler optimization decisions could dump a wall of text and sift through it trying to make up what's important and what's actionable.
Then, Adam Nemet et. al. added a compiler switch (`clang -fsave-optimization-record`) and the [opt-viewer python script](https://github.com/llvm/llvm-project/tree/main/llvm/tools/opt-viewer), as part of LLVM. He [presented it at the 2016 LLVM Developers’ Meeting](https://www.youtube.com/watch?v=qq0q1hfzidg), and lo it was good. Now users could generate and inspect HTMLs of their C/C++ sources, annotated with "optimization-remarks" in place. 

Alas, these tools were explicitly designed for use by compiler writers wishing to investigate and imporve optimization code, with only a mention of future adaptation for usage by developers wishing to understand and improve their application's optimization.

Hence the birth of OptView2. We aim to make this wonderful optimization data accessible and _actionable_ by developers.

## Main changes
1) Ignore system headers,
2) Collect only optimization _failures_, 
3) Display in index.html only a single entry per type/source loc,
4) Replace ‘pass’ with ‘optimization name’,
5) Make the index table sortable & resizable (Thanks [Ilan Ben-Hagai](https://github.com/supox))
6) Use abridged func names

## Project management
I don't see any potential compatibility considerations now or in the future, and these are essentially only 5 python scripts and some html+javascript - so at this point there won't be any versioning or releases structure.  

Just download and use - and please report any problems you come across.

## Usage examples
First, build your C/C++ project with Clang + `-fsave-optimization-record`. Note that by default this generates YAMLs alongside the obj files. Then -

### Basic usage:
```
./optview2/opt-viewer.py --output-dir <HTMLs destination> --source-dir <source location> <YAMLs location>
```
Note that `source-dir` needs to be the original root of the build with `-fsave-optimization-record`, even if you're interested only in part of the tree. Express this filter through the <YAML location>. 
### Parallelize to 10 jobs:
```
./optview2/opt-viewer.py -j10 --output-dir <...> --source-dir <...> <YAML dir>
```

### Split top level folders:
When working on large projects optview2's memory consumption easily gets out of hand. As a quick workaround, you can separate the work to build-subfolders (only first-level subfolders are supported).  For example:
```
./optview2/opt-viewer.py --split-top-level --output-dir <...> --source-dir <...> <YAMLs dir>
```
If, for example, the build dir includes subfolders "core", "utils" and "plugins" - the script would process them separately, and create 3 identically named subfolders under output-dir (with separate index files).
If this doesn't work for you - you can also filter out comment types via remarks-filter.
### Example
A dummy project with an optimization issue exists at `cpp_optimization_example`. To compile, generate HTML files and open browser, use the wrapper script:
```
./optview2/cpp_optimization_example/run_optview2.sh
```
