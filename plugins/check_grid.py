"""
KiCad 9/10 Action Plugin: Grid Checker
Checks vias and components against a user-defined grid
"""

import os
import pcbnew

MARKER_LAYER = pcbnew.User_9
MARKER_RADIUS_MM = 0.5
VIA_COLOR = pcbnew.COLOR4D(1.0, 0.0, 0.0, 1.0)
COMPONENT_COLOR = pcbnew.COLOR4D(0.0, 0.0, 1.0, 1.0)


class CheckGridPlugin(pcbnew.ActionPlugin):
    """Plugin to find and highlight vias and components not on a specified grid"""

    def __init__(self):
        super().__init__()
        self.markers = []

    def defaults(self):
        self.name = "Grid Checker"
        self.category = "Grid Tools"
        self.description = "Check vias and/or components against custom grid"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.png")

    def is_on_grid(self, value_mm, grid_size):
        """Check if a value in mm is on the specified grid"""
        grid_units = value_mm / grid_size
        return abs(grid_units - round(grid_units)) < 1e-6

    def clear_markers(self, board):
        """Remove all markers from the marker layer"""
        for marker in self.markers:
            try:
                board.Remove(marker)
            except Exception:
                pass
        self.markers.clear()

        to_remove = [d for d in board.GetDrawings()
                     if d.GetLayer() == MARKER_LAYER]
        for drawing in to_remove:
            try:
                board.Remove(drawing)
            except Exception:
                pass

    def create_marker(self, board, position, color):
        """Create a filled circle marker at the given position on the marker layer"""
        circle = pcbnew.PCB_SHAPE(board)
        circle.SetShape(pcbnew.SHAPE_T_CIRCLE)
        circle.SetCenter(position)
        circle.SetEnd(pcbnew.VECTOR2I(position.x + pcbnew.FromMM(MARKER_RADIUS_MM), position.y))
        circle.SetFilled(True)
        circle.SetFillColor(color)
        circle.SetLayer(MARKER_LAYER)
        board.Add(circle)
        self.markers.append(circle)

    def find_off_grid(self, items, grid_size, strict):
        """Check items against grid. Returns list of off-grid items."""
        off_grid = []
        for item in items:
            pos = item.GetPosition()
            x_on = self.is_on_grid(pcbnew.ToMM(pos.x), grid_size)
            y_on = self.is_on_grid(pcbnew.ToMM(pos.y), grid_size)
            is_off = not (x_on and y_on) if strict else not (x_on or y_on)
            if is_off:
                off_grid.append(item)
        return off_grid

    def get_vias(self, board):
        """Extract vias from the board's track list"""
        return [t for t in board.GetTracks()
                if type(t).__name__ == "PCB_VIA"]

    def format_result(self, label, total, off_grid_count, grid_size):
        """Format a result line for the report"""
        if off_grid_count > 0:
            return f"{label}: {off_grid_count} off-grid out of {total} total"
        return f"{label}: All {total} on {grid_size}mm grid"

    def update_selection(self, board, off_grid_items):
        """Clear current selection and select off-grid items"""
        for track in board.GetTracks():
            try:
                track.ClearSelected()
            except Exception:
                pass
        for fp in board.GetFootprints():
            try:
                fp.ClearSelected()
            except Exception:
                pass
        for item in off_grid_items:
            try:
                item.SetSelected()
            except Exception:
                pass

    def get_user_options(self):
        """Show options dialog. Returns dict or None if cancelled."""
        import wx

        dlg = wx.Dialog(None, title="Grid Checker", size=(450, 400))
        try:
            main_sizer = wx.BoxSizer(wx.VERTICAL)

            # Grid size
            grid_box = wx.StaticBox(dlg, label="Grid Size")
            grid_sizer = wx.StaticBoxSizer(grid_box, wx.VERTICAL)
            grid_sizer.Add(wx.StaticText(dlg, label="Grid size in mm:"), 0, wx.ALL, 5)
            grid_text = wx.TextCtrl(dlg, value="0.5")
            grid_sizer.Add(grid_text, 0, wx.ALL | wx.EXPAND, 5)
            main_sizer.Add(grid_sizer, 0, wx.ALL | wx.EXPAND, 10)

            # What to check
            check_box = wx.StaticBox(dlg, label="What to Check")
            check_sizer = wx.StaticBoxSizer(check_box, wx.VERTICAL)
            via_check = wx.CheckBox(dlg, label="Check Vias")
            via_check.SetValue(True)
            check_sizer.Add(via_check, 0, wx.ALL, 5)
            component_check = wx.CheckBox(dlg, label="Check Components (Footprints)")
            component_check.SetValue(True)
            check_sizer.Add(component_check, 0, wx.ALL, 5)
            marker_check = wx.CheckBox(dlg, label="Add markers on User.9 layer")
            marker_check.SetValue(True)
            check_sizer.Add(marker_check, 0, wx.ALL, 5)
            main_sizer.Add(check_sizer, 0, wx.ALL | wx.EXPAND, 10)

            # Strictness
            strict_box = wx.StaticBox(dlg, label="Grid Requirements")
            strict_sizer = wx.StaticBoxSizer(strict_box, wx.VERTICAL)
            strict_check = wx.CheckBox(dlg, label="Both X and Y must be on grid (strict)")
            strict_check.SetValue(True)
            strict_sizer.Add(strict_check, 0, wx.ALL, 5)
            help_text = wx.StaticText(dlg, label="When unchecked, only flags items where neither axis is on grid.")
            help_text.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
            strict_sizer.Add(help_text, 0, wx.ALL, 5)
            main_sizer.Add(strict_sizer, 0, wx.ALL | wx.EXPAND, 10)

            # Buttons
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            clear_btn = wx.Button(dlg, wx.ID_ANY, "Clear Markers")
            button_sizer.Add(clear_btn, 0, wx.ALL, 5)
            button_sizer.Add(wx.Button(dlg, wx.ID_OK, "Run Check"), 0, wx.ALL, 5)
            button_sizer.Add(wx.Button(dlg, wx.ID_CANCEL, "Cancel"), 0, wx.ALL, 5)
            main_sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)

            dlg.SetSizer(main_sizer)

            def on_clear_markers(event):
                board = pcbnew.GetBoard()
                if not board:
                    return
                self.clear_markers(board)
                pcbnew.Refresh()

            clear_btn.Bind(wx.EVT_BUTTON, on_clear_markers)
            dlg.Fit()
            dlg.Center()

            if dlg.ShowModal() != wx.ID_OK:
                return None

            try:
                grid_size = float(grid_text.GetValue().strip())
                if grid_size <= 0:
                    raise ValueError
            except ValueError:
                self.show_message("Invalid grid size. Please enter a positive number.", "Error", is_error=True)
                return None

            if not via_check.GetValue() and not component_check.GetValue():
                self.show_message("Please select at least one option (Vias or Components).", "Error", is_error=True)
                return None

            return {
                "grid_size": grid_size,
                "check_vias": via_check.GetValue(),
                "check_components": component_check.GetValue(),
                "create_markers": marker_check.GetValue(),
                "strict": strict_check.GetValue(),
            }
        finally:
            dlg.Destroy()

    def Run(self):
        """Main plugin execution"""
        try:
            options = self.get_user_options()
            if options is None:
                return

            grid_size = options["grid_size"]
            strict = options["strict"]
            create_markers = options["create_markers"]

            board = pcbnew.GetBoard()
            if not board:
                self.show_message("No board loaded!", "Error", is_error=True)
                return

            if create_markers:
                self.clear_markers(board)

            off_grid_items = []
            total_checked = 0
            message_parts = []

            # Check vias
            if options["check_vias"]:
                vias = self.get_vias(board)
                off_grid_vias = self.find_off_grid(vias, grid_size, strict)
                off_grid_items.extend(off_grid_vias)
                total_checked += len(vias)
                message_parts.append(self.format_result("Vias", len(vias), len(off_grid_vias), grid_size))
                print(f"Grid Checker: {len(off_grid_vias)}/{len(vias)} vias off-grid")

                if create_markers:
                    for via in off_grid_vias:
                        self.create_marker(board, via.GetPosition(), VIA_COLOR)

            # Check components
            if options["check_components"]:
                footprints = list(board.GetFootprints())
                off_grid_fps = self.find_off_grid(footprints, grid_size, strict)
                off_grid_items.extend(off_grid_fps)
                total_checked += len(footprints)
                message_parts.append(self.format_result("Components", len(footprints), len(off_grid_fps), grid_size))
                print(f"Grid Checker: {len(off_grid_fps)}/{len(footprints)} components off-grid")

                if create_markers:
                    for fp in off_grid_fps:
                        self.create_marker(board, fp.GetPosition(), COMPONENT_COLOR)

            self.update_selection(board, off_grid_items)
            pcbnew.Refresh()

            # Build results message
            if total_checked == 0:
                message = "No items found to check."
            else:
                grid_mode = "strict" if strict else "lenient"
                message = f"Grid: {grid_size}mm ({grid_mode})\n\n"
                message += "\n".join(message_parts)
                if off_grid_items:
                    message += f"\n\n{len(off_grid_items)} off-grid items selected."
                    if create_markers:
                        message += f"\n{len(off_grid_items)} markers added to User.9 layer."
                        message += "\nEnable User.9 in the Layers panel to see them."

            self.show_message(message, "Grid Checker Results")

        except Exception as e:
            print(f"Grid Checker error: {e}")
            self.show_message(f"Plugin error: {e}", "Grid Checker Error", is_error=True)

    def show_message(self, message, title, is_error=False):
        """Display a message dialog"""
        try:
            import wx
            icon = wx.ICON_ERROR if is_error else wx.ICON_INFORMATION
            dlg = wx.MessageDialog(None, message, title, wx.OK | icon)
            dlg.ShowModal()
            dlg.Destroy()
        except ImportError:
            print(f"{title}: {message}")


CheckGridPlugin().register()
