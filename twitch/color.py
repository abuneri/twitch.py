class Color:
    def __init__(self, hex_rgb):
        self._red = None
        self._green = None
        self._blue = None
        self._hex = hex_rgb
        hex_rgb = hex_rgb.lstrip('#') if hex_rgb.startswith('#') else hex_rgb

        hex_parts = list(hex_rgb)
        parts_itr = iter(hex_parts)
        hex_components = [hex + next(parts_itr) for hex in parts_itr]
        if len(hex_components) != 3:
            raise ValueError(f'invalid hexadecimal color code {hex_rgb}')
        self._red = int(hex_components[0], 16)
        self._green = int(hex_components[1], 16)
        self._blue = int(hex_components[2], 16)

    @property
    def red(self):
        return self._red

    @ property
    def green(self):
        return self._green

    @property
    def blue(self):
        return self._blue

    @property
    def hex(self):
        return self._hex
