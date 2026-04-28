# CHANGELOG.md

## XPCIpy GUI – Change Log
This document summarizes all approved updates, fixes, and improvements implemented in the Reconstruction (TLRec) and Simulation (PCSim) GUI modules.

## [v. 1.3.0] – PCSim Physics Engine Improvements

### PCSim – Insert Mode for CT-like Phantoms
- **New `is_insert` flag** on `GeometricObject` subclasses: setting `obj.is_insert = True` marks an object as an insert that physically replaces the base material instead of adding on top of it.
- **New function `_group_transmission_with_insert_replace()`** in `experiments.py`: when a group of objects at the same DSO plane contains inserts, the function replaces the base material contribution in the overlap region pixel-by-pixel, producing a physically correct CT-like phantom transmission.
  - Validates that exactly one base object exists per group; falls back to `_group_transmission_default` otherwise.
  - 5 unit tests added covering: no inserts, single insert, multiple inserts, fallback with no base, fallback with multiple bases.
- **README updated** with a new section "Insert Mode For CT-like Phantoms" explaining the physics, constraints, and a code example.

### PCSim – Source PSF Robustness
- **Sub-pixel PSF guard**: `Source.Source_PSF()` now detects when the effective Gaussian sigma is smaller than 0.5 pixels (sub-pixel regime) and returns a delta function instead of computing a numerically unstable Gaussian. Prevents homogeneous output images caused by near-zero PSF convolutions.

### PCSim – Object Positioning API: Physical Units
- **`x_shift` / `y_shift` now in µm** (physical units) across all `GeometricObject` subclasses (`Sphere`, `Wedge`, `Cylinder`, `Grating`, `DoubleSlit`, `KnifeEdge`, `Disk`). Previously these parameters were in pixels, which was non-intuitive and pixel-size dependent.
  - Each `make_geometry()` converts internally via `round(shift_µm / pixel_size)` so the physical position is always consistent regardless of pixel size.
  - **Migration**: multiply old pixel values by `pixel_size` to get the equivalent µm value.

### PCSim – Bug Fix: Object Shift Formula
- **Corrected grid shift formula** in all `make_geometry()` methods. The old formula `(-n ± shift_px)//2 : (n ± shift_px)//2` applied the shift at half the intended magnitude and with inverted sign. The new formula `-n//2 + shift_px : n//2 + shift_px` produces the correct 1:1 physical displacement in the expected direction.

### Simple Numerical Simulation – Random Talbot-Lau Dataset Workflow
- **Expanded geometric flexibility** in `src/Simple_Numerical_Simulation/Objects.py`:
  - Added support for center/rotation handling in core shapes used in synthetic scenes.
  - Added a richer geometry set and compositing utilities for layered synthetic phantoms.
- **New random scene generator**: introduced `RandomSimGenerator` to create random multi-object scenes with configurable object count, random positioning/orientation, material sampling, and optional insert regions.
- **Insert-aware composition (PCSim-inspired)**: added local replacement behavior for inserts when building synthetic objects, so insert regions can replace base material contribution in overlap areas.
- **Material/optics outputs for supervision**:
  - Added map accessors in `MultiMaterialComposite` (`thickness`, `phase`, `attenuation`, and **transmission**).
  - Added transmission computation via `get_transmission_map()` to support attenuation-vs-transmission training targets.
- **Physics-consistent optical scaling**: random generation path now supports physical `delta`/`beta` input with energy-based internal conversion through `energy_keV`.
- **High-level simulation helper**: added `simulate_random_tl_sample(...)` in `src/Simple_Numerical_Simulation/simulation.py` to produce, in one call:
  - synthetic scene maps (phase, gradient/DPC, laplacian, attenuation, transmission, thickness),
  - object/reference Talbot-Lau phase-stepping stacks.

### Notebook Workflow – Dataset + Reconstruction Integration
- **Notebook relocation**: moved simulation workflow notebook to `Notebooks/Notebook_Simulation.ipynb`.
- **Import portability update**: notebook import cells now append the project root dynamically so modules under `src/` resolve correctly when launched from `Notebooks/`.
- **Dataset guide added**: included an English quick guide section for random TL dataset generation and parameter usage.
- **TIFF export path integrated**: notebook saves object/reference stacks for reconstruction experiments.
- **TLRec bridge added**: new notebook cell runs `Modulation_Curve_Reconstruction` directly from generated stacks and exports DPC/Transmission/Dark-field/Phase reconstructions.

---

## [v. 1.2.0] – Quality-of-Life & Bug Fixes Round

### Keyboard Shortcuts & Documentation
- **Global keyboard shortcuts** added to main PCSim GUI:
  - `Enter` / `Ctrl+Enter` — Run simulation on active tab
  - `Ctrl+S` — Save result
  - `Ctrl+Shift+S` — Save preset (Inline or Talbot-Lau)
  - `F1` — Open Help window
  - `Ctrl+Q` — Exit application
- **Splash screen improvement**: Loading screen now skippable via click or key press for faster startup during development.
- **Documentation**: Added `docs/source/shortcuts.rst` with full keyboard shortcut reference (Sphinx documentation).
- **Help UI**: New "Shortcuts" tab added to Help window displaying all available shortcuts organized by context.

### PCSim – Critical Bug Fixes
- **Fixed AttributeError in Check Talbot-Lau tab**: Corrected incorrect variable name `self.c_grating_option` -> `self.c_grating_def` in `verify_physical_values_checkTL()` method (was causing crash every time Run button was pressed).
- **Fixed silent data corruption in Inline preset**: Removed spurious `"Period_G1"` field (Talbot-Lau variable) being saved in Inline Simulation preset dictionary.

### PCSim – Usability Improvements
- **Auto-update Talbot Distance (Check TL tab)**: Added real-time recalculation of Talbot distance field when user modifies X-ray energy, grating period, or grating definition. Previously required manual click to refresh; now uses `trace_add` callbacks on input fields.

### TLRec – Reconstruction GUI Enhancements
- **Descriptive save buttons**: Renamed all four identical `'Save Image'` buttons to:
  - `'Save DPC'` (Differential Phase Contrast)
  - `'Save Phase'` (Integrated Phase)
  - `'Save Transmission'`
  - `'Save Dark Field'`
- **Batch save button**: Added `'Save All to folder...'` button that saves all four reconstruction images (DPC, Phase, Transmission, Dark Field) as float32 TIFF files plus a `reconstruction_config.json` file to a user-selected directory in a single operation.

### TLRec Batch – Reconstruction Batch GUI Enhancements
- **Custom config support**: Added config file (.json) picker allowing users to load custom reconstruction parameters instead of always using the default config.
- **Per-file progress bar**: Added visual progress bar that advances with each acquisition processed, providing feedback during batch reconstruction.

---

## [v. 1.1.1] – Detector Post-Processing & Noise Model Improvements

### Detector Post-Processing (Inline & Talbot-Lau)
- Added full **post-processing detector model** without rerunning the simulation.
- Detector effects (PSF, downsampling and noise) can now be applied interactively to:
  - Inline simulations
  - Talbot-Lau object and reference stacks
- Raw (pre-detector) and post-processed images are displayed side-by-side for direct comparison.

### Physically-Meaningful Poisson Noise Model
- Replaced ad-hoc Poisson noise with a **photon-count–based model**.
- Introduced a configurable **photon number parameter `N0`**:
  - Intensity is scaled by `N0`
  - Poisson noise is applied in photon space
  - Output is renormalized after detection

### Talbot-Lau Post-Processing Enhancements
- Detector post-processing now affects **both object and reference stacks**.
- Stack browsing implemented via slice selection without altering window/level.
- Fixed layout and resizing issues when displaying multiple images simultaneously.

### Stability & Bug Fixes
- Fixed UI state bugs where disabled widgets were re-enabled after simulation.
- Fixed frame resizing issues causing images or colorbars to overflow or hide widgets.
- Improved thread-safe GUI updates during post-processing operations.


---
[v. 1.1.0] - Major GUI Refactor & Usability Improvements

### 1. General Architecture Improvements
- Removed all `global root` patterns throughout the codebase for safety, clarity, and better separation of concerns.
- Standardized constructors to receive `master` as parent container instead of creating or overwriting Tk roots.
- Added a shared status bar (`ttk.Label` bound to `status_var`) to all GUIs for real-time feedback.
- Added a thread-safe execution wrapper to avoid GUI freezing on long tasks.

---

## 2. TLRec – Reconstruction GUI Enhancements

### 2.1. Scrolling Support
- Implemented a custom `VerticalScrolledFrame` to handle large content on all platforms (Windows/Linux).
- Embedded the entire TLRec GUI inside the scrollable container.
- Fixed issues where large images clipped UI elements on Windows.

### 2.2. Background & Styling Fixes
- Corrected the `Canvas` background of the scroll frame (`bg="gray20"`) so unused space no longer appears white.
- Ensured all internal frames use the dark-themed `TFrame` style.

### 2.3. Window-Level Control Panels
Added per-image brightness/contrast controls for:
- Differential phase  
- Phase  
- Transmission  
- Dark-field  

Features:
- Individual sliders for **Center** and **Width**
- **Auto-level** button per image
- Real-time updating using the existing Matplotlib canvas

### 2.4. Interactive Modulation Curve
- Clicking on the reconstructed phase image automatically updates the modulation curve.

### 2.5. NaN Handling in Reconstruction and in the Uploaded Stacks
- Added `np.nan_to_num`-based fast sanitization for DPC, Dark-Field, Absorption, Transmission, Reference Stack and Object Stack.
- Prevented Wiener filter crashes due to NaNs in frequency domain.

### 2.6 Added Drag and Drop widget
- Added Drag and Drop widget to load Reference/Objects stacks.

---

## 3. PCSim – Simulation GUI Improvements

### 3.1. Added Scrollbars to All Notebook Tabs
- All simulation tabs (`Inline`, `Check TL`, `Talbot-Lau`) now use the same `VerticalScrolledFrame`.
- Prevents layout compression on small screens and allows long parameter forms.

### 3.2. Consistent Window Behavior
- The main application window now freezes to its initial size using:
  ```python
  root.update_idletasks()
  root.minsize(root.winfo_width(), root.winfo_height())
  ```
- Prevents window flickering, shrinking, or showing white margins when switching tabs.

### 3.3. Status Bar Integration
- All long-running tasks (`Inline`, `CheckTL`, `Talbot-Lau`) now call:
  ```python
  self.set_status("Running ...")
  ```
  and update on completion.

### 3.4. Result Frames Styled Consistently
- Parameter sidebars and result areas use `TFrame` styling for visual consistency.

### 3.5. Fixed Matplotlib RC Error
- Removed invalid rcParam `legend.labelcolor` for compatibility with older Matplotlib installs.

### 3.6. Added Presets
- Added new buttons to save/load JSON files with the configuration of a simulation. Now is easier to reproduce simulations.
- Simulation settings can now be exported and reloaded, greatly improving reproducibility and workflow efficiency.

### 3.7. Added Option to Export a Reproducible ZIP Package
- Implemented an automated system to generate a ZIP file containing all relevant simulation data:
  - Input parameters (JSON preset)
  - Output images and numerical results
  - Metadata (timestamp, system info)
- This feature provides complete reproducibility and facilitates sharing or archiving simulation runs.

### 3.8. Error handlind
- Implemented a window with the error when it occurs.

## 4. New Tab for Batch Reconstruction
- Added a new functionality to perform the phase stepping method to retrieve Phase Contrast Images for a lot of Acquisitions.

---
## 5. New Safety, Physics verification and Warnings

### 5.1 Physical Parameter Verification
- Added full verification for Inline, CheckTL and TL simulations.
- Prevents execution when parameters are non-physical (negative distances, invalid radius, wrong pixel size, etc.).

### 5.2 Grating Sampling Verification (through Warnings)
- G1/G2 period not sampled by an even number of pixels.
- Phase stepping does not cover a full period.
- Total stepping not aligned with G2 period.

### 5.3 Improved Talbot Distance Auto-Update
- Fixed cases where distances were not recalculated when inputs changed.

## 6. User Experience Enhancements

### 6.1 Loading Overlay for Long Calculations
- Added a semi-transparent fullscreen overlay showing:
  - "Loading..."
  - Optional progress percentage

- Overlay automatically:
  - blocks all user input
  - stays visible after minimizing/restoring
  - disappears smoothly after finishing

### 6.2 Tooltips System
- Added Tooltips to the widgets

### 7. Help, License & Citation System

### 7.1 Added Help Window
- Includes a (brief for now) user-guide

### 7.2 How to Cite Window
- Includes the citation of the work

### 7.3 License Window
- Includes the License of the work

## 8. Layout Fixes and Stability

### 8.1. Corrected White Zones During Tab Switching
- The scrollframe canvas now inherits the dark theme.

### 8.2. Grid Configuration Standardization
- Normalized `grid_rowconfigure` and `grid_columnconfigure` across tabs to:
  - `weight=1`
- Ensures all tabs expand uniformly to fill available space.

### 8.3. Removed All Root Geometry Side Effects
- No more resizing or collapsing when creating/destroying subframes.
- Notebook automatically fills the whole application area.

---

## 9. Future Work (Planned)
These items were discussed but not approved (yet) for implementation:

- History panel for reconstruction parameters  
- GPU acceleration indicators
- Hover-preview on images
- Plugin-style extension system
- Generate an executable
---

If you have any useful idea or found any bug, please contact with: vicsan05@ucm.es