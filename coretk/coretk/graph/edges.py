import logging
import tkinter as tk
from tkinter.font import Font

from coretk import themes
from coretk.dialogs.linkconfig import LinkConfiguration
from coretk.graph import tags
from coretk.nodeutils import NodeUtils

TEXT_DISTANCE = 0.30


class CanvasWirelessEdge:
    def __init__(self, token, position, src, dst, canvas):
        self.token = token
        self.src = src
        self.dst = dst
        self.canvas = canvas
        self.id = self.canvas.create_line(
            *position, tags=tags.WIRELESS_EDGE, width=1.5, fill="#009933"
        )

    def delete(self):
        self.canvas.delete(self.id)


class CanvasEdge:
    """
    Canvas edge class
    """

    width = 3

    def __init__(self, x1, y1, x2, y2, src, canvas):
        """
        Create an instance of canvas edge object
        :param int x1: source x-coord
        :param int y1: source y-coord
        :param int x2: destination x-coord
        :param int y2: destination y-coord
        :param int src: source id
        :param coretk.graph.graph.GraphCanvas canvas: canvas object
        """
        self.src = src
        self.dst = None
        self.src_interface = None
        self.dst_interface = None
        self.canvas = canvas
        self.id = self.canvas.create_line(
            x1, y1, x2, y2, tags=tags.EDGE, width=self.width, fill="#ff0000"
        )
        self.text_src = None
        self.text_dst = None
        self.token = None
        self.font = Font(size=8)
        self.link = None
        self.throughput = None
        self.set_binding()

    def set_binding(self):
        self.canvas.tag_bind(self.id, "<ButtonRelease-3>", self.create_context)

    def set_link(self, link):
        self.link = link
        self.draw_labels()

    def get_coordinates(self):
        x1, y1, x2, y2 = self.canvas.coords(self.id)
        v1 = x2 - x1
        v2 = y2 - y1
        ux = TEXT_DISTANCE * v1
        uy = TEXT_DISTANCE * v2
        x1 = x1 + ux
        y1 = y1 + uy
        x2 = x2 - ux
        y2 = y2 - uy
        return x1, y1, x2, y2

    def draw_labels(self):
        x1, y1, x2, y2 = self.get_coordinates()
        label_one = None
        if self.link.HasField("interface_one"):
            label_one = (
                f"{self.link.interface_one.ip4}/{self.link.interface_one.ip4mask}\n"
                f"{self.link.interface_one.ip6}/{self.link.interface_one.ip6mask}\n"
            )
        label_two = None
        if self.link.HasField("interface_two"):
            label_two = (
                f"{self.link.interface_two.ip4}/{self.link.interface_two.ip4mask}\n"
                f"{self.link.interface_two.ip6}/{self.link.interface_two.ip6mask}\n"
            )
        self.text_src = self.canvas.create_text(
            x1,
            y1,
            text=label_one,
            justify=tk.CENTER,
            font=self.font,
            tags=tags.LINK_INFO,
        )
        self.text_dst = self.canvas.create_text(
            x2,
            y2,
            text=label_two,
            justify=tk.CENTER,
            font=self.font,
            tags=tags.LINK_INFO,
        )

    def update_labels(self):
        """
        Move edge labels based on current position.

        :return: nothing
        """
        x1, y1, x2, y2 = self.get_coordinates()
        self.canvas.coords(self.text_src, x1, y1)
        self.canvas.coords(self.text_dst, x2, y2)

    def complete(self, dst):
        self.dst = dst
        self.token = tuple(sorted((self.src, self.dst)))
        x, y = self.canvas.coords(self.dst)
        x1, y1, _, _ = self.canvas.coords(self.id)
        self.canvas.coords(self.id, x1, y1, x, y)
        self.check_wireless()
        self.canvas.tag_raise(self.src)
        self.canvas.tag_raise(self.dst)

    def check_wireless(self):
        src_node = self.canvas.nodes[self.src]
        dst_node = self.canvas.nodes[self.dst]
        src_node_type = src_node.core_node.type
        dst_node_type = dst_node.core_node.type
        is_src_wireless = NodeUtils.is_wireless_node(src_node_type)
        is_dst_wireless = NodeUtils.is_wireless_node(dst_node_type)
        if is_src_wireless or is_dst_wireless:
            self.canvas.itemconfig(self.id, state=tk.HIDDEN)
            self._check_antenna()

    def _check_antenna(self):
        src_node = self.canvas.nodes[self.src]
        dst_node = self.canvas.nodes[self.dst]
        src_node_type = src_node.core_node.type
        dst_node_type = dst_node.core_node.type
        is_src_wireless = NodeUtils.is_wireless_node(src_node_type)
        is_dst_wireless = NodeUtils.is_wireless_node(dst_node_type)
        if is_src_wireless or is_dst_wireless:
            if is_src_wireless and not is_dst_wireless:
                dst_node.add_antenna()
            elif not is_src_wireless and is_dst_wireless:
                src_node.add_antenna()
            # TODO: remove this? dont allow linking wireless nodes?
            else:
                src_node.add_antenna()

    def delete(self):
        self.canvas.delete(self.id)
        if self.link:
            self.canvas.delete(self.text_src)
            self.canvas.delete(self.text_dst)

    def create_context(self, event):
        logging.debug("create link context")
        context = tk.Menu(self.canvas)
        themes.style_menu(context)
        context.add_command(label="Configure", command=self.configure)
        context.add_command(label="Delete")
        context.add_command(label="Split")
        context.add_command(label="Merge")
        if self.canvas.app.core.is_runtime():
            context.entryconfigure(1, state="disabled")
            context.entryconfigure(2, state="disabled")
            context.entryconfigure(3, state="disabled")
        context.post(event.x_root, event.y_root)

    def configure(self):
        logging.debug("link configuration")
        dialog = LinkConfiguration(self.canvas, self.canvas.app, self)
        dialog.show()
