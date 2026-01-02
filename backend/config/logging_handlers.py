"""
Custom logging handlers for Windows compatibility.

The standard RotatingFileHandler fails on Windows when multiple threads
try to rotate the log file simultaneously due to file locking.
"""
import logging
import os
import time
from logging.handlers import RotatingFileHandler


class WindowsSafeRotatingFileHandler(RotatingFileHandler):
    """
    A RotatingFileHandler that handles Windows file locking issues.
    
    On Windows, file rotation can fail with PermissionError when another
    thread has the file open. This handler catches those errors and
    continues logging without crashing.
    """
    
    def doRollover(self):
        """
        Override doRollover to handle Windows file locking gracefully.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        
        if self.backupCount > 0:
            # Try to rotate files, but don't fail if we can't
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}")
                if os.path.exists(sfn):
                    try:
                        if os.path.exists(dfn):
                            os.remove(dfn)
                        os.rename(sfn, dfn)
                    except (OSError, PermissionError):
                        # File is locked, skip this rotation
                        pass
            
            dfn = self.rotation_filename(f"{self.baseFilename}.1")
            try:
                if os.path.exists(dfn):
                    os.remove(dfn)
                self.rotate(self.baseFilename, dfn)
            except (OSError, PermissionError):
                # File is locked, try to truncate instead
                try:
                    with open(self.baseFilename, 'w'):
                        pass  # Truncate the file
                except (OSError, PermissionError):
                    pass  # Give up, just continue logging
        
        if not self.delay:
            self.stream = self._open()
    
    def rotate(self, source, dest):
        """
        Override rotate to handle Windows file locking.
        """
        try:
            if os.path.exists(source):
                if os.path.exists(dest):
                    os.remove(dest)
                os.rename(source, dest)
        except (OSError, PermissionError):
            # On Windows, if the file is locked, just truncate it
            try:
                with open(source, 'w'):
                    pass
            except (OSError, PermissionError):
                pass  # Give up gracefully
