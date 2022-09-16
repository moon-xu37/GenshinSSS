import time
from ctrl.interpret import Interpreter
from ctrl.output import Plotter, ExcelWriter

welcome = 'Muhe Ye!\n欢迎使用 原神 简单半自动模拟器 (Simple Semi-Automatic Simulator / SSS)\n'


def work_loop(mode: int = 0):
    if mode == 0:
        print(welcome)
    else:
        print('继续进行工作\n')
    return simulating()


def simulating():
    interpreter = Interpreter()
    interpreter.read_file()
    t1 = time.perf_counter()
    try:
        interpreter.main_loop()
    except Exception as e:
        print(e)
    t2 = time.perf_counter()
    print(f'模拟环节已完成--模拟用时: {t2-t1:.4f}s\n')

    choose = input('下面进入绘图环节,如需跳过请输入`n`,输入回车以继续绘图:')
    if choose == 'n':
        return outputting(interpreter)
    else:
        return plotting(interpreter)


def plotting(interpreter: Interpreter):
    plotter = Plotter(interpreter)
    t1 = time.perf_counter()
    try:
        plotter.work()
    except Exception as e:
        print(e)
    t2 = time.perf_counter()
    print('开始帧={}, 结束帧={}, 偏置帧={}'.format(
        plotter.start, plotter.end, plotter.bias))
    print(f'绘图环节已完成--绘图用时: {t2-t1:.4f}s\n')

    choose = input('下面进入数据输出环节,如需跳过请输入`n`,输入回车以继续数据输出:')
    if choose == 'n':
        return work_loop(1)
    else:
        return outputting(interpreter)


def outputting(interpreter: Interpreter):
    writer = ExcelWriter(interpreter)
    t1 = time.perf_counter()
    writer.work()
    t2 = time.perf_counter()
    print(f'数据输出环节已完成--数据输出用时: {t2-t1:.4f}s\n')
    choose = input('如需继续工作请输入`y`,输入回车以退出:')
    if choose == 'y':
        return work_loop(1)
    else:
        return


if __name__ == '__main__':
    work_loop()
