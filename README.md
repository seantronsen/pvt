# pvt -- Python Visualization & Algorithm Tuning

A small collection of real-time data viewing utilities, initially created to
satisfy the goal of enabling algorithmic tuning with rapid feedback.

With this viewer, your code is the bottleneck to the rendering pipeline rather
than the renderer itself (looking at you JupyterLab \w `matplotlib`). In other
words, this will render as quickly as your code can spit out the data.

## Early Development Notice

Understand this project is in the early stages of development and while it
remains quite functional, frequent changes should be expected when tracking the
`main` branch. For this reason, the developer(s) recommend tracking one of the
release tags for a more stable experience.

## Installation

1. Review the requirements and suggestions below.
2. Open a shell and create / activate a fresh python virtual environment.
3. Clone or submodule this repository.
4. Navigate to the repository directory.
5. Run `make install-dev` to install this package into the virtual environment,
   enabling use in any project.
6. Mess around with the demo: `python demo.py`.
7. Mess around with `pyqtgraph`'s demos: `python -c "import pvt; pvt.run_pyqtgraph_examples()"`

## Visualization Workflow

1. Create an application instance (e.g. `VisionViewer`) as a QtApplication
   instance must exist before instantiating any widgets.

2. Create all control widgets. Provide all instances with a key which will
   later be used to reference a unique element in the application state.
   Interacting with the widget will cause any subscribing display panes to be
   updated. Note that subscription occurs automatically when data and control
   panes are added to the viewer instance.

3. Create all display panes (e.g. `ImagePane`), passing each a callback
   function to generate new frames for display. To make use of the application
   state, the arguments of the callback must share the same names as the key
   values provided to the control widgets created in step 2. Note the order of
   defined arguments doesn't matter nor do all possible arguments need to be
   specified if the function declares a `**kwargs` parameter. If there is no
   need to update the display, specify a default callback which performs no
   processing and merely returns the data to be displayed. Detailed examples
   are provided in the `demo.py` file.

4. Add all panes to the viewer instance and execute the `run` method.

## A Note about the Callback Interface

Instances of the `StatefulPane` class intuitively hold references to a `State`
object. For the sake of brevity, understand that an indirect chain of callback
functions is used to communicate changes to the underlying state to the pane
interface. Those who are more curious are welcome to review the implementation
details in the source code.

## Requirements

- [anaconda3/miniconda3](https://docs.anaconda.com/free/miniconda/index.html)
- [GNU Make](https://www.gnu.org/software/make/)

**Linux Users**

Should work out of the box without any issues.

**MacOS Users**

- A Qt installation: MacOS uses cocoa and metal by default (jeers and boos allowed).

```bash

brew install qt

```

**Windows Users**

Provided this is a Python project, it should be possible to run all of this on
Windows with minimal changes. It's likely a similar issue to the missing Qt
installation will be presented on this operating system. Open an issue if you
run into any trouble or submit a pull request if you rectify the issue on your
own and want to share the solution with others.

## Help & Suggestions

- **Review**: Read through the `pyproject.toml` file to see the package
  requirements for this project. It's imperative the packages in existing
  projects are compatible.

- **Qt Incompatibilities**: Depending on packages already within your Python
  virtual environment, you may run into compatibility issues related to
  ambiguous references to multiple Qt library versions. To verify the problem,
  following the debugging steps outlined in this section. Likely culprits are
  any other packages that come bundled with Qt by default like `matplotlib` and
  `opencv-contrib-python`. The former rarely presents a problem, but OpenCV's
  python packages often are the culprit. To resolve the issue, uninstall all
  things OpenCV in the virtual environment and reinstall the **headless**
  versions (e.g. `pip install opencv-contrib-python-headless`).

- **`pyopengl-accelerate` compilation failure**: Although this is a helpful
  package which increases the performance of the OpenGL implementation for
  Python, there is no hard requirement for it to be installed. If you're
  working with a version that either has diverged from the main branch or an
  older version of the codebase, remove the requirement from the
  `pyproject.toml` file and the installation should proceed without any further
  errors.

- **Issues and Debugging**: Begin your debugging process by installing this
  package into a fresh `conda` environment enabled with `python==3.9` as this
  is the version used for development. From here, test out the implementations
  provided in `demo.py`. If the demos run appropriate with this set up, an
  incompatibility exists in your target environment. Based on past experience,
  this typically occurs from an ambiguous reference to multiple Qt libraries.

- **GitHub Issues**: If all else fails, don't hesitate to browse through
  current and past GitHub issues to see if anyone else has found the same
  problem (and potentially a solution). If there's nothing useful to be found,
  don't hesitate to open a new issue and so we work though the problem
  together.

## Acknowledgements

This project was made possible by the efforts of the
[PyQtGraph](https://www.pyqtgraph.org/) team. If you enjoy any feature of this
package, be sure to check out theirs for specifics and more advanced use cases.
