# Path of Exile Helper

A Windows automation tool for Path of Exile and Path of Exile 2 that provides various quality-of-life automation features through a user-friendly GUI interface.

## Features

- **Flask Automation**: Automatically presses flask keys at configurable intervals
- **Weapon Swap**: Automated weapon swapping functionality
- **Map Anointing**: Automated map anointing with image detection
- **Item Dumping**: Quick item dumping to stash with coordinate selection
- **Hotkey Support**: Customizable hotkeys for all features
- **POE Version Detection**: Supports both Path of Exile and Path of Exile 2
- **Settings Persistence**: All settings are saved and restored automatically

## Requirements

- Windows 10/11
- Python 3.7+ (for development)
- Path of Exile or Path of Exile 2 installed

## Installation

### Using the Pre-built Executable

1. Download `POE_Helper.exe` from the `src/dist/` directory
2. Run the executable (no installation required)

### From Source

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd auto
   ```

2. Install dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```

3. Run the application:
   ```bash
   python src/helper.py
   ```

## Usage

1. Launch the application
2. Configure your settings in the GUI:
   - Set flask keys and delay intervals
   - Configure weapon swap key
   - Set up hotkeys for each feature in the Settings tab
3. Enable features as needed using the buttons or hotkeys
4. The application will only work when Path of Exile is the active window (configurable)

## Project Structure

```
.
├── README.md           # This file
├── release.txt         # Release notes
└── src/                # Source code directory
    ├── assets/         # Image assets for detection
    ├── build/          # Build artifacts (PyInstaller)
    ├── dist/           # Distribution (executable)
    ├── helper.py       # Main application entry point
    ├── flask.py        # Flask automation module
    ├── weapon_swap.py  # Weapon swap automation module
    ├── map_anoint.py   # Map anointing module
    ├── dump_items.py   # Item dumping module
    ├── settings_manager.py  # Settings persistence
    ├── settings.json   # User settings file
    ├── requirements.txt    # Python dependencies
    └── helper.spec     # PyInstaller spec file
```

## Building

To build the executable from source:

```bash
cd src
pyinstaller helper.spec
```

The executable will be generated in `src/dist/POE_Helper.exe`.

## Configuration

Settings are automatically saved to `src/settings.json`. You can manually edit this file or use the GUI to configure:

- Flask button keys and delays
- Weapon swap key
- Hotkeys for all features
- Item dump coordinates

## Dependencies

- `pyinstaller` - Executable building
- `psutil` - Process detection
- `pyautogui` - Mouse/keyboard automation
- `keyboard` - Global hotkey support
- `pywin32` - Windows API access
- `opencv-python` - Image processing for map detection
- `numpy` - Numerical operations
- `Pillow` - Image handling

## Notes

- The application requires administrator privileges for global hotkey functionality
- All automation features only work when Path of Exile is the active window (by default)
- Press F11 to stop flask automation
- Settings are automatically saved when changed

## License

[TBD]

## Disclaimer

This tool is for personal use only. Use at your own risk and in accordance with Path of Exile's terms of service.
