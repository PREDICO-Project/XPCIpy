# CHANGELOG.md

## XPCIpy GUI – Change Log
This document summarizes all approved updates, fixes, and improvements implemented in the Reconstruction (TLRec) and Simulation (PCSim) GUI modules.

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