"""
main.py  —  OS Scheduler 3D Entry Point
Run: python main.py
"""
import sys
import gui_input as gui_mod
import visualizer as vis

_pending_new_run = False

def new_run_callback():
    global _pending_new_run
    _pending_new_run = True

def _check_new_run(val):
    from OpenGL.GLUT import glutTimerFunc, glutLeaveMainLoop
    global _pending_new_run
    if _pending_new_run:
        _pending_new_run = False
        glutLeaveMainLoop()
    else:
        glutTimerFunc(100, _check_new_run, 0)

def main():
    data = gui_mod.InputGUI().run()
    if data is None:
        print("No data. Exiting."); sys.exit(0)

    vis.load_run(data, on_new_run=new_run_callback)
    vis.init_window()

    from OpenGL.GLUT import (glutTimerFunc, glutMainLoop, glutDisplayFunc,
                              glutReshapeFunc, glutKeyboardFunc, glutMouseFunc,
                              glutMotionFunc, glutPassiveMotionFunc, glutSpecialFunc)
    while True:
        glutTimerFunc(100, _check_new_run, 0)
        try:
            glutMainLoop()
        except SystemExit:
            break
        data = gui_mod.InputGUI().run()
        if data is None:
            break
        vis.load_run(data, on_new_run=new_run_callback)
        glutDisplayFunc(vis.display)
        glutReshapeFunc(vis.reshape)
        glutKeyboardFunc(vis.keyboard)
        glutSpecialFunc(vis.special_key)
        glutMouseFunc(vis.mouse)
        glutMotionFunc(vis.motion)
        glutPassiveMotionFunc(vis.passive_motion)
        glutTimerFunc(16, vis.timer_callback, 0)

    print("Goodbye!")

if __name__ == "__main__":
    main()
