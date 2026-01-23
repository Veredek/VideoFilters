import os
import cv2
import tkinter as tk
import uuid
import inspect
import subprocess
from cv2.typing import MatLike
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
from filters import *
from typing import List, Callable, Any, Dict
from params_defs import PARAMS_DEFS


PADX = 10
PADY = 5
VIDEO_EXTENSIONS = (".mp4", ".avi")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
FRAME: MatLike|None = None
FilterFn = Callable[..., MatLike]


class Filters:
    def __init__(self):
        self.selected: None | str = None

        # region ----|1|---- Filter Params
        self._params_defs = PARAMS_DEFS
        self.params = {}

        for filter_name in self._params_defs.keys():
            param_registry = self._params_defs.get(filter_name, {})
            self.params.setdefault(filter_name, {})
            for param_name, cfg in param_registry.items():
                self.params[filter_name][param_name] = cfg.default
        # endregion -|1|-

        # region ----|1|---- Define filters
        self.filters: List[Callable] = (
            original,
            scanlines,
            blur,
            ca_linear,
            ca_radial,
            warp,
            saturation,
            warmth,
            contrast
        )
        self.t_filters: List[Callable] = ()
        'Filters that work only with time'
        # endregion -|1|-

        # region ----|1|---- Map filters
        self.filters_map: dict[str, FilterFn] = {
            func.__name__: func
            for func in self.filters
        }
        self.t_filters_map: dict[str, FilterFn] = {
            func.__name__: func
            for func in self.t_filters
        }
        self.all_filters_map: dict[str, FilterFn] = self.filters_map | self.t_filters_map
        # endregion -|1|-

    def set_param(
            self,
            filter_name: str,
            param: str,
            value: int
        ) -> None:

        cfg = self._params_defs[filter_name][param]

        def resolve(v):
            if callable(v):
                return v(FRAME)
            return v

        min_v = resolve(cfg.min)
        max_v = resolve(cfg.max)

        self.params[filter_name][param] = max(min_v, min(max_v, value))

    def apply_filter(self, frame: MatLike) -> MatLike:
        filter_fn = self.all_filters_map[self.selected]
        kwargs = self.params.get(self.selected)
        frame = filter_fn(frame, **kwargs)

        return frame


def mux_audio(
    video_no_audio: str, # path
    original_video: str, # path
    output_path: str # path
) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_no_audio,
        "-i", original_video,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        output_path
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def save_image(img: MatLike, filters: Filters):
    path = filedialog.asksaveasfilename(
        title="Salvar imagem",
        defaultextension=".png",
        initialfile=f"{uuid.uuid4().hex}.png",
        filetypes=[
            ("PNG", "*.png"),
            ("JPEG", "*.jpg"),
            ("Todos os arquivos", "*.*")
        ]
    )

    img = filters.apply_filter(img)

    cv2.imwrite(path, img)


def save_video(input_path: str, filters: Filters):
    cap = cv2.VideoCapture(input_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')

    output_path = filedialog.asksaveasfilename(
        title="salvar video",
        defaultextension=".mp4",
        initialfile=f"{uuid.uuid4().hex}.mp4",
        filetypes=[
            ("MP4", "*.mp4"),
            ("AVI", "*.avi")
        ]
    )

    temp_path = f"{uuid.uuid4().hex}.mp4"

    writer = cv2.VideoWriter(
        filename=temp_path,
        fourcc=fourcc,
        fps=fps,
        frameSize=(w, h)
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = filters.apply_filter(frame)
        writer.write(frame)

    cap.release()
    writer.release()

    mux_audio(
        video_no_audio=temp_path,
        original_video=input_path,
        output_path=output_path
    )

    # Delete temporary path
    if os.path.exists(temp_path):
        os.remove(temp_path)

    messagebox.showinfo("Save", "Video Saved Successfully!")


class GUI:
    def __init__(self, filters: Filters):
        # region ----|1|---- GUI Start
        self.root = tk.Tk()
        self.root.title("Midiafilt")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.width = int(screen_w * 0.8)
        self.height = int(screen_h * 0.8)
        self.x = (screen_w - self.width) // 2
        self.y = ((screen_h - self.height) // 2) // 2
        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        self.root.resizable(False, False)
        self.FILTER_COLUMN_WIDTH = 0.15 * self.width
        self.filters = filters
        # endregion -|1|-

        # region ----|1|---- Root Grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=0, minsize=self.FILTER_COLUMN_WIDTH)

        self.left_frame = tk.Frame(self.root)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.divider1 = tk.Frame(self.root, width=2, bg="gray")
        self.divider1.grid(row=0, column=1, sticky="ns")

        self.right_frame = tk.Frame(self.root)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        self.right_frame.grid_propagate(False)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        # endregion -|1|-

        # region ----|1|---- Left Grid
        self.midia_label = tk.Label(self.left_frame, bg="black")
        self.midia_label.pack(expand=True, fill="both")
        # endregion -|1|-

        # region ----|1|---- Right Grid
        self.filter_frame = tk.Frame(self.right_frame, bg="lightgray", width=self.FILTER_COLUMN_WIDTH)
        self.filter_frame.grid(row=0, column=0, sticky="nsew")
        self.filter_frame.grid_propagate(False)
        # endregion -|1|-

        # region ----|1|---- Select File
        self.selected_file: str | None = None
        self.file_ext: str | None = None

        self.file_btn = tk.Button(
            self.filter_frame,
            text="Selecionar arquivo",
            command=self.select_file,
        )

        self.file_btn.pack(fill="x", padx=PADX, pady=PADY)
        # endregion -|1|-

        # region ----|1|---- Select Filter
        self.option_var = tk.StringVar(value="Select Filter")

        self.option_combo = ttk.Combobox(
            self.filter_frame,
            textvariable=self.option_var,
            values=(
                list(self.filters.all_filters_map)
                if self.file_ext in VIDEO_EXTENSIONS
                else list(self.filters.filters_map)
            ),
            state="readonly"
        )

        self.option_combo.bind("<<ComboboxSelected>>", self.apply_filter)
        # endregion -|1|-

        # region ----|1|---- Filter Params
        self.params_frame = tk.Frame(self.filter_frame, bg="lightgray")
        # endregion -|1|-

        # region ----|1|---- Midia
        self.cap = None
        self.tk_img = None
        self.playing = False
        # endregion -|1|-

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecione um vídeo",
            filetypes=[
                ("Imagens e vídeos", "*.png *.jpg *.jpeg *.mp4 *.avi"),
                ("Vídeos", "*.mp4 *.avi *.mov *.mkv"),
                ("Imagens", "*.png *.jpg *.jpeg")
            ]
        )

        self.selected_file = file_path

        # Show filters combobox
        if self.selected_file:
            self.option_combo.pack(padx=PADX, pady=PADY)
            self.params_frame.pack(fill="x", padx=PADX, pady=PADY)

        self.file_ext = os.path.splitext(file_path)[1].lower()
        if self.file_ext in IMAGE_EXTENSIONS:
            self.show_image(file_path)
        elif self.file_ext in VIDEO_EXTENSIONS:
            self.show_video(file_path)

        return file_path if file_path else None

    def show_image(self, path: str):
        global FRAME
        FRAME = cv2.imread(path)
        if FRAME is None: return

        if self.filters.selected:
            FRAME = self.filters.apply_filter(FRAME)

        img: MatLike = cv2.cvtColor(FRAME, cv2.COLOR_BGR2RGB)

        h, w = img.shape[:2]
        frame_w = self.left_frame.winfo_width()
        frame_h = self.left_frame.winfo_height()
        scale = min(frame_w / w, frame_h / h)

        new_w = int(scale * w)
        new_h = int(scale * h)

        if new_w > 1 and new_h > 1:
            img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        pil_img = Image.fromarray(img_resized)
        self.tk_img = ImageTk.PhotoImage(pil_img)

        self.midia_label.configure(image=self.tk_img)

    def show_video(self, path: str):
        if self.cap: self.cap.release()

        self.cap = cv2.VideoCapture(path)
        self.playing = True
        self.update_video()

    def update_video(self):
        global FRAME
        if not self.playing or not self.cap: return

        ret, FRAME = self.cap.read()
        if not ret: # Resets the video loop
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, FRAME = self.cap.read()
            if not ret: return

        if self.filters.selected:
            FRAME= self.filters.apply_filter(FRAME)

        rgb_frame = cv2.cvtColor(FRAME, cv2.COLOR_BGR2RGB)

        h, w = rgb_frame.shape[:2]
        frame_w = self.left_frame.winfo_width()
        frame_h = self.left_frame.winfo_height()
        scale = min(frame_w / w, frame_h / h)

        new_w = int(scale * w)
        new_h = int(scale * h)

        if new_w > 1 and new_h > 1:
            frame_resized = cv2.resize(rgb_frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        pil_frame = Image.fromarray(frame_resized)
        self.tk_img = ImageTk.PhotoImage(pil_frame)

        self.midia_label.configure(image=self.tk_img)

        self.root.after(5, self.update_video)

    def apply_filter(self, event: tk.Event) -> None:
        self.filters.selected = self.option_var.get()
        func = self.filters.all_filters_map[self.filters.selected]

        self.build_filter_controls(func)

        # Pack Save Button
        if self.playing:
            save_btn = tk.Button(
                self.params_frame,
                text="Save",
                command=lambda: save_video(self.selected_file, self.filters)
            )
        else:
            save_btn = tk.Button(
                self.params_frame,
                text="Save",
                command=lambda: save_image(FRAME, self.filters)
            )
        save_btn.pack(anchor='s')

        if not self.playing: self.show_image(self.selected_file)
        self.params_frame.pack(fill="both")

    def build_filter_controls(self, filter_fn: Callable):
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        filter_name = filter_fn.__name__
        filter_params: Dict[str, int] = self.filters.params[filter_name]

        for param, value in filter_params.items():

            label = tk.Label(self.params_frame, text=param)
            label.pack()

            param_controls_grid = tk.Frame(self.params_frame)
            param_controls_grid.grid_rowconfigure(0, weight=1)
            param_controls_grid.grid_columnconfigure(0, weight=1)
            param_controls_grid.grid_columnconfigure(1, weight=1)
            param_controls_grid.grid_columnconfigure(2, weight=1)

            # (Return)
            validate_int_entry = self.root.register(
                lambda s: s in ("", "-") or s.lstrip("-").isdigit()
            )
            param_entry = tk.Entry(
                param_controls_grid,
                width=5,
                textvariable=tk.IntVar(value=value),
                justify="center",
                validate="key",
                validatecommand=(validate_int_entry, "%P")
            )
            param_entry.bind("<Return>",
                             lambda event,f=filter_name, p=param, e=param_entry:
                             self.mod_filter_param(filter_name=f, param=p, entry=e))
            param_entry.grid(row=0, column=1)

            # (-)
            minus_btn = tk.Button(
                param_controls_grid,
                text="-",
                command=(
                    lambda f=filter_name, e=param_entry, p=param:
                        self.mod_filter_param(filter_name=f, param=p, signal="-", entry=e)
                )
            )
            minus_btn.grid(row=0, column=0, sticky="ew")

            # (+)
            plus_btn = tk.Button(
                param_controls_grid,
                text="+",
                command=(
                    lambda f=filter_name, e=param_entry, p=param:
                        self.mod_filter_param(filter_name=f, param=p, signal="+", entry=e)
                )
            )
            plus_btn.grid(row=0, column=2, sticky="ew")

            # Pack
            param_controls_grid.pack(padx=30, pady=PADY)

    def mod_filter_param(self, filter_name: str, param: str, signal: str|None=None, entry: tk.Entry|None=None) -> None:
        if signal == "-":
            value = self.filters.params[filter_name][param] - 1

        elif signal == "+":
            value = self.filters.params[filter_name][param] + 1

        else:
            value = int(entry.get())

        int_var = tk.IntVar(name=entry["textvariable"])

        self.filters.set_param(filter_name, param, value)
        new_value = self.filters.params[filter_name][param]
        int_var.set(new_value)
        self.show_image(self.selected_file)


def main():

    filters = Filters()

    gui = GUI(filters)

    gui.root.mainloop()


if __name__ == "__main__":
    main()