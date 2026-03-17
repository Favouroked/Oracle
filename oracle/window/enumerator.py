import Quartz
from typing import List
from oracle.models.data_models import WindowInfo

class WindowEnumerator:
    @staticmethod
    def get_active_windows() -> List[WindowInfo]:
        """
        Enumerates active/visible application windows on macOS using Quartz.
        """
        # Options for window listing
        # kCGWindowListOptionOnScreenOnly: List windows that are currently on screen
        # kCGWindowListExcludeDesktopElements: Exclude desktop elements like the dock
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        
        windows = []
        for window in window_list:
            # We only want standard windows (layer 0)
            if window.get('kCGWindowLayer') != 0:
                continue
                
            owner_name = window.get('kCGWindowOwnerName', 'Unknown')
            window_name = window.get('kCGWindowName', '')
            window_id = window.get('kCGWindowNumber')
            pid = window.get('kCGWindowOwnerPID')
            bounds_dict = window.get('kCGWindowBounds')
            
            # Basic filtering: ignore windows with very small bounds or no owner
            if not owner_name or owner_name == 'Window Server':
                continue
                
            # Bounds are returned as a dictionary: {X, Y, Width, Height}
            bounds = {
                'x': bounds_dict.get('X', 0),
                'y': bounds_dict.get('Y', 0),
                'width': bounds_dict.get('Width', 0),
                'height': bounds_dict.get('Height', 0)
            }
            
            # Skip windows that are essentially invisible or too small
            if bounds['width'] < 10 or bounds['height'] < 10:
                continue
                
            windows.append(WindowInfo(
                window_id=window_id,
                app_name=owner_name,
                title=window_name,
                bounds=bounds,
                pid=pid
            ))
            
        # Deduplicate and sort (sometimes multiple entries for same window or many sub-windows)
        # For v1, we'll just keep them all but maybe sort by app name
        windows.sort(key=lambda x: x.app_name.lower())
        
        return windows

    @staticmethod
    def get_window_by_id(window_id: int) -> WindowInfo | None:
        """
        Finds a specific window by its ID.
        """
        windows = WindowEnumerator.get_active_windows()
        for w in windows:
            if w.window_id == window_id:
                return w
        return None
