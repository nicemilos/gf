"""Material color correction at load time; geometry and alpha stay intact."""
from PySide6.QtGui import QImage


def coat_pixels(image):
    """Ivory material inside the garment area; exclude face, skin and shoes."""
    data = image.constBits()
    width, height = image.width(), image.height()
    stride = image.bytesPerLine()
    for y in range(int(height * .45), int(height * .80)):
        for x in range(int(width * .32), int(width * .94)):
            if x > width * .74 and y < height * .57:
                continue
            offset = y * stride + x * 4
            r, g, b, a = data[offset:offset + 4]
            if a >= 240 and b > 140 and -5 <= r - g <= 38 and -5 <= g - b <= 38:
                yield offset, r, g, b


def coat_tone(image):
    channels = [[], [], []]
    for _, r, g, b in coat_pixels(image):
        if b >= 185 and r - g < 32 and g - b < 32:
            for values, value in zip(channels, (r, g, b)):
                values.append(value)
    if not channels[0]:
        raise ValueError('No ivory coat material found')
    return tuple(sorted(values)[int((len(values) - 1) * .8)] for values in channels)


def match_coat(image, reference_tone):
    image = image.convertToFormat(QImage.Format_RGBA8888)
    tone = coat_tone(image)
    shift = tuple(target - source for source, target in zip(tone, reference_tone))
    if shift == (0, 0, 0):
        return image
    result = image.copy()
    output = result.bits()
    for offset, r, g, b in coat_pixels(image):
        # Feather the material boundary in color space. Dark folds retain
        # their contrast and skin at the cuffs stays outside the correction.
        weight = min(1., (b - 140) / 45, (39 - (r - g)) / 7, (39 - (g - b)) / 7)
        for channel, value in enumerate((r, g, b)):
            output[offset + channel] = max(0, min(255, round(value + shift[channel] * weight)))
    return result
