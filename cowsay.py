from tempfile import mkstemp
from telex import plugin
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

import tgl
import os


class CowsayPlugin(plugin.TelexPlugin):
    """
    Renders text in a PIL generated image with monospace text.
    Also includes cowsay and tux ascii art to render text in.
    """

    patterns = {
        "^{prefix}monospaced (.+)$": "cowsay",
        "^{prefix}cowsay (.+)$": "cowsay",
        "^{prefix}tuxsay (.+)$": "tuxsay",
    }

    usage = [
        "{prefix}monospaced (text): Renders text in an image with monospace font.",
        "{prefix}cowsay (text): Renders text in an cowsay image with monospace font.",
        "{prefix}tuxsay (text): Renders text in an cowsay -f tux image with monospace font.",
    ]

    def do_cowsay(self, text, length=40, tux=False):
        if tux:
            return self.build_bubble(text, length) + self.build_tux()

        return self.build_bubble(text, length) + self.build_cow()

    def build_cow(self):
        return """
         \   ^__^
          \  (oo)\_______
             (__)\       )\/\\
                 ||----w |
                 ||     ||
        """

    def build_tux(self):
        return """
     \\
      \\
        .--.
       |o_o |
       |:_/ |
      //   \ \
     (|     | )
    /'\_   _/`\\
    \___)=(___/)
        """

    def build_bubble(self, text, length=40):
        bubble = []
        lines = self.normalize_text(text, length)
        bordersize = len(lines[0])
        bubble.append("  " + "_" * bordersize)

        for index, line in enumerate(lines):
            border = self.get_border(lines, index)
            bubble.append("%s %s %s" % (border[0], line, border[1]))

        bubble.append("  " + "-" * bordersize)

        return "\n".join(bubble)

    def normalize_text(self, text, length):
        lines = wrap(text, length)
        maxlen = len(max(lines, key=len))
        return [line.ljust(maxlen) for line in lines]

    def get_border(self, lines, index):
        if len(lines) < 2:
            return ["<", ">"]

        elif index == 0:
            return ["/", "\\"]

        elif index == len(lines) - 1:
            return ["\\", "/"]

        else:
            return ["|", "|"]

    def text2png(self, msg, text, color="#888", bgcolor="#000", fontfullpath=None, fontsize=13,
                 leftpadding=3, rightpadding=3, width=80):
        font = ImageFont.load_default() if fontfullpath is None else ImageFont.truetype(fontfullpath, fontsize)

        lines = []
        for line in text.splitlines():
            if line.strip() != '':
                lines += wrap(line, width, break_long_words=True, replace_whitespace=False)

        line_height = font.getsize(text)[1]
        img_height = line_height * (len(lines) + 1)
        width = ((width + 10) * line_height) // 2

        img = Image.new("RGBA", (width, img_height), bgcolor)
        draw = ImageDraw.Draw(img)

        y = 0
        for line in lines:
            draw.text((leftpadding, y), line, color, font=font)
            y += line_height

        filename = mkstemp(suffix='png', prefix="telex-cowsayplugin-")
        img.save(filename, 'png')

        peer = self.bot.get_peer_to_send(msg)

        def cleanup_cb(success, msg):
            if success:
                os.remove(filename)
            else:
                return "Cowsay: something went wrong."

        tgl.send_photo(peer, filename, cleanup_cb)

    def monospaced(self, msg, matches):
        text = matches.group(1)
        self.text2png(msg, text)

    def cowsay(self, msg, matches):
        text = matches.group(1)
        self.text2png(msg, self.do_cowsay(text), width=50)

    def tuxsay(self, msg, matches):
        text = matches.group(1)
        self.text2png(msg, self.do_cowsay(text, tux=True), width=50)
