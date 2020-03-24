import json
import os
import time
from threading import Thread
from tkinter import filedialog, Tk

import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)  # 初始化混音器，可有效降低音效延迟
pygame.init()  # 初始化游戏空间

display_width = 1000  # 定义游戏窗口 宽和高
display_height = 600

gameDisplay = pygame.display.set_mode((display_width,
                                       display_height))  # 初始化游戏窗口
pygame.display.set_caption('弹琴')  # 设置窗口标题

# 初始化三种颜色，并且用设置的背景色填充游戏窗口
red = 200, 20, 20
green = 20, 200, 20
backgroundColor = 220, 220, 200
gameDisplay.fill(backgroundColor)
pygame.display.update()

# 初始化全局变量
gameExit = False  # 不要退出游戏
channel_number = 1  # 设置通道计数器
channel = [0]  # 初始化从1到6声音通道序列
for i in range(1, 7):
    channel.append(pygame.mixer.Channel(i))
records = []  # 初始化存储录音变量
recording = False  # 录音状态
startTime = 0  # 时间戳
OSD = []  # 用来显示文字的容器

squares = []  # 方块儿显示容器
lines = []  # 五线谱显示容器
clock = pygame.time.Clock()  # 时钟对象

# 五线谱发生器速度设定
spawn_event = pygame.USEREVENT + 1
pygame.time.set_timer(spawn_event, 3000)  # 三秒（3000毫秒）一小节

# 指定保存子文件夹
saveFileRoot = 'records'

# 设置音阶字典 对应音频文件来源于 'https://github.com/saransha/EasyElectric'
sound_map = {
    'do0': 'Piano/Piano.ff.C2.wav',  # 低音部分
    're0': 'Piano/Piano.ff.D2.wav',
    'mi0': 'Piano/Piano.ff.E2.wav',
    'fa0': 'Piano/Piano.ff.F2.wav',
    'so0': 'Piano/Piano.ff.G2.wav',
    'la0': 'Piano/Piano.ff.A2.wav',
    'si0': 'Piano/Piano.ff.B2.wav',
    'do1': 'Piano/Piano.ff.C3.wav',  # 中音部分
    're1': 'Piano/Piano.ff.D3.wav',
    'mi1': 'Piano/Piano.ff.E3.wav',
    'fa1': 'Piano/Piano.ff.F3.wav',
    'so1': 'Piano/Piano.ff.G3.wav',
    'la1': 'Piano/Piano.ff.A3.wav',
    'si1': 'Piano/Piano.ff.B3.wav',
    'do2': 'Piano/Piano.ff.C4.wav',  # 高音部分
    're2': 'Piano/Piano.ff.D4.wav',
    'mi2': 'Piano/Piano.ff.E4.wav',
    'fa2': 'Piano/Piano.ff.F4.wav',
    'so2': 'Piano/Piano.ff.G4.wav',
    'la2': 'Piano/Piano.ff.A4.wav',
    'si2': 'Piano/Piano.ff.B4.wav',
    'do3': 'Piano/Piano.ff.c5.wav'
}
# 设置按键映射字典 目前中音是数字键1-8，低音是最下面一排字母键Z-M，高音是A-K
key_map = {
    pygame.K_1: 'do1', pygame.K_2: 're1', pygame.K_3: 'mi1',  # 中音部分
    pygame.K_4: 'fa1', pygame.K_5: 'so1', pygame.K_6: 'la1',
    pygame.K_7: 'si1', pygame.K_8: 'do2',
    pygame.K_z: 'do0', pygame.K_x: 're0', pygame.K_c: 'mi0',  # 低音部分
    pygame.K_v: 'fa0', pygame.K_b: 'so0', pygame.K_n: 'la0',
    pygame.K_m: 'si0', pygame.K_COMMA: 'do1',
    pygame.K_a: 'do2', pygame.K_s: 're2', pygame.K_d: 'mi2',  # 高音部分
    pygame.K_f: 'fa2', pygame.K_g: 'so2', pygame.K_h: 'la2',
    pygame.K_j: 'si2', pygame.K_k: 'do3'
}
# 控制按键 KEY for control functions
key_for_record = pygame.K_BACKSLASH
key_for_playback = pygame.K_BACKSPACE
key_for_loadFile = pygame.K_LEFTBRACKET
key_for_saveFile = pygame.K_RIGHTBRACKET

# 定义音符显示位置
note_position = {
    'do0': 379, 're0': 367, 'mi0': 355, 'fa0': 343,  # 低音部分
    'so0': 331, 'la0': 319, 'si0': 307,
    'do1': 295, 're1': 283, 'mi1': 272, 'fa1': 259,  # 中音部分
    'so1': 247, 'la1': 235, 'si1': 223,
    'do2': 210, 're2': 198, 'mi2': 185, 'fa2': 173,  # 高音部分
    'so2': 160, 'la2': 148, 'si2': 135, 'do3': 123
}


def async_call(fn):  # 设置同步执行函数
    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()

    return wrapper


class Square:
    """方块类（class Note）
    名字虽然是Square，实际上已经改成了image：note_130.png
    暂时沿用名字
    """

    def __init__(self, group, startY):
        w, h = 100, 100  # temp vars
        self.image = pygame.Surface((w, h))  # 方块要渲染的图像
        self.image.fill(backgroundColor)  # 填充颜色
        # self.image.set_colorkey(backgroundColor)
        self.image = pygame.image.load("images/note_130.png")
        self.rect = self.image.get_rect()  # 方块的矩形对象
        self.rect.centerx = display_width - 5  # x坐标移到屏幕中央
        self.rect.centery = startY  # y坐标移到屏幕中央
        self.dx = -1  # 水平单位位移
        self.dy = 0  # 垂直单位位移
        self.group = group
        self.group.append(self)  # 把自己添加到组中

    def move(self):  # 移动矩形Surface对象
        self.rect.move_ip(self.dx, self.dy)
        self.vanish_on_edge()

    def vanish_on_edge(self):  # 超出边缘后移除
        if self.rect.right <= 0: self.group.remove(self)


class Text:  # 文字显示类
    def __init__(self, text, color, group, timer=0):
        self.myFont = pygame.font.Font(None, 50)
        self.image = self.myFont.render(text, True, color)
        self.group = group
        self.group.append(self)  # 把自己添加到组中

    def remove(self):
        self.group.remove(self)


class Line(Square):  # 继承方块类
    def __init__(self, group):  # 为五线谱重新初始化
        w, h = 200, 100  # temp vars
        self.image = pygame.Surface((w, h))  # 创建五线谱对象
        self.image = pygame.image.load("images/line.png")  # 五线谱要渲染的图像
        self.rect = self.image.get_rect()  # 五线谱的矩形对象
        self.rect.centerx = display_width + 100  # 创建时的x坐标
        self.rect.centery = 260  # 创建时的y坐标
        self.dx = -1  # 水平单位位移
        self.dy = 0  # 垂直单位位移
        self.group = group
        self.group.append(self)  # 把自己添加到组中


def beep(sound):  # 播放音阶（升级了多通道播放）
    global channel_number  # 声明全局变量 用来切换声道
    if channel_number > 6:
        channel_number = 1
    sounds = pygame.mixer.Sound(sound_map[sound])  # 读入音阶字典
    channel[channel_number].play(sounds)  # 指定声道播放
    channel_number += 1  # 切换声道
    Square(squares, note_position[sound])
    return


@async_call
def play(data_to_play):  # 异步调用回放模块
    playing = Text('Playing records...', green, OSD)
    for wait, note in data_to_play:  # 依次按时间间隔播放记录的音符
        time.sleep(wait)
        if note in key_map:
            beep(key_map[note])
    time.sleep(2)
    playing.remove()
    return


@async_call
def writeToFile(data_to_write):  # 异步调用存盘，主要是为了显示文字的延时
    timeStr = time.strftime("%Y-%m-%d.%H-%M-%S", time.localtime(time.time()))
    root = os.path.abspath(os.path.join(os.getcwd(), saveFileRoot))
    if not os.path.isdir(root):  # 如果文件夹不存在就创建一个
        os.mkdir(root)
    filename = os.path.join(root, 'record.' + timeStr + '.notemap')
    jsonData = []
    for delay, note in data_to_write:  # 数据整理成json格式，方便未来扩展功能
        dataFormat = {'delay': round(delay, 3), 'note': note}
        jsonData.append(dataFormat)
    with open(filename, 'w', encoding='utf-8') as jsonFile:
        json.dump(jsonData, jsonFile, ensure_ascii=False, indent=2)
    textWritten = Text('File written.', green, OSD)  # 显示文件已保存
    time.sleep(2)
    textWritten.remove()
    return


def readFromFile():
    file_root = Tk()  # 初始化Tk
    file_root.withdraw()
    data_read = []
    file = filedialog.askopenfilename(title=u'选择要播放的文件',
                                      initialdir=(os.path.join(os.getcwd(), saveFileRoot)))  # 打开选择文件窗口
    with open(file, encoding='utf-8') as jsonFile:
        data_dict = json.load(jsonFile)
    file_root.destroy()  # 关闭Tk，焦点返回主窗口
    for data in data_dict:
        data_read.append(list(data.values()))
    return data_read


textRecording = Text('', red, OSD)  # 因为录制伴随主进程，所以先初始化录制实例

while not gameExit:
    for event in pygame.event.get():
        if event.type == spawn_event:  # 根据定时器生产五线谱
            Line(lines)
        if event.type == pygame.QUIT:  # 设定关闭程序的方法
            gameExit = True

        if event.type == pygame.KEYDOWN:  # 如果有按键按下
            keyDown = event.key
            if keyDown == pygame.K_ESCAPE:  # 按下‘ESC’键退出
                gameExit = True

            # 设定各个音阶按键
            if keyDown in key_map:
                beep(key_map[keyDown])

            # 设定各个控制功能按键
            if keyDown == key_for_record:  # 设置激活录音功能
                recording = not recording  # 按一次是开始录音，再按停止
                if recording:
                    records = []  # 初始化录音变量，因为之前已经有过初始化，所以如果注销本句，每次开始录音会累计录制
                    startTime = time.time()  # 记录开始时间
                    textRecording = Text('Recording...', red, OSD)
                else:
                    textRecording.remove()  # 若停止录音，清除’录音中‘字样
            if keyDown == key_for_playback:  # 设置回放
                play(records)
            if keyDown == key_for_saveFile:  # 调用写文件
                writeToFile(records)
            if keyDown == key_for_loadFile:  # 调用读取文件并播放
                records = readFromFile()
                play(records)

            if recording:  # 如果录音状态中
                waitTime = time.time() - startTime  # 记录音符中间的间隔
                startTime = time.time()
                records.append([waitTime, keyDown])  # 添加音符记录
                # print('录制中...', len(records), keyDown, lastTime)
    [line.move() for line in lines]  # 移动五线谱
    [square.move() for square in squares]  # 移动每个方块
    # 渲染各个图像，一般首先渲染screen，它做为背景
    gameDisplay.fill(backgroundColor)
    [gameDisplay.blit(line.image, line.rect) for line in lines]
    [gameDisplay.blit(square.image, square.rect) for square in squares]
    [gameDisplay.blit(text.image, (100, 450)) for text in OSD]
    pygame.display.update()  # 刷新游戏屏幕显示
    clock.tick(60)  # set fps 60

pygame.quit()  # 关闭游戏
quit()
