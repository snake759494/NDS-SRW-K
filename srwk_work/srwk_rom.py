# -*- coding: utf-8 -*-
"""srwk_rom.py — thin ndspy wrapper for reading/replacing files in the SRW K rom."""
import os
import ndspy.rom

def _names(rom):
    names = {}
    def rec(folder, prefix):
        for i, fname in enumerate(folder.files):
            names[folder.firstID + i] = prefix + fname
        for sub_name, sub in folder.folders:
            rec(sub, prefix + sub_name + "/")
    rec(rom.filenames, "")
    return names

class Rom:
    def __init__(self, path):
        self.path = path
        self.rom = ndspy.rom.NintendoDSRom.fromFile(path)
        self.names = _names(self.rom)
        self.ids = {v: k for k, v in self.names.items()}

    def get(self, name):
        return self.rom.files[self.ids[name]]

    def set(self, name, data):
        self.rom.files[self.ids[name]] = data

    def set_arm9(self, data):
        self.rom.arm9 = data

    def get_arm9(self):
        return self.rom.arm9

    def set_overlay_file(self, file_id, data):
        # overlay files are stored as files 0..91
        self.rom.files[file_id] = data

    def save(self, out_path):
        self.rom.saveToFile(out_path)


class _Extracted:
    """Directory-backed stand-in for `Rom`, reading the trees extract_roms.py makes.

    The injectors only ever call .get(), so once jp/ and kr/ exist the graphics
    steps no longer need the ROMs themselves."""
    def __init__(self, root):
        self.root = root

    def get(self, name):
        with open(os.path.join(self.root, name), "rb") as f:
            return f.read()


def open_rom(path, extract_dir=None):
    """Rom(path) if the ROM is there, else the matching extract_roms.py tree."""
    if os.path.exists(path):
        return Rom(path)
    if extract_dir and os.path.isdir(extract_dir):
        return _Extracted(extract_dir)
    raise FileNotFoundError(
        f"{path} not found and no extracted tree at {extract_dir!r} — "
        "run extract_roms.py (see docs/BUILD.md)")
