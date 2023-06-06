# https://github.com/OpenBluetoothToolbox/SimpleBLE
# ZSRR Controller Ver2.0
import PySimpleGUI as sg
import simplepyble


# Scan for available PC's BT adapters
# Show user to choose and return chosen
def getAdapter():
    # Scan for available PC BT adapters
    adapters = simplepyble.Adapter.get_adapters()
    adptList = list()
    # Prepare printable list of adapter's names
    for i, ada in enumerate(adapters):
        adptList.append(f"{i}: {ada.identifier()} [{ada.address()}]")
    # Prepare adapter's Listbox
    lst = sg.Listbox(adptList, expand_y=True, expand_x=True)
    # Define window layout
    AdapterWinLayout = [[sg.Text('Choose adapter')],
                        [lst],
                        [sg.Button('OK'), sg.Button('Exit')]]
    AdapterWindow = sg.Window('Adapters', AdapterWinLayout, finalize=True, size=[350, 150])
    while True:
        event, values = AdapterWindow.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == 'OK':
            ada = lst.get_indexes()
            break
    AdapterWindow.close()
    adapter = adapters[ada[0]]
    print(f"Selected adapter: {adapter.identifier()} [{adapter.address()}]")

    # Return chosen adapter, if selected more than 1, return first
    return adapter


# Takes available peripherals
# Prints them to user for choose
# and returns the chosen one
def getPeripheral(peripherals):
    perList = list()
    # Prepare printable list of peripherals names
    for i, peripheral in enumerate(peripherals):
        perList.append(f"{i}: {peripheral.identifier()} [{peripheral.address()}]")
    # Prepare peripherals' Listbox
    lst = sg.Listbox(perList, expand_y=True, expand_x=True)
    # Define window layout
    AdapterWinLayout = [[sg.Text('Choose Peripheral')],
                        [lst],
                        [sg.Button('OK'), sg.Button('Exit')]]
    AdapterWindow = sg.Window('Peripherals', AdapterWinLayout, finalize=True, size=[210, 250])
    while True:
        event, values = AdapterWindow.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == 'OK':
            per = lst.get_indexes()
            break
    AdapterWindow.close()
    # Return chosen peripheral, if selected more than 1, return first
    return peripherals[per[0]]


# Scans for available peripherals with given adapter
def getScan(adapter):
    # Set messages for peripheral scan
    adapter.set_callback_on_scan_start(lambda: print("Scan started."))
    adapter.set_callback_on_scan_stop(lambda: print("Scan complete."))
    adapter.set_callback_on_scan_found(
        lambda peripheral: print(f"Found {peripheral.identifier()} [{peripheral.address()}]"))
    # Scan for 5 seconds and show "scanning" window
    popupLayout = [[sg.Text("Scanning")]]
    scanningWindow = sg.Window("Scan", popupLayout, finalize=True, disable_close=True,
                               disable_minimize=True, size=[100, 60])
    scanningWindow.read(timeout=0, close=False)
    adapter.scan_for(5000)
    peripherals = adapter.scan_get_results()
    scanningWindow.close()
    return peripherals


# Connect to given peripheral
def connect(peripheral):
    popupLayout = [[sg.Text("Connecting")]]
    connectWindow = sg.Window("Connect", popupLayout, finalize=True, disable_close=True,
                              disable_minimize=True, size=[100, 60])
    connectWindow.read(timeout=0, close=False)
    print(f"Connecting to: {peripheral.identifier()} [{peripheral.address()}]")
    peripheral.connect()
    print("Successfully connected, listing services...")
    connectWindow.close()


# Scan for services
# give user choice or select automatically
def getService(peripheral, auto=True):
    services = peripheral.services()
    service_characteristic_pair = []
    for service in services:
        for characteristic in service.characteristics():
            service_characteristic_pair.append((service.uuid(), characteristic.uuid()))

    # Query the user to pick a service/characteristic pair if not auto
    if not auto:
        print("Please select a service/characteristic pair "
              "[15: 0000ffe0-0000-1000-8000-00805f9b34fb 0000ffe1-0000-1000-8000-00805f9b34fb] : ")
        for i, (service_uuid, characteristic) in enumerate(service_characteristic_pair):
            print(f"{i}: {service_uuid} {characteristic}")

        choice = int(input("Enter choice: "))
        return service_characteristic_pair[choice]
    else:
        print("Choosing service automatically!")
        for i, (service_uuid, characteristic) in enumerate(service_characteristic_pair):
            if service_uuid == '0000ffe0-0000-1000-8000-00805f9b34fb':
                return service_characteristic_pair[i]
    print("Couldn't find service to connect automatically!\n"
          " Consider using manual pick")
    return 0


# Show main controlling window
# Takes connected peripheral and its chosen service
# Sends data to robot in loop
def controlWindow(peripheral, service_uuid, characteristic_uuid):
    layout = \
        [
            [sg.Text("ZSRR Controller", justification='center', expand_x=True)],
            [sg.RealtimeButton("↑", size=(2, 1))],
            [sg.RealtimeButton("←", size=(2, 1)), sg.RealtimeButton("→", size=(2, 1))],
            [sg.RealtimeButton("↓", size=(2, 1))],
            [sg.Slider(range=(0, 300), default_value=90, orientation='horizontal', key='MS'),
             sg.Text("Motor Speed", pad=0)],
            [sg.Button('Set'), sg.Slider(range=(0, 135), default_value=90, orientation='horizontal', key='SE'),
             sg.Text("Servo")],
            [sg.Push(), sg.Button("Exit")]
        ]
    window = sg.Window("Controller", layout, size=(300, 250), return_keyboard_events=True, finalize=True)
    window.bind('<Left>', '-LEFT-')
    window.bind('<Right>', '-RIGHT-')
    window.bind('<Down>', '-DOWN-')
    window.bind('<Up>', '-UP-')
    window.bind('<w>', '↑')
    window.bind('<a>', '←')
    window.bind('<s>', '↓')
    window.bind('<d>', '→')
    window.bind('<l>', '-LARGE-')
    window.bind('<k>', '-SMOL-')
    window.bind('<o>', '-OPEN-')

    while True:
        event, values = window.read(timeout=0)
        # Keyboard/Buttons events
        toSend = f"%d%.3d%d%.3d%d%.3d" % (0, 0, 0, 0, 0, 0)
        # Get user input and prepare data to send
        if event == "Exit" or event == sg.WIN_CLOSED:
            print("Exiting!")
            peripheral.disconnect()
            break
        if event == "↑":
            toSend = f"%d%.3d%d%.3d%d%.3d" % (1, values['MS'], 1, values['MS'], 0, 0)
        if event == "←": # or (len(event) == 1 and ord(event) == 97):
            toSend = f"%d%.3d%d%.3d%d%.3d" % (0, values['MS'], 1, values['MS'], 0, 0)
        if event == "→": # or (len(event) == 1 and ord(event) == 100):
            toSend = f"%d%.3d%d%.3d%d%.3d" % (1, values['MS'], 0, values['MS'], 0, 0)
        if event == "↓": # or (len(event) == 1 and ord(event) == 115):
            toSend = f"%d%.3d%d%.3d%d%.3d" % (0, values['MS'], 0, values['MS'], 0, 0)
        if event == 'Set' or (len(event) == 1 and ord(event) == 32):
            toSend = f"%d%.3d%d%.3d%d%.3d" % (1, 0, 1, 0, 1, values['SE'])
        if event == '-LEFT-':
            val = values['SE'] - 5
            if val < 0:
                val = 0
            window['SE'].update(value=val)
            window.refresh()
            toSend = f"%d%.3d%d%.3d%d%.3d" % (1, 0, 1, 0, 1, val)
        if event == '-RIGHT-':
            val = values['SE'] + 5
            if val > 135:
                val = 135
            window['SE'].update(value=val)
            window.refresh()
            toSend = f"%d%.3d%d%.3d%d%.3d" % (1, 0, 1, 0, 1, val)
        if event == '-UP-':
            window['MS'].update(value=values['MS'] + 20)
            window.refresh()
        if event == '-DOWN-':
            window['MS'].update(value=values['MS'] - 20)
            window.refresh()
        if event == '-LARGE-':
            val = 115
            window['SE'].update(value=val)
            window.refresh()
            toSend = f"%d%.3d%d%.3d%d%.3d" % (1, 0, 1, 0, 1, val)
        if event == '-SMOL-':
            val = 125
            window['SE'].update(value=val)
            window.refresh()
            toSend = f"%d%.3d%d%.3d%d%.3d" % (1, 0, 1, 0, 1, val)
        if event == '-OPEN-':
            val = 70
            window['SE'].update(value=val)
            window.refresh()
            toSend = f"%d%.3d%d%.3d%d%.3d" % (1, 0, 1, 0, 1, val)
        # Calculate checkSum
        checkSum = 0
        for i in toSend:
            checkSum = checkSum + int(i)
        toSend = toSend + (f'%.3d' % checkSum)
        # Send data to robot
        # print(toSend)
        peripheral.write_request(service_uuid, characteristic_uuid, str.encode(toSend))
    window.close()


def main():
    # Set windows theme
    sg.theme('DarkAmber')

    # Get adapter to use
    adapter = getAdapter()

    # Scan for peripherals and get results
    peripherals = getScan(adapter)

    # Get peripheral to use
    peripheral = getPeripheral(peripherals)

    # Connect to peripheral
    connect(peripheral)

    # Choose service to use
    service_uuid, characteristic_uuid = getService(peripheral)

    # Show main control window
    controlWindow(peripheral, service_uuid, characteristic_uuid)


if __name__ == "__main__":
    main()
