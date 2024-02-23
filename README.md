# qtviewer

A small collection of image viewing utilities created to simplify algorithmic
tuning efforts by utilizing technologies which allow for a fast render cycle
when changes are detected.

## Installation

1. Review the requirements and suggestions below.
2. Open a shell and create / activate your virtual python environment.
3. Clone or submodule this repository.
4. Navigate to the project directory.
5. Run `make install-dev`
6. Mess around with the demo: `python demo.py`.
7. Mess around with `pyqtgraph`'s demos: `python -c "import qtviewer; qtviewer.run_pyqtgraph_examples()"`

## Visualization Workflow

1. Create an application instance (e.g. `VisionViewer`) as QtApplication must
   exist before instantiating any widgets. Obscure errors may result if this
   requirement is not abided by.

2. Create all modification / control widgets for a pane. Provide all such instances with
   both a key and initial value for their corresponding state assignment. Each
   widget should be responsible for a unique state element. Conceptually, these
   are just key value pairs in a python dictionary. Interacting with the widget
   and altering it's local state results in changes being bubbled up to the parent
   pane state.

3. Create all data display panes (e.g. `ImagePane`). Each child class of
   StatefulPane requires that a callback function be passed to the instance
   constructor. Remember those keys from the key-value pairs in step 02? The
   parameters of the callback function need to have the same names as those keys.
   Order doesn't matter and extras are ignored if a `**kwargs` parameter is
   defined on the callback function. An example is provided below.

4. Attach all widgets to their corresponding panes.

5. Execute the `run` method for the application instance.

## A Note on the QT Viewer Callback Interface

Instances of the `StatefulPane` class intuitively hold references to a `State`
object. For the sake of brevity, understand that an indirect chain of callback
functions is used to communicate changes to the underlying state to the pane
interface. Those who are more curious are welcome to review the implementation
details in the source code.

## Requirements

- [anaconda3/miniconda3](https://docs.anaconda.com/free/miniconda/index.html)
- [GNU Make](https://www.gnu.org/software/make/)

**MacOS Users**

- A Qt installation: MacOS uses cocoa by default (jeers and boos allowed).

```bash

brew install qt

```

**Windows Users**
Provided this is a python project, it should be possible to run all of this on
Windows with minimal changes. It's likely a similar issue to the missing Qt
installation will be presented on this operating system. Open an issue if you
run into any trouble or submit a pull request if you rectify the issue on your
own and want to share the solution with others.

## Suggestions

Review the `pyproject.toml` file to see the package requirements for this
project. It's imperative the packages in existing projects are compatible.

Additionally, bast on past experience with similar libraries and OpenCV,
certain virtual environments will find a Qt package conflict issue which is
typically the result of the Qt library packaged with matplotlib. If you find
yourself in this situation, open an issue on the repository page and we can
work through it together.
