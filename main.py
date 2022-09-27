import time
from itertools import combinations
from ctrl.interpret import Interpreter
from ctrl.output import Plotter, ExcelWriter
from ctrl.shapley import ShapleyInterpreter

welcome = 'Muhe Ye!\n欢迎使用 原神 简单半自动模拟器 (Simple Semi-Automatic Simulator / SSS)\n'

__mode = ''

__cnt = 0


def work_loop():
    global __cnt, __mode
    if __cnt == 0:
        print(welcome)
        __mode = input('进入沙普利值分析模式请输入`s`,只进行数据输出请输入`o`,如需进行完整输出输入回车:')
    else:
        print(f'\n继续进行工作,第{__cnt+1}项工作\n')

    if __mode == 's':
        return shapley_sim()
    elif __mode == 'o':
        return simulating()
    else:
        return simulating()


def simulating():
    global __mode
    interpreter = Interpreter()
    try:
        interpreter.read_file()
    except:
        print('初始化出现错误')
    t1 = time.perf_counter()
    try:
        interpreter.main_loop()
        t2 = time.perf_counter()
        print(f'模拟环节已完成--模拟用时: {t2-t1:.4f}s\n')
    except Exception as e:
        print(e)
        print('模拟环节出现错误')

    if __mode == 'o':
        print('下面进入数据输出环节\n')
        return outputting(interpreter)
    else:
        print('下面进入绘图环节\n')
        return plotting(interpreter)


def plotting(interpreter: Interpreter):
    plotter = Plotter(interpreter)
    t1 = time.perf_counter()
    try:
        plotter.work()
        t2 = time.perf_counter()
        print('\n开始帧={}, 结束帧={}, 偏置帧={}'.format(
            plotter.start, plotter.end, plotter.bias))
        print(f'绘图环节已完成--绘图用时: {t2-t1:.4f}s\n')
    except Exception as e:
        print(e)
        print('绘图环节出现错误')

    print('下面进入数据输出环节\n')
    return outputting(interpreter)


def outputting(interpreter: Interpreter):
    writer = ExcelWriter(interpreter)
    t1 = time.perf_counter()
    try:
        writer.work()
        t2 = time.perf_counter()
        print(f'数据输出环节已完成--数据输出用时: {t2-t1:.4f}s\n')
    except Exception as e:
        print(e)
        print('数据输出环节出现错误')

    choose = input('如需继续工作请输入`y`,输入回车以退出:')
    if choose == 'y':
        global __cnt
        __cnt += 1
        return work_loop()
    else:
        return


def shapley_sim():
    mother = Interpreter()
    # try:
    #     mother.read_file()
    #     path = mother.path
    #     characters = list(mother.characters.keys())
    # except:
    #     print('母本初始化出现错误')
    mother.read_file()
    mother.output = False
    mother.main_loop()
    path = mother.path
    characters = list(mother.characters.keys())
    m = ['A', 'B', 'C', 'D']
    v = {}
    t1 = time.perf_counter()
    for n in range(1, 5):
        for comb in combinations(range(4), n):
            interpreter = ShapleyInterpreter(characters, comb)
            interpreter.path = path
            # try:
            #     interpreter.process_file()
            # except:
            #     print('初始化出现错误')
            interpreter.process_file()

            # try:
            #     interpreter.main_loop()
            # except Exception as e:
            #     print(e)
            #     print('模拟环节出现错误')
            interpreter.main_loop()

            writer = ExcelWriter(interpreter)
            # try:
            #     writer.write_sum(''.join(comb))
            # except Exception as e:
            #     print(e)
            #     print('数据输出环节出现错误')
            s = writer.write_sum(''.join([m[i] for i in comb]))
            v[comb] = s
            print(comb, '完成')
    t2 = time.perf_counter()
    print(f'沙普利值模拟环节已完成--模拟用时: {t2-t1:.4f}s\n')
    
    plotter = Plotter(mother)
    t1 = time.perf_counter()
    try:
        plotter.shapley_show(v)
        t2 = time.perf_counter()
        print(f'沙普利值绘图环节已完成--绘图用时: {t2-t1:.4f}s\n')
    except Exception as e:
        print(e)
        print('绘图环节出现错误')

    choose = input('如需继续工作请输入`y`,输入回车以退出:')
    if choose == 'y':
        __cnt += 1
        return work_loop()
    else:
        return


if __name__ == '__main__':
    work_loop()
