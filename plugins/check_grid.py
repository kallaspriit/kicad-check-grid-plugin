"""
KiCad 9 Action Plugin: Grid Checker
Checks vias and components against a user-defined grid
"""

import math
import pcbnew


class CheckGridPlugin(pcbnew.ActionPlugin):
    """Plugin to find and highlight vias and components that are not on a specified grid"""
    
    def __init__(self):
        super().__init__()
        self.markers = []  # Store created markers for cleanup
    
    def defaults(self):
        """Set up plugin properties"""
        self.name = "Grid Checker"
        self.category = "Grid Tools"
        self.description = "Check vias and/or components against custom grid"
        self.show_toolbar_button = True
        self.icon_file_name = "icon.png"
    
    def is_on_grid(self, value_mm, grid_size):
        """Check if a value in mm is on the specified grid"""
        # Calculate how many grid units this value represents
        grid_units = value_mm / grid_size
        # Check if it's close to a whole number (within tolerance)
        return abs(grid_units - round(grid_units)) < 1e-6
    
    def clear_existing_markers(self, board):
        """Remove any existing markers from previous runs"""
        try:
            # Remove markers we created
            for marker in self.markers:
                try:
                    board.Remove(marker)
                except:
                    pass
            self.markers.clear()
            
            # Also try to remove any drawings on User.9 layer (our marker layer)
            drawings = board.GetDrawings()
            to_remove = []
            for drawing in drawings:
                try:
                    if drawing.GetLayer() == pcbnew.User_9:
                        to_remove.append(drawing)
                except:
                    pass
            
            for drawing in to_remove:
                try:
                    board.Remove(drawing)
                except:
                    pass
                    
        except Exception as e:
            print(f"Warning: Could not clear all markers: {e}")
    
    def create_marker(self, board, pos_mm, item_type, reference=""):
        """Create a visual marker at the specified position"""
        try:
            # Convert mm to KiCad internal units
            pos = pcbnew.VECTOR2I(pcbnew.FromMM(pos_mm[0]), pcbnew.FromMM(pos_mm[1]))
            
            # Create a filled circle marker
            circle = pcbnew.PCB_SHAPE(board)
            circle.SetShape(pcbnew.SHAPE_T_CIRCLE)
            circle.SetCenter(pos)
            circle.SetEnd(pcbnew.VECTOR2I(pos.x + pcbnew.FromMM(0.5), pos.y))  # 0.5mm radius
            circle.SetFilled(True)  # Make it filled
            
            # Set color based on item type
            if item_type == 'via':
                # Red filled circle for vias
                circle.SetFillColor(pcbnew.COLOR4D(1.0, 0.0, 0.0, 1.0))
            else:
                # Blue filled circle for components
                circle.SetFillColor(pcbnew.COLOR4D(0.0, 0.0, 1.0, 1.0))
            
            circle.SetLayer(pcbnew.User_9)  # Use User.9 layer
            
            # Add to board
            board.Add(circle)
            self.markers.append(circle)
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not create marker at {pos_mm}: {e}")
            return False
    
    def make_user9_visible(self):
        """Make User.9 layer visible so markers can be seen"""
        try:
            board = pcbnew.GetBoard()
            if not board:
                return
            
            # Get the layer settings
            layer_set = board.GetVisibleLayers()
            
            # Add User.9 layer to visible layers if not already visible
            if not layer_set.Contains(pcbnew.User_9):
                layer_set.addLayer(pcbnew.User_9)
                board.SetVisibleLayers(layer_set)
                print("Made User.9 layer visible to show markers")
                
        except Exception as e:
            print(f"Warning: Could not make User.9 layer visible: {e}")
    
    def get_user_options(self):
        """Get grid size and check options from user"""
        try:
            import wx
            
            # Create custom dialog
            dlg = wx.Dialog(None, title="Off-Grid Checker Options", size=(450, 400))
            
            # Main sizer
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Grid size section
            grid_box = wx.StaticBox(dlg, label="Grid Size")
            grid_sizer = wx.StaticBoxSizer(grid_box, wx.VERTICAL)
            
            grid_label = wx.StaticText(dlg, label="Enter grid size in mm (common values: 0.5, 0.25, 1.0):")
            grid_sizer.Add(grid_label, 0, wx.ALL, 5)
            
            grid_text = wx.TextCtrl(dlg, value="0.5")
            grid_sizer.Add(grid_text, 0, wx.ALL | wx.EXPAND, 5)
            
            main_sizer.Add(grid_sizer, 0, wx.ALL | wx.EXPAND, 10)
            
            # Check options section
            check_box = wx.StaticBox(dlg, label="What to Check")
            check_sizer = wx.StaticBoxSizer(check_box, wx.VERTICAL)
            
            via_check = wx.CheckBox(dlg, label="Check Vias")
            via_check.SetValue(True)  # Default to checked
            check_sizer.Add(via_check, 0, wx.ALL, 5)
            
            component_check = wx.CheckBox(dlg, label="Check Components (Footprints)")
            component_check.SetValue(False)  # Default to unchecked
            check_sizer.Add(component_check, 0, wx.ALL, 5)
            
            marker_check = wx.CheckBox(dlg, label="Create Visual Markers (persistent highlights)")
            marker_check.SetValue(True)  # Default to checked
            check_sizer.Add(marker_check, 0, wx.ALL, 5)
            
            main_sizer.Add(check_sizer, 0, wx.ALL | wx.EXPAND, 10)
            
            # Grid strictness section
            strict_box = wx.StaticBox(dlg, label="Grid Requirements")
            strict_sizer = wx.StaticBoxSizer(strict_box, wx.VERTICAL)
            
            strict_check = wx.CheckBox(dlg, label="Require BOTH X AND Y on grid")
            strict_check.SetValue(True)  # Default to strict (both coordinates must be on grid)
            strict_sizer.Add(strict_check, 0, wx.ALL, 5)
            
            help_text = wx.StaticText(dlg, label="Unchecked: Report items where NEITHER X nor Y is on grid\nChecked: Report items where X or Y (or both) is off grid")
            help_text.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
            strict_sizer.Add(help_text, 0, wx.ALL, 5)
            
            main_sizer.Add(strict_sizer, 0, wx.ALL | wx.EXPAND, 10)
            
            # Buttons
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            clear_btn = wx.Button(dlg, wx.ID_ANY, "Clear Markers")
            ok_btn = wx.Button(dlg, wx.ID_OK, "Run Check")
            cancel_btn = wx.Button(dlg, wx.ID_CANCEL, "Cancel")
            
            button_sizer.Add(clear_btn, 0, wx.ALL, 5)
            button_sizer.Add(ok_btn, 0, wx.ALL, 5)
            button_sizer.Add(cancel_btn, 0, wx.ALL, 5)
            
            main_sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
            
            dlg.SetSizer(main_sizer)
            
            # Bind clear button event
            def on_clear_markers(event):
                try:
                    board = pcbnew.GetBoard()
                    if board:
                        self.clear_existing_markers(board)
                        pcbnew.Refresh()
                        wx.MessageBox("All markers cleared from User.9 layer.", "Markers Cleared", wx.OK | wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("No board loaded!", "Error", wx.OK | wx.ICON_ERROR)
                except Exception as e:
                    wx.MessageBox(f"Error clearing markers: {e}", "Error", wx.OK | wx.ICON_ERROR)
            
            clear_btn.Bind(wx.EVT_BUTTON, on_clear_markers)
            
            # Ensure dialog fits content and center on screen
            dlg.Fit()
            dlg.Center()
            
            # Show dialog and get results
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    grid_size = float(grid_text.GetValue().strip())
                    if grid_size <= 0:
                        raise ValueError("Grid size must be positive")
                    
                    check_vias = via_check.GetValue()
                    check_components = component_check.GetValue()
                    create_markers = marker_check.GetValue()
                    require_both_on_grid = strict_check.GetValue()
                    
                    if not check_vias and not check_components:
                        dlg.Destroy()
                        self.show_message("Please select at least one option (Vias or Components).", "Error")
                        return None
                    
                    dlg.Destroy()
                    return {
                        'grid_size': grid_size,
                        'check_vias': check_vias,
                        'check_components': check_components,
                        'create_markers': create_markers,
                        'require_both_on_grid': require_both_on_grid
                    }
                except ValueError:
                    dlg.Destroy()
                    self.show_message("Invalid grid size. Please enter a positive number.", "Error")
                    return None
            else:
                dlg.Destroy()
                return None  # User cancelled
                
        except ImportError:
            # Fallback: use defaults if wx not available
            return {
                'grid_size': 0.5,
                'check_vias': True,
                'check_components': False,
                'create_markers': True,
                'require_both_on_grid': True
            }
    
    def Run(self):
        """Main plugin execution"""
        try:
            # Get options from user
            options = self.get_user_options()
            if options is None:
                return  # User cancelled or invalid input
            
            grid_size = options['grid_size']
            check_vias = options['check_vias']
            check_components = options['check_components']
            create_markers = options['create_markers']
            require_both_on_grid = options['require_both_on_grid']
            
            # Get the current board
            board = pcbnew.GetBoard()
            if not board:
                self.show_message("No board loaded!", "Error")
                return

            # Clear any existing markers from previous runs
            if create_markers:
                self.clear_existing_markers(board)

            off_grid_items = []
            all_items = []
            results = {}
            markers_created = 0  # Track how many markers we create            # Check vias if requested
            if check_vias:
                print("=== CHECKING VIAS ===")
                all_tracks = board.GetTracks()
                print(f"Total tracks found: {len(all_tracks)}")
                
                via_count = 0
                off_grid_via_count = 0
                
                for i, track in enumerate(all_tracks):
                    # Method 1: Check if this is a via using IsVia()
                    is_via_method1 = hasattr(track, 'IsVia') and track.IsVia()
                    
                    # Method 2: Check track type name
                    is_via_method2 = 'VIA' in type(track).__name__.upper()
                    
                    # Method 3: Check if it has via-specific attributes
                    is_via_method3 = hasattr(track, 'GetViaType')
                    
                    # Consider it a via if any method indicates it
                    if is_via_method1 or is_via_method2 or is_via_method3:
                        via_count += 1
                        pos = track.GetPosition()
                        x_mm = pcbnew.ToMM(pos.x)
                        y_mm = pcbnew.ToMM(pos.y)
                        
                        all_items.append(('via', x_mm, y_mm, track))
                        
                        x_on_grid = self.is_on_grid(x_mm, grid_size)
                        y_on_grid = self.is_on_grid(y_mm, grid_size)
                        
                        print(f"Via {via_count} at ({x_mm:.3f}, {y_mm:.3f}) mm")
                        print(f"  X on grid: {x_on_grid}, Y on grid: {y_on_grid}")
                        
                        # Apply grid checking based on strictness setting
                        is_off_grid = False
                        if require_both_on_grid:
                            # Strict mode: both X and Y must be on grid
                            is_off_grid = not (x_on_grid and y_on_grid)
                        else:
                            # Lenient mode: at least one of X or Y must be on grid
                            is_off_grid = not (x_on_grid or y_on_grid)
                        
                        if is_off_grid:
                            off_grid_items.append(track)
                            off_grid_via_count += 1
                            if require_both_on_grid:
                                print(f"  -> OFF GRID! (Both X and Y must be on grid)")
                            else:
                                print(f"  -> OFF GRID! (Neither X nor Y is on grid)")
                            
                            # Create marker if requested
                            if create_markers:
                                if self.create_marker(board, (x_mm, y_mm), 'via'):
                                    markers_created += 1
                
                results['vias'] = {'total': via_count, 'off_grid': off_grid_via_count}
                print(f"Total vias: {via_count}, Off-grid vias: {off_grid_via_count}")
            
            # Check components if requested
            if check_components:
                print("=== CHECKING COMPONENTS ===")
                all_footprints = board.GetFootprints()
                print(f"Total footprints found: {len(all_footprints)}")
                
                component_count = 0
                off_grid_component_count = 0
                
                for footprint in all_footprints:
                    component_count += 1
                    pos = footprint.GetPosition()
                    x_mm = pcbnew.ToMM(pos.x)
                    y_mm = pcbnew.ToMM(pos.y)
                    
                    all_items.append(('component', x_mm, y_mm, footprint))
                    
                    x_on_grid = self.is_on_grid(x_mm, grid_size)
                    y_on_grid = self.is_on_grid(y_mm, grid_size)
                    
                    ref = footprint.GetReference()
                    print(f"Component {ref} at ({x_mm:.3f}, {y_mm:.3f}) mm")
                    print(f"  X on grid: {x_on_grid}, Y on grid: {y_on_grid}")
                    
                    # Apply grid checking based on strictness setting
                    is_off_grid = False
                    if require_both_on_grid:
                        # Strict mode: both X and Y must be on grid
                        is_off_grid = not (x_on_grid and y_on_grid)
                    else:
                        # Lenient mode: at least one of X or Y must be on grid
                        is_off_grid = not (x_on_grid or y_on_grid)
                    
                    if is_off_grid:
                        off_grid_items.append(footprint)
                        off_grid_component_count += 1
                        if require_both_on_grid:
                            print(f"  -> OFF GRID! (Both X and Y must be on grid)")
                        else:
                            print(f"  -> OFF GRID! (Neither X nor Y is on grid)")
                        
                        # Create marker if requested
                        if create_markers:
                            if self.create_marker(board, (x_mm, y_mm), 'component', ref):
                                markers_created += 1
                
                results['components'] = {'total': component_count, 'off_grid': off_grid_component_count}
                print(f"Total components: {component_count}, Off-grid components: {off_grid_component_count}")
            
            # Clear all selections first - KiCad 9 compatible method
            for track in board.GetTracks():
                try:
                    track.ClearSelected()
                except:
                    pass
            
            for footprint in board.GetFootprints():
                try:
                    footprint.ClearSelected()
                except:
                    pass
            
            # Select the off-grid items using KiCad 9 method
            for item in off_grid_items:
                try:
                    item.SetSelected()
                except:
                    pass
            
            # Make User.9 layer visible if we created any markers
            if markers_created > 0:
                self.make_user9_visible()
            
            # Refresh the display
            pcbnew.Refresh()
            
            # Build results message
            message_parts = []
            
            if check_vias and 'vias' in results:
                via_total = results['vias']['total']
                via_off_grid = results['vias']['off_grid']
                if via_off_grid > 0:
                    message_parts.append(f"Vias: {via_off_grid} off-grid out of {via_total} total")
                else:
                    message_parts.append(f"Vias: All {via_total} are on {grid_size}mm grid ✓")
            
            if check_components and 'components' in results:
                comp_total = results['components']['total']
                comp_off_grid = results['components']['off_grid']
                if comp_off_grid > 0:
                    message_parts.append(f"Components: {comp_off_grid} off-grid out of {comp_total} total")
                else:
                    message_parts.append(f"Components: All {comp_total} are on {grid_size}mm grid ✓")
            
            # Add grid requirement info to message
            grid_mode = "Both X and Y must be on grid" if require_both_on_grid else "At least one of X or Y must be on grid"
            
            if off_grid_items:
                message = f"Off-Grid Items Found (Grid: {grid_size}mm):\n"
                message += f"Mode: {grid_mode}\n\n" + "\n".join(message_parts)
                message += f"\n\n{len(off_grid_items)} items have been selected (highlighted)."
                if create_markers:
                    message += "\n\nPersistent markers created on User.9 layer:"
                    message += "\n• Red filled circles (0.25mm) for off-grid vias"
                    message += "\n• Blue filled circles (0.25mm) for off-grid components"
                    message += "\n\nMarkers will remain visible while you work!"
                message += "\n\nCheck the console output for detailed positions."
            else:
                if len(all_items) == 0:
                    message = "No items found to check!"
                else:
                    message = f"Grid Check Complete (Grid: {grid_size}mm):\n"
                    message += f"Mode: {grid_mode}\n\n" + "\n".join(message_parts)
            
            self.show_message(message, "Off-Grid Vias Report")
            
        except Exception as e:
            error_msg = f"Plugin error: {str(e)}"
            print(error_msg)  # Log to console
            self.show_message(error_msg, "Plugin Error")
    
    def show_message(self, message, title):
        """Display a message to the user with fallback options"""
        try:
            # Try direct wx import (KiCad 9)
            import wx
            dlg = wx.MessageDialog(None, message, title, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        except ImportError:
            try:
                # Try pcbnew wx wrapper
                if hasattr(pcbnew, 'wx'):
                    pcbnew.wx.MessageBox(message, title)
                else:
                    print(f"{title}: {message}")
            except:
                print(f"{title}: {message}")


# Register the plugin with KiCad
CheckGridPlugin().register()
