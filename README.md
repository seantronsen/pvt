# pvt – Python Data Visualizer & Algorithm Tuner

`pvt` is a lightweight collection of real-time data visualization tools built
for rapid algorithm tuning. Its design ensures that user-defined
computations—not the rendering backend—limit the achievable framerate.

## Early Development

This project is in early development, so frequent changes are expected on the
`main` branch. For a more stable experience, use a tagged release.

## Requirements

See the `pyproject.toml` file for the current listing of required packages and
version information.

### Platform Notes

- **Linux:** Works out of the box on major distributions.
- **macOS:** Ensure a Qt installation is available. If your Python Qt bindings
  lack the required libraries, install libqt6 with:
  ```bash
  brew install qt6
  ```
- **Windows:** Not directly supported. With minor modifications (typically
  around Qt installation), it should work. Please report any issues or
  contribute fixes.

## Installation

1. Clone the repository.
2. Inside the local repository directory, run `make install-dev` to install pvt.
3. Test the installation using the demos: `python demo.py`.

## Visualization Workflow

1. **Initialize:** Create an `App` instance (a QtApplication instance must be
   created before instantiating any widgets per the laws of `Qt`).
2. **Define Callbacks:** Write a function that computes your display data.
   Parameterize it to allow interactivity. If displaying results from mutliple
   functions, include a `**kwargs` parameter in each definition.
3. **Add Controls:** Create control widgets (e.g., sliders, toggles) with unique
   keys that map to callback parameters. These controls update subscribed
   display panes through the `VisualizerContext`.
4. **Create Displays:** Set up data displays (e.g., `ImagePane`) that call your
   callbacks upon widget interaction.
5. **Start the App:** Add all widgets to the `App` and execute its `run` method.

See `demo.py` for detailed examples.

## Help & Suggestions

- **Compatibility:** Review `pyproject.toml` for package requirements and ensure
  compatibility with your environment.
- **Qt Issues:** If you encounter Qt conflicts (often due to packages like
  `opencv-contrib-python`), uninstall the conflicting packages and reinstall
  their headless versions (e.g. `opencv-contrib-python-headless`).
- **Debugging:** Try a fresh conda environment using the provided
  `environment.yml` and test with `demo.py`. For simplicity, you can use the
  Makefile recipe we use internally for convenience by executing
  `make environment`. If the demo runs correctly, the issue likely lies in your
  target environment.
- **Support:** Consult the repository issues for similar problems or open a new
  issue if needed.

## Acknowledgements

This project was made possible by the efforts of the
[PyQtGraph](https://www.pyqtgraph.org/) team. If you enjoy any feature of this
package, be sure to check out theirs for specifics and more advanced use cases.
