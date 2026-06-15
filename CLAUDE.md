# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

HeartsofOpenIron aims to become an open-source Paradox Entertainment-like grand strategy map game set in the World War II era, implemented as a Godot 4 GDExtension project written in C++ with `godot-cpp` bindings. The extension library is named `EXTENSION-NAME` in the build files and is copied into the Godot project under `project/bin/<platform>/`.

The repository is currently a small GDExtension template rather than a full game implementation:
- `src/register_types.cpp` is the GDExtension entry point and registers native classes.
- `src/example_class.*` is the sample native `RefCounted` class exposed to GDScript.
- `project/example.gd` demonstrates loading and calling the native class.
- `doc/CONOPS.md` contains the current game scope/context notes for the broader project.

The `godot-cpp` dependency is a Git submodule. If build files cannot find `godot-cpp/src`, initialize it first:

```sh
git submodule update --init --recursive
```

## Common commands

### SCons build

SCons is the primary build path used by GitHub Actions.

```sh
scons target=template_debug platform=windows arch=x86_64 precision=double
```

Useful variants:

```sh
scons target=template_debug platform=linux arch=x86_64 precision=double
scons target=template_release platform=windows arch=x86_64 precision=single
```

To use the example build profile, pass it explicitly:

```sh
scons build_profile=build_profile.json target=template_debug platform=windows arch=x86_64 precision=double
```

### CMake build

CMake is also supported and automatically initializes the `godot-cpp` submodule if its source is missing.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

The CMake target is a shared library named from `LIBNAME` in `CMakeLists.txt`; the post-build step copies it into `project/bin/<platform>/`.

### Formatting

The repository has `.clang-format` configured for LLVM-style C++ formatting with tabs and a zero column limit. The CI workflow currently has the following formatting check commented out, but this is the intended command shape:

```sh
python -m pip install clang-format
clang-format src/*.h src/*.cpp --dry-run --Werror
```

To apply formatting in place:

```sh
clang-format -i src/*.h src/*.cpp
```

### Tests

There are no automated unit tests in the repository at the time this file was created. CI only builds selected GDExtension target/platform/precision combinations.

### CI

GitHub Actions are under `.github/workflows/`:

- `.github/workflows/ci.yml` builds a selected matrix of platforms and targets. Its push/pull-request triggers are currently commented out; it runs manually via `workflow_dispatch`.
- `.github/workflows/make_build.yml` manually builds and uploads artifacts for the full supported platform matrix.

## Architecture notes

### Build system

`SConstruct` is the main build script. It:
1. Requires an initialized `godot-cpp` directory.
2. Invokes `godot-cpp/SConstruct` to get the Godot C++ build environment.
3. Compiles all `src/*.cpp` files.
4. Adds generated documentation data for debug/editor targets when supported.
5. Produces the extension shared library in `bin/<platform>/`.
6. Installs/copies the library into `project/bin/<platform>/`.

`CMakeLists.txt` mirrors this with CMake and `GodotCPPModule`. It sets C++17, links `godot::cpp`, and uses `RUNTIME_OUTPUT_DIRECTORY` so the built extension lands in the Godot project's bin directory.

### Native extension registration

GDExtension initialization happens in `src/register_types.cpp`:
- `example_library_init` creates a `GDExtensionBinding::InitObject`.
- It registers `initialize_gdextension_types` and `uninitialize_gdextension_types`.
- `initialize_gdextension_types` runs at `MODULE_INITIALIZATION_LEVEL_SCENE` and registers classes with `GDREGISTER_CLASS`.

When adding a native class, register it in `initialize_gdextension_types` and ensure its source is included by the build system.

### Godot project

The Godot project is in `project/`, with `project/project.godot` targeting Godot 4.1 and Forward Plus. `project/example.gd` is a smoke-test scene script that instantiates `ExampleClass` and calls `print_type`.
