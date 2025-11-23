# Pop!_OS Multitouch Tuner

A comprehensive GUI tool for fine-tuning touchpad sensitivity, acceleration, and gestures on Linux (specifically optimized for GNOME/Pop!_OS).

![Pop!_OS Multitouch Tuner](icon.png)

## Features

-   **GUI-based Configuration**: Easily adjust pointer speed, acceleration profile, and gesture sensitivity.
-   **Dynamic Sensitivity Control**: Automatically lowers sensitivity and disables acceleration (Flat profile) during 3-finger gestures for precise control.
-   **System Tray Integration**: Minimizes to the system tray for background operation.
-   **Persistence**: Automatically saves and restores settings across reboots.
-   **Autostart**: Option to start automatically on login.
-   **Touchegg Integration**: Configures `touchegg` gesture thresholds and delays.

## Requirements

-   Python 3
-   `libinput-tools` (for `libinput debug-events`)
-   `xinput`
-   `touchegg` (optional, for gesture features)
-   `python3-tk` (Tkinter)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/popos-multitouch-tuner.git
    cd popos-multitouch-tuner
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install System dependencies** (Ubuntu/Pop!_OS):
    ```bash
    sudo apt install python3-tk libinput-tools xinput touchegg
    ```

4.  **Configure Sudo Rights** (Important):
    The daemon needs to run `libinput` without password prompts.
    
    Run the following command to install the sudoers configuration:
    ```bash
    sudo cp popos_multitouch_tuner_sudoers /etc/sudoers.d/popos_multitouch_tuner
    sudo chmod 0440 /etc/sudoers.d/popos_multitouch_tuner
    ```

## Usage

Run the application:
```bash
python3 popos_multitouch_tuner.py
```

-   **Pointer Speed**: Adjusts the standard pointer speed.
-   **Acceleration Profile**: Switch between 'Adaptive' (default) and 'Flat' (no acceleration).
-   **1-Finger Sensitivity**: Adjusts the Coordinate Transformation Matrix (CTM) for global sensitivity.
-   **Dynamic 3-Finger Sensitivity**:
    -   Enable this to automatically lower sensitivity and disable acceleration when using 3-finger gestures (e.g., window dragging).
    -   Adjust the **3-Finger Multiplier** to set the desired sensitivity during gestures.

## License

MIT License

## Credits

This project was created with the assistance of **Google DeepMind's Gemini Antigravity**.
