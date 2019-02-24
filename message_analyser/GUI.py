import os
import logging
import asyncio
import tkinter as tk
import message_analyser.retriever.telegram as tlg
import message_analyser.storage as storage
from message_analyser import analyser
from tkinter import filedialog


async def start_gui(loop):
    app = MessageAnalyserGUI(tk.Tk(), loop)
    try:
        while True:
            # We want to update the application but get back
            # to asyncio's event loop. For this we sleep a
            # short time so the event loop can run.
            #
            # https://www.reddit.com/r/Python/comments/33ecpl
            # print("UPDATED!")
            app.update()
            await asyncio.sleep(0.05)
    except KeyboardInterrupt:
        pass
    except tk.TclError as e:
        if "application has been destroyed" not in e.args[0]:
            raise


class LoggingToGUI(logging.Handler):
    """ Used to redirect logging output to the widget passed in parameters """

    # https://stackoverflow.com/a/18194597

    def __init__(self, console):
        logging.Handler.__init__(self)

        self.console = console  # Any text widget, you can use the class above or not

    def emit(self, message):  # Overwrites the default handler's emit method
        formatted_message = self.format(message)  # You can change the format here

        # Disabling states so no user can write in it
        self.console.configure(state=tk.NORMAL)
        self.console.insert(tk.END, formatted_message)  # Inserting the logger message in the widget
        self.console.configure(state=tk.DISABLED)
        self.console.see(tk.END)
        # print(message)  # You can just print to STDout in your overriden emit no need for black magic


class MessageAnalyserGUI(tk.Frame):
    """Represents a GUI for the message analyser app.

    Contains next frames:
        A frame with a greeting and choosing of the base analyser parameters (raise_start_frame).
        A frame to set analyser attributes based on previous frame results (raise_files_frame).
        A frame to make an initial sign-in into Telegram client (raise_telegram_auth_frame, optional).
        A frame to choose a Telegram dialogue to analyse messages from (raise_dialogs_select_frame, optional).
        A frame to show analysing process and results (raise_finish_frame).

    Attributes:
        parent (tk.Frame): A root frame (tk.Tk()) of a tkinter app.
        loop (asyncio.windows_events._WindowsSelectorEventLoop, optional): An event loop.
        x (int): A horizontal size of the window.
        y (int): A vertical size of the window.
        session_params (dict):
            A dictionary which contains all the message analyser parameters for their future processing. Looks like:
            {
                "from_vk": (bool) True if some messages will be received from the VkOpt file.,
                "from_telegram": (bool) True if some messages will be received from the Telegram.,
                "plot_words": (bool) True if we need a file with words for future analysis of them.,
                "dialogue": (str,optional) String representation ("dialog_name (id=dialog_id)") of a Telegram dialogue.,
                "vkopt_file": (str,optional) A path to the file with VkOpt messages.,
                "words_file": (str,optional) A path to the file with words.,
                "your_name": (str) Your name.,
                "target_name": (str) Target's name.
            }
    """

    def __init__(self, parent, loop, *args, **kwargs):
        """Inits MessageAnalyserGUI class with parent frame and basic attributes. Raises an initial frame of the GUI."""
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title("Message analyser")
        self.x, self.y = 700, 500
        self.parent.geometry(f"{self.x}x{self.y}")
        self.parent.grid_columnconfigure(3, weight=8)
        self.parent.resizable(False, False)
        self.default_font_name = "Courier"
        self.default_font = (self.default_font_name, 11)
        self.button_background = "#ccccff"
        self.aio_loop = loop

        self.session_params = dict()

        self.raise_start_frame()

    def __set_file_path(self, label_text, file):
        """Stores file path in session parameters and changes the corresponding label text."""
        self.session_params[file] = filedialog.askopenfilename(title=file, filetypes=[("Text files", ".txt")])
        label_text.set("File :          " + os.path.split(self.session_params[file])[-1])

    def raise_start_frame(self):
        """Chooses base analyser parameters (do or do not analyse Telegram messages/vk.com messages/words)."""
        labels_frame = tk.Frame()
        labels_frame.pack(side=tk.TOP)

        start_label = tk.Label(labels_frame, text="Hi!\nLet's get started",
                               height=2, width=35, font=(self.default_font_name, 20))
        start_label.pack()

        start_label = tk.Label(labels_frame, text="What do You want to analyse?",
                               height=2, width=35, font=(self.default_font_name, 15))
        start_label.pack()

        check_boxes_frame = tk.Frame()
        check_boxes_frame.pack(anchor=tk.W)
        from_telegram = tk.BooleanVar()
        telegram_check_button = tk.Checkbutton(check_boxes_frame, text="Messages from Telegram", variable=from_telegram,
                                               font=self.default_font)
        telegram_check_button.pack(anchor=tk.W)

        from_vk = tk.BooleanVar()
        vk_check_button = tk.Checkbutton(check_boxes_frame, text="Messages from vkOpt text file", variable=from_vk,
                                         font=self.default_font)
        vk_check_button.pack(anchor=tk.W)

        plot_words = tk.BooleanVar()
        words_check_button = tk.Checkbutton(check_boxes_frame, text="Add file with words", variable=plot_words,
                                            font=self.default_font)
        words_check_button.pack(anchor=tk.W)

        def set_data_and_continue():
            if from_vk.get() or from_telegram.get():
                self.session_params["plot_words"] = plot_words.get()
                self.session_params["from_vk"] = from_vk.get()
                self.session_params["from_telegram"] = from_telegram.get()
                bottom_frame.destroy()
                labels_frame.destroy()
                check_boxes_frame.destroy()
                return self.raise_files_frame()
            telegram_check_button.config(fg="red")
            vk_check_button.config(fg="red")

        bottom_frame = tk.Frame()
        bottom_frame.pack(side=tk.BOTTOM)
        continue_button = tk.Button(bottom_frame, text="Continue", command=set_data_and_continue,
                                    padx=35, background=self.button_background, font=self.default_font)
        continue_button.pack(side=tk.BOTTOM)
        self.parent.bind('<Return>', lambda _: set_data_and_continue())

    def raise_files_frame(self):
        """Chooses a file with words and a file with VkOpt messages; assigns names."""
        table_frame = tk.Frame()
        table_frame.pack(expand=True, fill="both")

        cur_row = 0
        if self.session_params["from_vk"]:
            cur_row += 1
            vkopt_label = tk.Label(table_frame, text="Choose path to:", height=2, font=self.default_font)
            vkopt_label.grid(row=cur_row, column=1, sticky=tk.W)

            vkopt_button = tk.Button(table_frame, text="vkOpt file",
                                     command=lambda: self.__set_file_path(vkopt_filename_label_text, "vkopt_file"),
                                     font=self.default_font)
            vkopt_button.grid(row=cur_row, column=2, sticky=tk.W)

            cur_row += 1
            vkopt_filename_label_text = tk.StringVar()
            vkopt_filename_label_text.set("File :          ")
            vkopt_filename_label = tk.Label(table_frame, textvariable=vkopt_filename_label_text, height=2,
                                            font=self.default_font)
            vkopt_filename_label.grid(row=cur_row, column=1, sticky=tk.W, columnspan=30)

        if self.session_params["plot_words"]:
            cur_row += 1
            words_label = tk.Label(table_frame, text="Choose path to:", height=2, font=self.default_font)
            words_label.grid(row=cur_row, column=1, sticky=tk.W)

            words_button = tk.Button(table_frame, text="words file",
                                     command=lambda: self.__set_file_path(words_filename_label_text, "words_file"),
                                     font=self.default_font)
            words_button.grid(row=cur_row, column=2, sticky=tk.W)

            cur_row += 1
            words_filename_label_text = tk.StringVar()
            words_filename_label_text.set("File :          ")
            words_filename_label = tk.Label(table_frame, textvariable=words_filename_label_text, height=2,
                                            font=self.default_font)
            words_filename_label.grid(row=cur_row, column=1, sticky=tk.W, columnspan=30)

        _, _, _, your_name, target_name = storage.get_session_params()

        cur_row += 1
        your_name_label = tk.Label(table_frame, text="Your name:     ", height=2, font=self.default_font)
        your_name_label.grid(row=cur_row, column=1, sticky=tk.W)

        your_name_dir = tk.Entry(table_frame, width=40, font=self.default_font)
        your_name_dir.insert(tk.END, your_name)
        your_name_dir.grid(row=cur_row, column=2)

        cur_row += 1
        target_name_label = tk.Label(table_frame, text="Target's name: ", height=2, font=self.default_font)
        target_name_label.grid(row=cur_row, column=1, sticky=tk.W)

        target_name_dir = tk.Entry(table_frame, width=40, font=self.default_font)
        target_name_dir.insert(tk.END, target_name)
        target_name_dir.grid(row=cur_row, column=2)

        if self.session_params["from_vk"]:
            cur_row += 1
            names_label = tk.Label(table_frame, text=("Please be sure these names are equal to the names in the \n"
                                                      "vkOpt file. Otherwise vkOpt file will not be read correctly."),
                                   fg="red", height=2, font=self.default_font, justify="left")
            names_label.grid(row=cur_row, column=1, sticky=tk.W, columnspan=30)

        def set_data_and_continue():
            your_name_label.config(fg="black")
            target_name_label.config(fg="black")
            if your_name_dir.get().isspace() or not your_name_dir.get():
                return your_name_label.config(fg="red")
            if target_name_dir.get().isspace() or not target_name_dir.get():
                return target_name_label.config(fg="red")

            if self.session_params["from_vk"]:
                if "vkopt_file" not in self.session_params:
                    return vkopt_filename_label.config(fg="red")
                vkopt_filename_label.config(fg="black")

            if self.session_params["plot_words"]:
                if "words_file" not in self.session_params:
                    return words_filename_label.config(fg="red")
                words_filename_label.config(fg="black")

            self.session_params["your_name"] = your_name_dir.get()
            self.session_params["target_name"] = target_name_dir.get()
            bottom_frame.destroy()
            table_frame.destroy()
            if self.session_params["from_telegram"]:
                return self.raise_telegram_auth_frame()
            self.raise_finish_frame()

        bottom_frame = tk.Frame()
        bottom_frame.pack(side=tk.BOTTOM)
        continue_button = tk.Button(bottom_frame, text="Continue", command=set_data_and_continue,
                                    padx=35, background=self.button_background, font=self.default_font)
        continue_button.pack(side=tk.BOTTOM)
        self.parent.bind('<Return>', lambda _: set_data_and_continue())

    def raise_telegram_auth_frame(self):
        """Makes an initial sign-in into Telegram client."""
        table_frame = tk.Frame()
        table_frame.pack(expand=True, fill="both")

        assert self.session_params["from_telegram"]

        api_id, api_hash, phone_number, _ = storage.get_telegram_secrets()

        api_id_label = tk.Label(table_frame, text="API id :       ", height=2, font=self.default_font)
        api_id_label.grid(row=1, column=1, sticky=tk.W)

        api_id_dir = tk.Entry(table_frame, width=46, font=self.default_font)
        api_id_dir.insert(tk.END, api_id)
        api_id_dir.grid(row=1, column=2, sticky=tk.W)

        api_hash_label = tk.Label(table_frame, text="API hash :     ", height=2, font=self.default_font)
        api_hash_label.grid(row=2, column=1, sticky=tk.W)

        api_hash_dir = tk.Entry(table_frame, width=46, font=self.default_font)
        api_hash_dir.insert(tk.END, api_hash)
        api_hash_dir.grid(row=2, column=2, sticky=tk.W)

        phone_number_label = tk.Label(table_frame, text="Phone number : ", height=2, font=self.default_font)
        phone_number_label.grid(row=3, column=1, sticky=tk.W)

        phone_number_dir = tk.Entry(table_frame, width=46, font=self.default_font)
        phone_number_dir.insert(tk.END, phone_number)
        phone_number_dir.grid(row=3, column=2, sticky=tk.W)

        code_label = tk.Label(table_frame, text="Code :         ", height=2, font=self.default_font)
        code_label.grid(row=4, column=1, sticky=tk.W)

        code_dir = tk.Entry(table_frame, width=46, font=self.default_font)
        code_dir.grid(row=4, column=2, sticky=tk.W)

        message_label_text = tk.StringVar()

        message_label_text.set(("Please be sure You have set the right API ID and key\n"
                                "They can be obtained from:\n"
                                "https://core.telegram.org/api/obtaining_api_id"))
        message_label = tk.Label(table_frame, textvariable=message_label_text, height=3,
                                 font=self.default_font, fg="red", justify="left")
        message_label.grid(row=5, column=1, sticky=tk.W, columnspan=2)

        async def try_sign_in_and_continue():
            res = await tlg.get_sign_in_results(api_id_dir.get(),
                                                api_hash_dir.get(),
                                                code_dir.get(),
                                                phone_number_dir.get(),
                                                self.session_params["your_name"],
                                                loop=self.aio_loop)
            try:
                api_id_label.config(fg="black")
            except tk.TclError:  # too fast "continue" button clicks?
                return
            api_hash_label.config(fg="black")
            phone_number_label.config(fg="black")
            code_label.config(fg="black")
            if res == "wrong api":
                api_id_label.config(fg="red")
                api_hash_label.config(fg="red")
                return message_label_text.set("Please be sure You have set the right API ID and hash\n"
                                              "They can be obtained from:\n"
                                              "https://core.telegram.org/api/obtaining_api_id")
            elif res == "need phone":
                phone_number_label.config(fg="red")
                return message_label_text.set("Please carefully set Your phone number in order to   \n"
                                              "get a confirmation code.\n ")

            elif res == "need code":
                code_label.config(fg="red")
                return message_label_text.set("Please check Your private messages (or SMS) and      \n"
                                              "copypaste the right code.\n ")
            elif res == "no internet":
                return message_label_text.set("Please be sure You have stable Internet connection.\n\n")

            assert res == "success"
            storage.store_telegram_secrets(api_id_dir.get(), api_hash_dir.get(), phone_number_dir.get(),
                                           session_name=self.session_params["your_name"])
            bottom_frame.destroy()
            table_frame.destroy()
            self.aio_loop.create_task(self.raise_dialogs_select_frame())

        bottom_frame = tk.Frame()
        bottom_frame.pack(side=tk.BOTTOM)
        continue_button = tk.Button(bottom_frame, text="Continue",
                                    command=lambda: self.aio_loop.create_task(try_sign_in_and_continue()),
                                    padx=35, background=self.button_background,
                                    font=self.default_font)
        continue_button.pack(side=tk.BOTTOM)
        self.parent.bind('<Return>', lambda _: self.aio_loop.create_task(try_sign_in_and_continue()))

    async def raise_dialogs_select_frame(self):
        """Chooses a Telegram dialogue to analyse messages from."""
        table_frame = tk.Frame()
        table_frame.pack(expand=True, fill="both")

        dialog_select_label = tk.Label(table_frame, text="Please select a dialog You want to analyse messages from :",
                                       height=2, font=self.default_font)
        dialog_select_label.grid(row=1, column=1, sticky=tk.W)

        dialogs = await tlg.get_str_dialogs(loop=self.aio_loop)
        for i in range(len(dialogs)):
            dialogs[i] = ''.join(char for char in dialogs[i] if char < u"\uffff")

        dialog_variable = tk.StringVar()
        dialog_variable.set(dialogs[0])  # default value
        dialog_selection_menu = tk.OptionMenu(table_frame, dialog_variable, *dialogs)
        dialog_selection_menu.grid(row=2, column=1, sticky=tk.W)

        def select_dialog_and_continue():
            self.session_params["dialogue"] = dialog_variable.get()
            bottom_frame.destroy()
            table_frame.destroy()
            self.raise_finish_frame()

        bottom_frame = tk.Frame()
        bottom_frame.pack(side=tk.BOTTOM)
        continue_button = tk.Button(bottom_frame, text="Continue",
                                    command=select_dialog_and_continue, padx=35, background=self.button_background,
                                    font=self.default_font)
        continue_button.pack(side=tk.BOTTOM)
        self.parent.bind('<Return>', lambda _: select_dialog_and_continue())

    def raise_finish_frame(self):
        """Shows analysis process and results."""
        table_frame = tk.Frame()
        table_frame.pack(expand=True, fill="both")

        finish_label = tk.Label(table_frame,
                                text=("Plots and other data will be saved in a 'results' folder.\n"
                                      "Please, wait for the 'Done.' line. It takes some time..."),
                                height=2, justify="left")
        finish_label.pack(anchor=tk.W)

        text_widget = tk.Text(table_frame)
        text_widget.pack(expand=True, fill="both")

        logger = logging.getLogger("message_analyser")
        logger.addHandler(LoggingToGUI(text_widget))
        self.finalise()

    def finalise(self):
        storage.store_session_params(self.session_params)
        self.aio_loop.create_task(analyser.retrieve_and_analyse(self.aio_loop))


if __name__ == "__main__":
    aio_loop = asyncio.get_event_loop()
    try:
        aio_loop.run_until_complete(start_gui(aio_loop))
    finally:
        if not aio_loop.is_closed():
            aio_loop.close()
