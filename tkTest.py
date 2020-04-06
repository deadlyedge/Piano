import pygame
from tkinter import *  # not advisable to import everything with *
from tkinter import filedialog

pygame.mixer.init()  # initializing the mixer

root = Tk()

audio_file_name = ''


def open_masker():
    global audio_file_name
    audio_file_name = filedialog.askopenfilename(filetypes=(("Audio Files", ".wav .ogg"), ("All Files", "*.*")))


def masker_screen():
    # we will also use the audio_file_name global variable
    global m_screen, audio_file_name

    m_screen = Toplevel(root)
    m_screen.geometry('600x600')
    m_screen.transient(root)
    m_label = Label(m_screen, text="Playing New Masker Noise")
    m_label.pack(anchor=CENTER)

    if audio_file_name:  # play sound if just not an empty string
        noise = pygame.mixer.Sound(audio_file_name)
        noise.play(0, 5000)


b1 = Button(root, text='open file', command=open_masker)
# does not make sense to call pack directly
# and stored the result in a variable, which would be None
b1.pack(anchor=CENTER)

Button(root, text='continue', command=masker_screen).pack(anchor=E)

root.mainloop()
