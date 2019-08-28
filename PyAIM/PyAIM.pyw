import tkinter
from tkinter import messagebox
from tkinter import ttk
import pymem
import os
import math

TITLE = "PyAIM"


def MsgError(title=TITLE, msg="undefined error"):
    root.withdraw()
    messagebox.showerror(title, msg)
    raise SystemExit(1)


class CGame:
    def __init__(self):
        try:
            self.process = pymem.Pymem("gta_sa.exe")
            self.samp_base_address = pymem.process.module_from_name(self.process.process_handle, "samp.dll").lpBaseOfDll
            if self.samp_base_address == 0:
                MsgError(msg="samp.dll not found!")

            pSAMPInfo = self.process.read_ulong(self.samp_base_address + 0x21A0F8)
            if pSAMPInfo == 0:
                MsgError(msg="pSAMPInfo\nPointer for samp struct is null")

            self.pPresets = self.process.read_ulong(pSAMPInfo + 0x3C5)
            if self.pPresets == 0:
                MsgError(msg="pPresets\nPointer for samp struct is null")

            pPools = self.process.read_ulong(pSAMPInfo + 0x3CD)
            if pPools == 0:
                MsgError(msg="pPools\nPointer for samp struct is null")

            pPlayer = self.process.read_ulong(pPools + 0x18)
            if pPlayer == 0:
                MsgError(msg="pPlayer\nPointer for samp struct is null")

            pLocalPlayer = self.process.read_ulong(pPlayer + 0x22)
            if pLocalPlayer == 0:
                MsgError(msg="pLocalPlayer\nPointer for samp struct is null")

            if self.process.read_int(pLocalPlayer + 0x0C) <= 0:
                MsgError(msg="Player is not active")

            self.extraWS_address_list = [0x5109AC, 0x5109C5, 0x5231A6, 0x52322D, 0x5233BA]
            self.extraWS_default_value = [None] * 5
            for i in range(5):
                self.extraWS_default_value[i] = self.process.read_uchar(self.extraWS_address_list[i])

            self.default_wallhack_dist = self.process.read_float(self.pPresets + 0x27)
        except pymem.exception.PymemError as e:
            MsgError(msg=e)

    # nop by SR_Team
    def spread(self, toggle: bool):
        try:
            if toggle is True:
                pymem.memory.write_bytes(self.process.process_handle, 0x740460, b"\x90\x90\x90", 3)
            else:
                pymem.memory.write_bytes(self.process.process_handle, 0x740460, b"\xD8\x48\x2C", 3)
        except pymem.exception.WinAPIError as e:
            messagebox.showerror(TITLE, e)

    def wallhack(self, toggle: bool, value: float):
        try:
            if toggle is True:
                self.process.write_uchar(self.pPresets + 0x2F, 0)
                self.process.write_float(self.pPresets + 0x27, value)
            else:
                self.process.write_uchar(self.pPresets + 0x2F, 1)
                self.process.write_float(self.pPresets + 0x27, value)
        except pymem.exception.MemoryWriteError as e:
            messagebox.showerror(TITLE, e)

    # by FYP
    def extraWS(self, toggle: bool):
        try:
            if toggle is True:
                for i in range(5):
                    self.process.write_uchar(self.extraWS_address_list[i], 235)
            else:
                for i in range(5):
                    self.process.write_uchar(self.extraWS_address_list[i], self.extraWS_default_value[i])
        except pymem.exception.MemoryWriteError as e:
            messagebox.showerror(TITLE, e)

    def aim(self):
        try:
            pPed = self.process.read_ulong(0xB6F5F0)
            if pPed == 0:
                return

            weapon_slot = self.process.read_uchar(pPed + 0x718)
            if weapon_slot != 2 and weapon_slot != 3 and weapon_slot != 4 and weapon_slot != 5 and weapon_slot != 6 and weapon_slot != 7:
                return

            pTarget = self.process.read_ulong(0xB6F3B8)
            if pTarget == 0:
                return

            pTargetPed = self.process.read_ulong(pTarget + 0x79C)
            if pTargetPed == 0:
                return

            pMatrix = self.process.read_ulong(pTargetPed + 0x14)
            if pMatrix == 0:
                return

            if self.process.read_float(pTargetPed + 0x540) > 0:
                fCamPos = [self.process.read_float(0xB6F9CC), self.process.read_float(0xB6F9D0)]

                '''
                offsetPos = [0x30] * 3
                fPos = [None] * 3
                for i in range(3):
                    offsetPos[i] += (0x4 * i)
                    fPos[i] = self.process.read_float(pMatrix + offsetPos[i])
                '''

                fPos = [self.process.read_float(pMatrix + 0x30), self.process.read_float(pMatrix + 0x34)]

                aa = abs(fCamPos[0] - fPos[0])
                ab = abs(fCamPos[1] - fPos[1])
                ac = math.sqrt(aa * aa + ab * ab)

                alpha = math.asin(aa / ac)
                beta = math.acos(aa / ac)

                if fCamPos[0] > fPos[0] and fCamPos[1] < fPos[1]:
                    beta = -beta
                elif fCamPos[0] > fPos[0] and fCamPos[1] > fPos[1]:
                    pass
                elif fCamPos[0] < fPos[0] and fCamPos[1] > fPos[1]:
                    beta = alpha + (math.pi / 2)
                elif fCamPos[0] < fPos[0] and fCamPos[1] < fPos[1]:
                    beta = -alpha - (math.pi / 2)

                if weapon_slot == 5:
                    beta += 0.027
                elif weapon_slot == 6:
                    beta += 0.0185
                else:
                    beta += 0.040

                self.process.write_float(0xB6F258, beta)
        except pymem.exception.PymemMemoryError:
            pass


class Main(tkinter.Frame):
    def __init__(self, root):
        super().__init__(root)

        self.game = CGame()

        self.string_aim = tkinter.StringVar()
        self.string_aim.set("AimBot: off")

        self.string_spread = tkinter.StringVar()
        self.string_spread.set("NoSpread: off")

        self.string_wallhack = tkinter.StringVar()
        self.string_wallhack.set("WallHack: off")

        self.string_extraWS = tkinter.StringVar()
        self.string_extraWS.set("ExtraWS: off")

        self.wallhack_dist = tkinter.IntVar()
        self.wallhack_dist.set(self.game.default_wallhack_dist)

        self.toggle_aim = tkinter.BooleanVar()
        self.toggle_aimbot = False

        self.toggle_spread = tkinter.BooleanVar()
        self.toggle_wallhack = tkinter.BooleanVar()
        self.toggle_extraWS = tkinter.BooleanVar()

        self.initMain()
        self.update()
        root.protocol("WM_DELETE_WINDOW", self.destructor)

    def update(self):
        if self.toggle_aimbot is True:
            self.game.aim()

        root.after(10, self.update)

    def destructor(self):
        root.destroy()
        try:
            if pymem.Pymem("gta_sa.exe").process_id > 0:
                self.game.spread(False)
                self.game.wallhack(False, self.game.default_wallhack_dist)
                self.game.extraWS(False)
        except pymem.exception.ProcessNotFound:
            pass

    def initMain(self):
        main_frame = tkinter.Frame()
        main_frame.pack(side=tkinter.TOP, anchor=tkinter.W)

        label_frame = [ttk.LabelFrame(main_frame, text="functions"), ttk.LabelFrame(main_frame, text="status")]
        label_frame[0].pack(padx=6, pady=5, side=tkinter.LEFT)
        label_frame[1].pack(padx=2, pady=5)

        ttk.Checkbutton(label_frame[0], text="AimBot", variable=self.toggle_aim, onvalue=True, offvalue=False).pack(padx=3, pady=1, anchor=tkinter.W)
        ttk.Checkbutton(label_frame[0], text="NoSpread", variable=self.toggle_spread, onvalue=True, offvalue=False).pack(padx=3, pady=1, anchor=tkinter.W)
        ttk.Checkbutton(label_frame[0], text="ExtraWS", variable=self.toggle_extraWS, onvalue=True, offvalue=False).pack(padx=3, pady=1, anchor=tkinter.W)

        wallhack_frame = ttk.LabelFrame(label_frame[0], text="WallHack")
        wallhack_frame.pack(padx=5, pady=5)

        ttk.Checkbutton(wallhack_frame, text="on/off", variable=self.toggle_wallhack, onvalue=True, offvalue=False).pack(padx=3, pady=1, anchor=tkinter.W)
        ttk.LabeledScale(wallhack_frame, variable=self.wallhack_dist, from_=0, to=999, compound=tkinter.BOTTOM).pack(padx=3, pady=3)
        self.wallhack_dist.set(self.game.default_wallhack_dist)

        ttk.Button(label_frame[0], text="toggle", width=17, command=self.cheatToggle).pack(padx=3, pady=3)

        ttk.Label(label_frame[1], textvariable=self.string_aim).pack(padx=3, pady=1, anchor=tkinter.W)
        ttk.Label(label_frame[1], textvariable=self.string_spread).pack(padx=3, pady=1, anchor=tkinter.W)
        ttk.Label(label_frame[1], textvariable=self.string_extraWS).pack(padx=3, pady=1, anchor=tkinter.W)
        ttk.Label(label_frame[1], textvariable=self.string_wallhack).pack(padx=3, pady=1, anchor=tkinter.W)

    def cheatToggle(self):
        if self.toggle_aim.get() is True:
            self.toggle_aimbot = True
            self.string_aim.set("AimBot: on")
        else:
            self.toggle_aimbot = False
            self.string_aim.set("AimBot: off")

        if self.toggle_spread.get() is True:
            self.game.spread(True)
            self.string_spread.set("NoSpread: on")
        else:
            self.game.spread(False)
            self.string_spread.set("NoSpread: off")

        if self.toggle_wallhack.get() is True:
            self.game.wallhack(True, float(self.wallhack_dist.get()))
            self.string_wallhack.set("WallHack: on")
        else:
            self.game.wallhack(False, self.game.default_wallhack_dist)
            self.string_wallhack.set("WallHack: off")

        if self.toggle_extraWS.get() is True:
            self.game.extraWS(True)
            self.string_extraWS.set("ExtraWS: on")
        else:
            self.game.extraWS(False)
            self.string_extraWS.set("ExtraWS: off")


def go_to_group():
    answer = messagebox.askyesno(TITLE, "PyAIM by Alferov\n\nGo to vk.com group?")
    if answer is True:
        os.system("start https://vk.com/alferov_cheats")


if __name__ == "__main__":
    pymem.logger.setLevel(pymem.logging.NOTSET)

    root = tkinter.Tk()
    app = Main(root)
    app.pack()

    logo = tkinter.PhotoImage(data='''
        iVBORw0KGgoAAAANSUhEUgAAAFAAAABQBAMAAAB8P++eAAAAJ1BMVEUAAAAblwsQWgYKPAQAAAAblwsAAAAblwv/AAAlAAB7AACq
        AADcAACYVyozAAAACHRSTlMA/lkVjJ7MzdK/6N4AAAM/SURBVEjHxJTNasMwDMdDTdh1yjC+dh4hV61l7DXmBtPXmDPy/lMiXLPE
        Vg09TIcQm5++/pbd7E05jU2NHQC+/gVU/RXAXO5WeXawmj7fSUscmzmKIHMcUyKHJZQHmAP9dFK/xKxdqwGE3hUlnpDlWUgtBDQY
        dVSuHPIVYEyCt8UqVaBkEWS/fOMtAQnkdSGz/nvWLpc77SfwCQzmSrxl6j1Gjxx42PuHbJEfoPdVv2TAd+jkreT+HKtNguXBWNAw
        YSxb77CTDTBZa4+r0D8E0aIHY98KE9stofnLZjbgba5XH5NAKICdAMqp9VZuH2D23nMzIzVDiysYP27bRkc3RakkDyKeQIuCN6Lg
        9UfY5obiu3rM5MG9RFfAqqvwCbr6cj12XZXbPgAGH3lSmNAVjxSP0PxbXB2stg0EAQAdIjffYbYhYJ0ECgX3JKxSUHQuvRofAia6
        9h9WuzqESpjV1SlBFjmKsr2XRQ35qM6sIhwFJ9YtBmnl4WF7xrOzY8YeEhqQRwcplZp6H4+Pb0dGMzgjhz0dH+McgPOdVJf+EcmQ
        /mDeuxzDH8ZBqtHhiez7AB449rFffY8uoAsoSCIqy9V54UQBOFG5YesAKFTgtTnD1cOHxTq4KKDi3CTphc5honl21eZwgiGpOM+u
        cV3gm02bxylB0cHTlvO7F5AXGPzdQ9nBz9zGhvAOoengQy1j8QmBm9WVhRjaqYe6jmWtd1l9/wSbmbyUUbYEVy5UBxv2URnGYsGq
        XbZKejhHdikDhGEPwVEGoIPLZ/Dr47WYjoFf9H3qHYczLJY2MPiNCJk3hJR1qNoGBlmHmHVOWe8hFdxL+BbhszrmWMdtjIEBlEHM
        b8ZBN1sehjLawz8lQhlQMqWyEEOh+lcGsXgs5gT1bWLL08N9eXzM2sfy6FsLq0aZw7CvY9VYqP5i6E2ojIX45du3YZJaGIv2BuFs
        AH8yRrDrnljMqHtcmS3pnxnAuv5F0PajcGVE/TjHClIdB5DzlKDtcPy8K+rw01ZMCYrpa/C8pT3TTHQKBA28Bs/0tuJZflIZsPsa
        JoUHdIsWa9rTIYDd17TdcbMHEK2eJgWgo5tjp0Q/LWwAcMVl/Os/8OsOGcYhtIcAAAAASUVORK5CYII=''')

    btn_logo = tkinter.Button(root, image=logo, bd=0, cursor="heart", command=go_to_group)
    btn_logo.pack()
    btn_logo.place(x=140, y=130)

    window_size = [230, 235]
    window_pos = [int(root.winfo_screenwidth() / 2 - (window_size[0] / 2)), int(root.winfo_screenheight() / 2 - (window_size[1] / 2))]

    root.title(TITLE)
    root.geometry(f"{window_size[0]}x{window_size[1]}+{window_pos[0]}+{window_pos[1]}")
    root.resizable(False, False)
    root.attributes("-alpha", 0.96)
    root.mainloop()
