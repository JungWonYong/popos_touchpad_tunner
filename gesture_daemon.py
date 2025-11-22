import subprocess
import sys
import re
import argparse
import signal
import os

def set_ctm(device_id, multiplier):
    try:
        subprocess.run(
            ['xinput', 'set-prop', str(device_id), 'Coordinate Transformation Matrix', 
             str(multiplier), '0', '0', '0', str(multiplier), '0', '0', '0', '1'],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"Error setting CTM: {e}", file=sys.stderr)

def set_profile(device_id, profile_type):
    # profile_type: 'adaptive' or 'flat'
    val = "1, 0" if profile_type == 'adaptive' else "0, 1"
    try:
        subprocess.run(
            ['xinput', 'set-prop', str(device_id), 'libinput Accel Profile Enabled', val.split(',')[0], val.split(',')[1]],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"Error setting profile: {e}", file=sys.stderr)

def get_current_profile(device_id):
    try:
        output = subprocess.check_output(
            ['xinput', 'list-props', str(device_id)],
            text=True
        )
        for line in output.splitlines():
            if 'libinput Accel Profile Enabled (' in line:
                parts = line.split(':')[1].strip().split(',')
                if parts[0].strip() == '1':
                    return 'adaptive'
                elif parts[1].strip() == '1':
                    return 'flat'
    except Exception as e:
        print(f"Error reading profile: {e}", file=sys.stderr)
    return 'adaptive'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', required=True, help="Touchpad Device ID")
    parser.add_argument('--normal', type=float, default=1.0, help="Normal CTM multiplier")
    parser.add_argument('--gesture', type=float, default=0.4, help="Gesture (3-finger) CTM multiplier")
    args = parser.parse_args()

    device_id = args.device
    normal_ctm = args.normal
    gesture_ctm = args.gesture

    print(f"Starting Gesture Daemon for Device {device_id}")
    print(f"Normal CTM: {normal_ctm}, Gesture CTM: {gesture_ctm}")

    # Capture initial profile to restore later
    initial_profile = get_current_profile(device_id)
    print(f"Initial Profile: {initial_profile}")

    # Ensure we start with normal CTM and initial profile
    set_ctm(device_id, normal_ctm)
    set_profile(device_id, initial_profile)

    # Start libinput debug-events
    event_node = find_event_node(device_id)
    if not event_node:
        print("Could not find event node for device.", file=sys.stderr)
        return

    print(f"Monitoring {event_node}...")
    
    process = subprocess.Popen(
        ['sudo', 'libinput', 'debug-events', '--device', event_node],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    # Handle exit signals to restore CTM
    def signal_handler(sig, frame):
        print("\nExiting... Restoring Normal CTM and Profile.")
        set_ctm(device_id, normal_ctm)
        set_profile(device_id, initial_profile)
        process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Track current state to avoid redundant calls
    is_gesture_active = False

    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            # Check for GESTURE_SWIPE_BEGIN/END
            if 'GESTURE_SWIPE_BEGIN' in line:
                parts = line.split()
                try:
                    fingers = int(parts[-1])
                    if fingers >= 3:
                        print(f"Gesture Begin ({fingers} fingers) -> Low Sensitivity & Flat Profile")
                        set_ctm(device_id, gesture_ctm)
                        set_profile(device_id, 'flat')
                        is_gesture_active = True
                except ValueError:
                    pass
            
            elif 'GESTURE_SWIPE_END' in line:
                if is_gesture_active:
                    print("Gesture End -> Normal Sensitivity & Restore Profile")
                    set_ctm(device_id, normal_ctm)
                    set_profile(device_id, initial_profile)
                    is_gesture_active = False

    except Exception as e:
        print(f"Error in loop: {e}", file=sys.stderr)
    finally:
        set_ctm(device_id, normal_ctm)
        set_profile(device_id, initial_profile)
        process.terminate()

def find_event_node(device_id):
    try:
        output = subprocess.check_output(['xinput', 'list-props', str(device_id)], text=True)
        for line in output.splitlines():
            if 'Device Node' in line:
                # Device Node (307):	"/dev/input/event13"
                match = re.search(r'"([^"]+)"', line)
                if match:
                    return match.group(1)
    except:
        pass
    return None

def get_event_node_id(device_id):
    # Helper not used if find_event_node works
    pass

if __name__ == "__main__":
    main()
