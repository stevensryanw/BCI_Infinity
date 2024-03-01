import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import os
import numpy as np
import pandas as pd
from PIL import Image, ImageTk
from functools import partial
from snake import EmbeddedGameWindow
import random
from pyOpenBCI import OpenBCICyton
from pylsl import StreamInfo, StreamOutlet
import threading
import multiprocessing
import time

LARGEFONT =("Verdana", 35)
WIDTH = 500
HEIGHT = 500
SPEED = 200
SPACE_SIZE = 50
BODY_SIZE = 1
SNAKE = "#00FF00"
FOOD = "#FF0000"
BACKGROUND = "#000000"

#ensuring this is repo is here and is current cwd
if os.path.isdir("../BCI_Infinity"):
    pathDir = os.path.abspath("../BCI_Infinity")
    print(pathDir)
    while os.getcwd() != pathDir:
        print("Directory is wrong")
        os.chdir(pathDir)
        print("Directory changed to "+pathDir)
#once ensured then check if folder data exists
parentDir = pathDir+"/"
extraDir = "data"
dataPath = os.path.join(pathDir, extraDir)
print(dataPath)
#if it does then take list of files in there
if os.path.isdir("../BCI_Infinity/data"):
    dataPath = os.path.abspath("../BCI_Infinity/data")
    dataFiles = os.listdir(dataPath)
    if len(dataFiles)==0:
        dataFiles = ["No Current Files"]
#if not then create and give the string no files currently
else:
    os.mkdir(dataPath)
    dataFiles = ["No Current Files"]

#make background gray
ctk.set_appearance_mode("dark")

class App(ctk.CTk):
        # __init__ function for class tkinterApp 
    def __init__(self, *args, **kwargs): 
        # __init__ function for class Tk
        ctk.CTk.__init__(self, *args, **kwargs)
        #self._set_appearance_mode("dark")
        # creating a container
        container = ctk.CTkFrame(self)  
        container.pack(side = "top", fill = "both", expand = True) 
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)
        # initializing frames to an empty array
        self.frames = {}  
        # iterating through a tuple consisting
        # of the different page layouts
        #if a page is added it needs to be placed here
        for F in (Home, LiveFeed, UserRecording, Modeling, SnakeGame, USBOutput):
            frame = F(container, self)
            # initializing frame of that object from
            # startpage, page1, page2 respectively with 
            # for loop
            self.frames[F] = frame 
            frame.grid(row = 0, column = 0, sticky ="nsew")
        self.show_frame(Home)
    # to display the current frame passed as
    # parameter
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class LiveFeed(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent)
        label = ctk.CTkLabel(self, text ="Live Feed", font = LARGEFONT)
        label.grid(row = 0, column = 4, padx = 100, pady = 10)
        button1 = ctk.CTkButton(self, text ="Home",corner_radius=25,
                            command = lambda : controller.show_frame(Home))
        button1.grid(row = 1, column = 1, padx = 10, pady = 30)

#first window frame startpage
class Home(ctk.CTkFrame):
    def __init__(self, parent, controller): 
        ctk.CTkFrame.__init__(self, parent)
        # label of frame Layout 2
        label = ctk.CTkLabel(self, text ="BCI Infinty", font = LARGEFONT)
        # putting the grid in its place by using
        # grid
        label.grid(row = 0, column = 4, padx = 100, pady = 10) 
        button1 = ctk.CTkButton(self, text ="Live Feed",corner_radius=25, 
        command = lambda : controller.show_frame(LiveFeed))
        # putting the button in its place by
        # using grid
        button1.grid(row = 1, column = 1, padx = 10, pady = 20)
        ## button to show frame 2 with text layout2
        button2 = ctk.CTkButton(self, text ="Recording Data",corner_radius=25,
        command = lambda : controller.show_frame(UserRecording))
        # putting the button in its place by
        # using grid
        button2.grid(row = 2, column = 1, padx = 10, pady = 20)
        ## button to show model selection frame with
        button3 = ctk.CTkButton(self, text ="Modeling",corner_radius=25,
        command = lambda : controller.show_frame(Modeling))
        # putting the button in its place by
        # using grid
        button3.grid(row = 3, column = 1, padx = 10, pady = 20)
        #including snake game page for now
        button4 = ctk.CTkButton(self, text = "Snake Game", corner_radius=25, 
        command = lambda : controller.show_frame(SnakeGame))
        #places button to switch to snake game page
        button4.grid(row=4, column=1, padx=10, pady=20)
        #including USB output page for now
        button5 = ctk.CTkButton(self, text = "USB Output", corner_radius=25,
        command = lambda : controller.show_frame(USBOutput))
        #places button to switch to USB output page
        button5.grid(row=5, column=1, padx=10, pady=20)

#third window frame page2
class UserRecording(ctk.CTkFrame): 
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent)
        self.label = ctk.CTkLabel(self, text ="Recording Data", font = LARGEFONT)
        self.label.grid(row = 0, column = 4, padx = 100, pady = 10)
        self.instructions_label = ctk.CTkLabel(self, text="Follow the movement instructions below:")
        self.instructions_label.grid(row = 1, column = 4)
        self.canvas = ctk.CTkCanvas(self, width=400, height=400)
        self.canvas.grid(row = 2, column = 4, padx = 100, pady = 10)
        self.prepare_time = 5
        self.hold_time = 10
        self.rest_time = 10
        self.movements = ["Jaw Clench", "Move Right Arm", "Move Left Arm", "Move Legs"]
        self.shuffle_movements()
        self.current_movement_index = 0
        self.current_movement = None
        self.prompt_count = 0
        self.total_prompts = 4 * 40  # 4 movements, 40 times each
        self.start_button = ctk.CTkButton(self, text="Start Collecting", corner_radius=25, command=self.start_prompting)
        self.start_button.grid(row=2, column = 1, padx = 10, pady=30)
        self.home_button = ctk.CTkButton(self, text ="Home",corner_radius=25,
                            command = lambda : controller.show_frame(Home))
        self.home_button.grid(row = 1, column = 1, padx = 10, pady = 30)
        #data collection buttons
        #Begin collection (currently doing nothing)
        #Stop data collection
        self.stop_button = ctk.CTkButton(self, text="Stop Collecting", corner_radius=25, command=self.stop_prompting)
        self.stop_button.grid(row=3, column=1, sticky = "news", padx=10, pady=30)
        self.is_prompting = False  # Flag to check if prompting is in progress
        self.step_start_time = 0
        self.record_thread = None

    def start_prompting(self):
        self.start_button.configure(state=ctk.DISABLED)
        self.stop_button.configure(state=ctk.NORMAL)
        self.is_prompting = True
        self.prompt_next_movement()
        self.start_record()
        #Allow stream to start before prompting
        time.sleep(15)

    def stop_prompting(self):
        self.is_prompting = False
        self.start_button.configure(state=ctk.NORMAL)
        self.stop_button.configure(state=ctk.DISABLED)
        self.instructions_label.configure(text="Training canceled!")
        self.current_movement_index = 0
        self.shuffle_movements()
        self.prepare_time = 5
        self.hold_time = 10
        self.rest_time = 10
        if self.canvas.find_all():
            self.instructions_label.configure(text="Training canceled!")
            self.canvas.delete("all")
            open('tempVal.txt', 'w').close()
            self.stop_record()

    def shuffle_movements(self):
        random.shuffle(self.movements)

    def prompt_next_movement(self):
        if self.prompt_count < self.total_prompts and self.is_prompting:
            self.instructions_label.configure(text="Prepare for the next movement...")
            self.canvas.delete("all")
            self.canvas.after(1000 * self.prepare_time, self.show_movement_instruction)
        else:
            self.instructions_label.configure(text="Training completed!")
            self.stop_prompting()
            open('tempVal.txt', 'w').close()

    def show_movement_instruction(self):
        if self.is_prompting:
            self.instructions_label.configure(text="Hold the movement for {} seconds".format(self.hold_time))
            self.current_movement = self.movements[self.current_movement_index]
            open('tempVal.txt', 'w').close()
            f = open("tempVal.txt", "a")
            f.write(self.current_movement)
            f.close()
            self.canvas.create_text(100, 100, text=self.current_movement)
            self.canvas.after(1000 * self.hold_time, self.show_rest_period)
        else:
            open('tempVal.txt', 'w').close()
            self.instructions_label.configure(text="Training canceled!")
            self.canvas.delete("all")

    def show_rest_period(self):
        if self.is_prompting:
            self.instructions_label.configure(text="Rest for {} seconds".format(self.rest_time))
            self.canvas.delete("all")
            open('tempVal.txt', 'w').close()
            self.prompt_count += 1
            self.current_movement_index = (self.current_movement_index + 1) % len(self.movements)
            if self.current_movement_index == 0:
                self.shuffle_movements()
            self.canvas.after(1000 * self.rest_time, self.prompt_next_movement)

    def start_record(self):
        if self.record_thread is None or not self.record_thread.is_alive():
            self.record_thread = threading.Thread(target=self.record_data)
            self.record_thread.start()

    def stop_record(self):
        if self.record_thread is not None and self.record_thread.is_alive():
            self.record_thread.join()

    def record_data(self):
        SCALE_FACTOR_EEG = (4500000)/24/(2**23-1) #uV/count
        SCALE_FACTOR_AUX = 0.002 / (2**4)
        print("Creating LSL stream for EEG. \nName: OpenBCIEEG\nID: OpenBCItestEEG\n")
        info_eeg = StreamInfo('OpenBCIEEG', 'EEG', 8, 250, 'float32', 'OpenBCItestEEG')
        print("Creating LSL stream for AUX. \nName: OpenBCIAUX\nID: OpenBCItestEEG\n")
        info_aux = StreamInfo('OpenBCIAUX', 'AUX', 3, 250, 'float32', 'OpenBCItestAUX')
        outlet_eeg = StreamOutlet(info_eeg)
        outlet_aux = StreamOutlet(info_aux)
        file_out = open('newest_rename.csv', 'a')
        file_out.truncate(0)
        def lsl_streamers(sample):
            file_in = open('tempVal.txt', 'r')
            input = file_in.readline()
            lbl = ''
            if input != '':
                lbl = input
            else:
                lbl = 'norm'
            outlet_eeg.push_sample(np.array(sample.channels_data)*SCALE_FACTOR_EEG)
            outlet_aux.push_sample(np.array(sample.aux_data)*SCALE_FACTOR_AUX)
            #print(sample.channels_data*SCALE_FACTOR_EEG, sample.aux_data*SCALE_FACTOR_AUX, lbl)
            for datai in sample.channels_data:
                file_out.write(str(datai*SCALE_FACTOR_EEG) + ',')
            for dataj in sample.aux_data:
                file_out.write(str(dataj*SCALE_FACTOR_AUX) + ',')
            file_out.write(str(lbl) + '\n')
            file_in.close()
        board = OpenBCICyton()
        board.start_stream(lsl_streamers)
        file_out.close()

#Page 3: Model Selection, Data Input, Training, and Testing, and Result Visualization
class Modeling(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent)
        label = ctk.CTkLabel(self, text ="User Modeling", font = LARGEFONT)
        label.grid(row = 0, column = 3, padx = 50, pady = 10)
        #Home button
        button1 = ctk.CTkButton(self, text ="Home",corner_radius=25, 
                            command = lambda : controller.show_frame(Home))
        # putting the button in its place 
        # by using grid
        button1.grid(row = 1, column = 1, padx = 10, pady = 30)
        ## dropdown option for the model label with options for models to run, function will run corresponding model
        model_dropdown = ctk.CTkComboBox(self, values = ["LDA", "SVM"])
        model_dropdown.grid(row=2, column = 1, padx=10, pady=10)
        #labels for the data dropdown
        Data_label = ctk.CTkLabel(self, text="Data")
        Data_label.grid(row=3, column=0, padx = 10, pady=10)
        ## dropdown option for the data that we will run into the model. select from csvs, will be populated from directory 
        Data_dropdown = ctk.CTkComboBox(self, values = dataFiles)
        Data_dropdown.grid(row=3, column = 1, padx=10, pady=10)
        ## Creating the file name label and setting it inside of our input frame
        txt_label = ctk.CTkLabel(self, text="File Name")
        ## Here I use grid to place a grid like section of labels, I want the prompt label at index 0
        txt_label.grid(row=4, column=0, padx = 10, pady = 10)
        ## Creating our textbox so user can input file name
        txt_entry = ctk.CTkTextbox(self, height=10)
        txt_entry.grid(row= 4, column =1, padx = 10, pady = 10)
        #will send the user back to the main menu
        run_button = ctk.CTkButton(self, text="Run")
        #put button on a grid
        run_button.grid(row=5, column=0, columnspan = 2, sticky = "news", padx=10, pady=10)

class SnakeGame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent)
        button1 = ctk.CTkButton(self, text ="Home",corner_radius=25, 
                            command = lambda : controller.show_frame(Home))
        button1.grid(row = 1, column = 1, padx = 10, pady = 30)
        label = ctk.CTkLabel(self, text ="Snake Game", font = LARGEFONT)
        label.grid(row = 0, column = 2, padx = 50, pady = 10)
        self.game_frame = EmbeddedGameWindow(self, 260, 260)
        self.game_frame.grid(row=1, column=2, padx=10, pady=10)
        #frame2.update()

#second window frame page1 
class USBOutput(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent)
        label = ctk.CTkLabel(self, text ="USB Output", font = LARGEFONT)
        label.grid(row = 0, column = 4, padx = 100, pady = 10)
        button1 = ctk.CTkButton(self, text ="Home",corner_radius=25,
                            command = lambda : controller.show_frame(Home))
        button1.grid(row = 1, column = 1, padx = 10, pady = 30)

score = 0
direction = 'down'

# Driver Code
app = App()
#setting window size by pixels "width x height"
app.geometry("800x700")
app.update()
#with new size labels should shift right by increasing columns
app.mainloop()