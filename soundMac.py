import time

import pygame

from async_call import async_call  # 传入模块

pygame.mixer.pre_init(44100, -16, 1, 512)  # 初始化混音器，可有效降低音效延迟
pygame.init()  # 初始化游戏空间

display_width = 1000  # 定义游戏窗口 宽和高
display_height = 600

gameDisplay = pygame.display.set_mode((display_width, display_height))  # 初始化游戏窗口
pygame.display.set_caption('弹琴')  # 设置窗口标题

# 初始化三种颜色，并且用设置的黑色填充游戏窗口
red = 200, 20, 20
green = 20, 200, 20
black = 50, 50, 50
gameDisplay.fill(black)
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
clock = pygame.time.Clock()  # 时钟对象

# 设置音阶字典 对应音频文件来源于 'https://github.com/saransha/EasyElectric'
sound_map = {'do1': 'Piano/Piano.ff.C3.wav',
             're1': 'Piano/Piano.ff.D3.wav',
             'mi1': 'Piano/Piano.ff.E3.wav',
             'fa1': 'Piano/Piano.ff.F3.wav',
             'so1': 'Piano/Piano.ff.G3.wav',
             'la1': 'Piano/Piano.ff.A3.wav',
             'si1': 'Piano/Piano.ff.B3.wav',
             'do2': 'Piano/Piano.ff.C4.wav'
             }
# 设置按键映射字典 目前是数字键1-8
key_map = {
    pygame.K_1: 'do1', pygame.K_2: 're1', pygame.K_3: 'mi1',
    pygame.K_4: 'fa1', pygame.K_5: 'so1', pygame.K_6: 'la1',
    pygame.K_7: 'si1', pygame.K_8: 'do2'
}
# 定义声音 颜色 和 位置
note_color = {
    'do1': (233, 20, 20),
    're1': (233, 115, 20),
    'mi1': (233, 210, 20),
    'fa1': (25, 233, 20),
    'so1': (20, 185, 233),
    'la1': (20, 115, 233),
    'si1': (70, 20, 233),
    'do2': (233, 233, 233)
}
color_position = {'do1': 330, 're1': 300, 'mi1': 270, 'fa1': 240,
                  'so1': 210, 'la1': 180, 'si1': 150, 'do2': 120}


class Text:  # 文字显示类
    def __init__(self, text, color, group):
        self.myFont = pygame.font.Font(None, 50)
        self.image = self.myFont.render(text, True, color)
        self.group = group
        self.group.append(self)  # 把自己添加到组中

    def remove(self):
        self.group.remove(self)


textRecording = Text('', red, OSD)


class Square:
    """方块类"""

    def __init__(self, group, color, startY):
        """初始化"""
        w, h = 40, 40  # temp vars
        self.image = pygame.Surface((w, h))  # 方块要渲染的图像
        # r, g, b, alpha = random.randint(0, 255), random.randint(0, 255), \
        #           random.randint(0, 255), random.randint(0, 255)
        self.image.fill(color)  # 填充颜色
        self.rect = self.image.get_rect()  # 方块的矩形对象
        self.rect.centerx = display_width - 5  # x坐标移到屏幕中央
        self.rect.centery = startY  # y坐标移到屏幕中央
        self.dx = -1  # 水平单位位移
        self.dy = 0  # 垂直单位位移
        self.group = group
        self.group.append(self)  # 把自己添加到组中

    def move(self):
        """移动矩形"""
        self.rect.move_ip(self.dx, self.dy)
        self.vanish_on_edge()

    def vanish_on_edge(self):
        """到边缘消失"""
        if self.rect.right <= 0 or self.rect.left >= display_width or \
                self.rect.bottom <= 0 or self.rect.top >= display_height: self.group.remove(self)


# def drawCircle(color):
#     top = random.randint(50, display_height - 50)
#     left = random.randint(50, display_width - 50)
#     r = random.randint(50, 100)
#     pygame.draw.circle(gameDisplay, color, [top, left], r, 5)
#     pygame.display.update()
#     return


def beep(sound):  # 播放音阶（升级了多通道播放）
    global channel_number  # 声明全局变量 用来切换声道
    if channel_number > 6:
        channel_number = 1
    sounds = pygame.mixer.Sound(sound_map[sound])  # 读入音阶字典
    channel[channel_number].play(sounds)  # 指定声道播放
    channel_number += 1  # 切换声道
    Square(squares, note_color[sound], color_position[sound])
    return


@async_call
def play(data_to_play):  # 回放模块
    playing = Text('Playing records...', green, OSD)
    for note, last in data_to_play:  # 依次按时间间隔播放记录的音符
        time.sleep(last)
        if note in key_map:
            beep(key_map[note])
    time.sleep(1)
    playing.remove()
    return


while not gameExit:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # 设定关闭程序的方法
            gameExit = True

        if event.type == pygame.KEYDOWN:  # 如果有按键按下
            keyDown = event.key

            # 设定各个音阶按键
            if keyDown in key_map:
                beep(key_map[keyDown])

            # 设定各个控制功能按键
            if keyDown == pygame.K_o:  # 设置激活录音功能
                recording = not recording  # 按一次是开始录音，再按停止
                if recording:
                    records = []  # 初始化录音变量
                    startTime = time.time()  # 记录开始时间
                    textRecording = Text('Recording...', red, OSD)
                else:
                    textRecording.remove()  # 若停止录音，清除’录音中‘字样
            if keyDown == pygame.K_p:  # 设置回放
                play(records)

            if recording:  # 如果录音状态中
                lastTime = time.time() - startTime  # 记录音符中间的间隔
                startTime = time.time()
                records.append([keyDown, lastTime])  # 添加音符记录
                # print('录制中...', len(records), keyDown, lastTime)
    [square.move() for square in squares]  # 移动每个方块

    # 渲染各个图像，一般首先渲染screen，它做为背景
    gameDisplay.fill(black)
    [gameDisplay.blit(square.image, square.rect) for square in squares]
    [gameDisplay.blit(text.image, (100, 400)) for text in OSD]
    pygame.display.update()  # 刷新游戏屏幕显示
    clock.tick(60)  # set fps 60

pygame.quit()  # 关闭游戏
