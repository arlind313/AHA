"""Skeleton rig for S001 (adult Conor walking toward camera, Marbella) - joint positions in plate pixels.

Derived by hand from the approved Page 01 panel 1 (plate.png, 1080x1920). Image-left = Conor's right side.
Pose in the artwork: 'contact' - image-left leg forward (foot low), image-right leg back (foot high).
"""
J = {
    "crown": (530, 85), "head": (550, 200), "chin": (560, 300), "neck": (575, 350),
    "sh_L": (385, 440), "el_L": (370, 700), "wr_L": (360, 985), "hd_L": (370, 1120),
    "sh_R": (815, 430), "el_R": (860, 700), "wr_R": (880, 915), "hd_R": (820, 1085),
    "chest": (595, 620), "waist": (600, 925),
    "hip_L": (480, 1000), "kn_L": (500, 1360), "an_L": (530, 1700), "ft_L": (540, 1865),
    "hip_R": (730, 985), "kn_R": (680, 1320), "an_R": (650, 1545), "ft_R": (660, 1690),
}
BONES = [("crown", "head"), ("head", "chin"), ("chin", "neck"), ("neck", "chest"), ("chest", "waist"),
         ("neck", "sh_L"), ("sh_L", "el_L"), ("el_L", "wr_L"), ("wr_L", "hd_L"),
         ("neck", "sh_R"), ("sh_R", "el_R"), ("el_R", "wr_R"), ("wr_R", "hd_R"),
         ("waist", "hip_L"), ("hip_L", "kn_L"), ("kn_L", "an_L"), ("an_L", "ft_L"),
         ("waist", "hip_R"), ("hip_R", "kn_R"), ("kn_R", "an_R"), ("an_R", "ft_R"),
         ("sh_L", "chest"), ("sh_R", "chest"), ("hip_L", "hip_R")]
