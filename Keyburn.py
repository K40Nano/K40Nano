from pynput import keyboard

from k40nano.NanoPlotter import NanoPlotter

amount = 50
down = False
plotter = NanoPlotter()
plotter.open()


def on_press(keypress):
    try:
        key = keypress.char
        if key == 'e':
            if not plotter.up():
                plotter.down()
        if key == 'a':
            plotter.move(-amount, 0)
        elif key == 'd':
            plotter.move(amount, 0),
        elif key == 's':
            plotter.move(0, amount)
        elif key == 'w':
            plotter.move(0, -amount)
        elif key == '1':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(10)
        elif key == '2':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(20)
        elif key == '3':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(30)
        elif key == '4':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(40)
        elif key == '5':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(50)
        elif key == '6':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(60)
        elif key == '7':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(70)
        elif key == '8':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(80)
        elif key == '9':
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(90)
    except AttributeError:
        if keypress == keyboard.Key.space:
            plotter.down()
        if keypress == keyboard.Key.home:
            plotter.home()
        return


def on_release(key):
    print('{0} released'.format(key))
    if key == keyboard.Key.esc:
        if not plotter.exit_compact_mode_finish():
            plotter.close()
            return False
        return True
    if key == keyboard.Key.space:
        plotter.up()


# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
