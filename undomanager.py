# file: undomanager.py
import os
import pickle
import json
import tempfile
import time
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from textual.widgets import DataTable
import zlib

class UndoManager:
    """
    Manages undo/redo operations using disk-based snapshots.
    Supports both full snapshots and delta compression.
    """
    
    def __init__(self, data_table: DataTable, max_history_size: int = 50):
        """
        Initialize the UndoManager.
        
        Args:
            data_table: The DataTable widget to manage
            max_history_size: Maximum number of undo steps to keep
        """
        self.data_table = data_table
        self.max_history_size = max_history_size
        
        # Create temporary directory for snapshots
        self.temp_dir = tempfile.mkdtemp(prefix="csv_editor_undo_")
        self.snapshot_counter = 0
        
        # Undo/Redo stacks (store metadata only)
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
        
        # State tracking
        self._in_undo_redo = False
        self.current_changes: Dict[str, Tuple[Any, Any]] = {}
        
        # Statistics
        self.stats = {
            'snapshots_created': 0,
            'snapshots_loaded': 0,
            'disk_used': 0,
            'compression_ratio': 1.0
        }
    
    def __del__(self):
        """Clean up temporary files on deletion."""
        self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def get_temp_dir(self) -> str:
        """Get the temporary directory path."""
        return self.temp_dir
    
    def get_stats(self) -> Dict:
        """Get usage statistics."""
        # Calculate current disk usage
        disk_used = 0
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, file)
                if os.path.isfile(filepath):
                    disk_used += os.path.getsize(filepath)
        
        self.stats['disk_used'] = disk_used
        self.stats['undo_stack_size'] = len(self.undo_stack)
        self.stats['redo_stack_size'] = len(self.redo_stack)
        
        return self.stats.copy()
    
    # ============================================
    # File Management
    # ============================================
    
    def _get_snapshot_filename(self, snapshot_id: int) -> str:
        """Generate filename for a snapshot."""
        return os.path.join(self.temp_dir, f"snapshot_{snapshot_id}.pkl")
    
    def _get_metadata_filename(self, snapshot_id: int) -> str:
        """Generate filename for metadata."""
        return os.path.join(self.temp_dir, f"meta_{snapshot_id}.json")
    
    def _create_snapshot_id(self) -> int:
        """Generate a unique snapshot ID."""
        self.snapshot_counter += 1
        return self.snapshot_counter
    
    def _delete_snapshot_file(self, snapshot_id: int) -> None:
        """Delete snapshot file from disk."""
        try:
            # Delete main snapshot file
            snapshot_file = self._get_snapshot_filename(snapshot_id)
            if os.path.exists(snapshot_file):
                os.remove(snapshot_file)
            
            # Delete metadata file
            meta_file = self._get_metadata_filename(snapshot_id)
            if os.path.exists(meta_file):
                os.remove(meta_file)
        except:
            pass
    
    # ============================================
    # Data Extraction
    # ============================================
    
    def _extract_table_state(self) -> Dict:
        """
        Extract current table state in a compact format.
        Only stores non-empty cells to save space.
        """
        if not self.data_table or not hasattr(self.data_table, 'rows'):
            return {}
        
        state = {
            'columns': [],
            'rows': {},
            'column_widths': {},
            'cursor': self._get_cursor_position(),
            'timestamp': time.time()
        }
        
        # Extract column information
        for col_key in self.data_table.columns.keys():
            col = self.data_table.columns[col_key]
            state['columns'].append({
                'key': col_key.value,
                'label': col.label,
                'width': col.width if hasattr(col, 'width') else None
            })
        
        # Extract column widths
        for col_key in self.data_table.columns.keys():
            state['column_widths'][col_key.value] = self.data_table.columns[col_key].width
        
        # Extract cell values (only non-empty)
        for row_key in self.data_table.rows:
            row_data = {}
            for col_key in self.data_table.columns.keys():
                try:
                    value = self.data_table.get_cell(row_key, col_key)
                    if value is not None and str(value).strip():
                        row_data[col_key.value] = str(value)
                except:
                    continue
            
            if row_data:  # Only store rows with data
                state['rows'][row_key] = row_data
        
        return state
    
    def _extract_full_table_state(self) -> Dict:
        """
        Extract full table state including empty cells.
        Used for periodic full snapshots.
        """
        if not self.data_table:
            return {}
        
        state = {
            'columns': [],
            'rows': {},
            'column_widths': {},
            'cursor': self._get_cursor_position(),
            'timestamp': time.time()
        }
        
        # Extract column information
        for col_key in self.data_table.columns.keys():
            col = self.data_table.columns[col_key]
            state['columns'].append({
                'key': col_key.value,
                'label': col.label,
                'width': col.width if hasattr(col, 'width') else None
            })
        
        # Extract all cell values (including empty)
        for row_key in self.data_table.rows:
            row_data = {}
            for col_key in self.data_table.columns.keys():
                try:
                    value = self.data_table.get_cell(row_key, col_key)
                    row_data[col_key.value] = str(value) if value is not None else ""
                except:
                    row_data[col_key.value] = ""
            
            state['rows'][row_key] = row_data
        
        # Extract column widths
        for col_key in self.data_table.columns.keys():
            state['column_widths'][col_key.value] = self.data_table.columns[col_key].width
        
        return state
    
    def _get_cursor_position(self) -> Optional[Tuple[int, int]]:
        """Get current cursor position."""
        try:
            if hasattr(self.data_table, 'cursor_coordinate'):
                coord = self.data_table.cursor_coordinate
                return (coord.row, coord.column)
        except:
            pass
        return None
    
    # ============================================
    # Snapshot Creation
    # ============================================
    
    def create_snapshot(self, action: str = "", snapshot_type: str = "auto") -> int:
        """
        Create a snapshot of current state.
        
        Args:
            action: Description of the action
            snapshot_type: "full", "delta", or "auto" (chooses based on change size)
        
        Returns:
            Snapshot ID or -1 if failed
        """
        if self._in_undo_redo:
            return -1
        
        snapshot_id = self._create_snapshot_id()
        
        # Choose snapshot type
        if snapshot_type == "auto":
            if self.current_changes and len(self.current_changes) < 100:
                snapshot_type = "delta"
            else:
                snapshot_type = "full"
        
        try:
            if snapshot_type == "delta":
                success = self._save_delta_snapshot(snapshot_id, action)
            else:
                success = self._save_full_snapshot(snapshot_id, action)
            
            if success:
                # Store in undo stack
                self.undo_stack.append({
                    'id': snapshot_id,
                    'action': action,
                    'timestamp': time.time(),
                    'type': snapshot_type
                })
                
                # Clear redo stack when new action is performed
                self.redo_stack.clear()
                
                # Clean up old snapshots if needed
                self._cleanup_old_snapshots()
                
                # Clear current changes
                self.current_changes.clear()
                
                self.stats['snapshots_created'] += 1
                return snapshot_id
            else:
                return -1
                
        except Exception as e:
            print(f"Error creating snapshot: {e}")
            return -1
    
    def _save_full_snapshot(self, snapshot_id: int, action: str) -> bool:
        """Save a full snapshot to disk."""
        try:
            # Extract table state
            state = self._extract_full_table_state()
            state['id'] = snapshot_id
            state['action'] = action
            state['type'] = 'full'
            
            # Compress and save
            compressed_data = self._compress_data(state)
            
            with open(self._get_snapshot_filename(snapshot_id), 'wb') as f:
                f.write(compressed_data)
            
            # Save metadata
            self._save_metadata(snapshot_id, state, len(compressed_data))
            
            return True
            
        except Exception as e:
            print(f"Error saving full snapshot: {e}")
            return False
    
    def _save_delta_snapshot(self, snapshot_id: int, action: str) -> bool:
        """Save a delta (changes only) snapshot to disk."""
        try:
            if not self.current_changes:
                # If no changes tracked, save full snapshot instead
                return self._save_full_snapshot(snapshot_id, action)
            
            # Convert changes to serializable format
            serializable_changes = {}
            for coord, (old_val, new_val) in self.current_changes.items():
                if isinstance(coord, tuple):
                    coord_str = f"{coord[0]},{coord[1]}"
                else:
                    coord_str = str(coord)
                serializable_changes[coord_str] = (old_val, new_val)
            
            delta_data = {
                'id': snapshot_id,
                'action': action,
                'timestamp': time.time(),
                'type': 'delta',
                'changes': serializable_changes,
                'cursor': self._get_cursor_position(),
                'full_snapshot_ref': None
            }
            
            # Periodically link to full snapshot (every 10th delta)
            if len(self.undo_stack) % 10 == 0:
                full_id = self._create_snapshot_id()
                if self._save_full_snapshot(full_id, f"baseline_for_{snapshot_id}"):
                    delta_data['full_snapshot_ref'] = full_id
            
            # Compress and save
            compressed_data = self._compress_data(delta_data)
            
            with open(self._get_snapshot_filename(snapshot_id), 'wb') as f:
                f.write(compressed_data)
            
            # Save metadata
            self._save_metadata(snapshot_id, delta_data, len(compressed_data))
            
            return True
            
        except Exception as e:
            print(f"Error saving delta snapshot: {e}")
            return False
    
    def _save_metadata(self, snapshot_id: int, data: Dict, size: int) -> None:
        """Save lightweight metadata for quick access."""
        try:
            metadata = {
                'id': snapshot_id,
                'action': data.get('action', ''),
                'timestamp': data.get('timestamp', time.time()),
                'type': data.get('type', 'full'),
                'size': size,
                'rows': len(data.get('rows', {})),
                'changes': len(data.get('changes', {})),
                'cursor': data.get('cursor')
            }
            
            with open(self._get_metadata_filename(snapshot_id), 'w') as f:
                json.dump(metadata, f, indent=2)
        except:
            pass
    
    def _compress_data(self, data: Dict) -> bytes:
        """Compress data using zlib."""
        try:
            pickled = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            compressed = zlib.compress(pickled, level=6)
            
            # Update compression ratio stat
            if len(pickled) > 0:
                self.stats['compression_ratio'] = len(compressed) / len(pickled)
            
            return compressed
        except:
            # Fallback: don't compress
            return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
    
    def _decompress_data(self, compressed_data: bytes) -> Dict:
        """Decompress data."""
        try:
            decompressed = zlib.decompress(compressed_data)
            return pickle.loads(decompressed)
        except:
            # Fallback: assume it's not compressed
            return pickle.loads(compressed_data)
    
    # ============================================
    # Snapshot Restoration
    # ============================================
    
    def load_snapshot(self, snapshot_id: int) -> Optional[Dict]:
        """
        Load a snapshot from disk.
        
        Returns:
            The snapshot data or None if failed
        """
        try:
            filename = self._get_snapshot_filename(snapshot_id)
            
            if not os.path.exists(filename):
                return None
            
            # Load and decompress
            with open(filename, 'rb') as f:
                compressed_data = f.read()
            
            data = self._decompress_data(compressed_data)
            
            self.stats['snapshots_loaded'] += 1
            return data
            
        except Exception as e:
            print(f"Error loading snapshot {snapshot_id}: {e}")
            return None
    
    def restore_snapshot(self, snapshot_id: int) -> bool:
        """
        Restore table state from snapshot.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._in_undo_redo = True
            
            # Load snapshot data
            data = self.load_snapshot(snapshot_id)
            if not data:
                return False
            
            # Restore based on snapshot type
            if data.get('type') == 'delta':
                success = self._apply_delta_snapshot(data)
            else:
                success = self._apply_full_snapshot(data)
            
            # Restore cursor position if available
            if success and data.get('cursor'):
                self._restore_cursor(data['cursor'])
            
            return success
            
        except Exception as e:
            print(f"Error restoring snapshot: {e}")
            return False
        finally:
            self._in_undo_redo = False
    
    def _apply_full_snapshot(self, data: Dict) -> bool:
        """Apply a full snapshot to the table."""
        try:
            # Clear the table
            self.data_table.clear(columns=True)
            
            # Restore columns
            for col_info in data.get('columns', []):
                width = col_info.get('width')
                if col_info['key'] == 'row_number':
                    self.data_table.add_column(col_info['label'], key=col_info['key'], width=width or 5)
                else:
                    if width:
                        self.data_table.add_column(col_info['label'], key=col_info['key'], width=width)
                    else:
                        self.data_table.add_column(col_info['label'], key=col_info['key'])
            
            # Restore rows
            for row_key, row_cells in data.get('rows', {}).items():
                row_data = []
                for col_info in data.get('columns', []):
                    value = row_cells.get(col_info['key'], "")
                    row_data.append(value)
                
                self.data_table.add_row(*row_data)
            
            # Refresh table
            self.data_table.refresh(layout=True)
            return True
            
        except Exception as e:
            print(f"Error applying full snapshot: {e}")
            return False
    
    def _apply_delta_snapshot(self, data: Dict) -> bool:
        """Apply a delta snapshot to the table."""
        try:
            changes = data.get('changes', {})
            
            # Track reverse changes for potential redo
            reverse_changes = {}
            
            for coord_str, (old_val, new_val) in changes.items():
                try:
                    # Parse coordinates
                    if ',' in coord_str:
                        row_str, col_str = coord_str.split(',')
                        row, col = int(row_str), int(col_str)
                        coord = (row, col)
                    else:
                        # Handle other coordinate formats if needed
                        coord = coord_str
                    
                    # Get current value
                    if isinstance(coord, tuple):
                        current_val = self.data_table.get_cell_at(coord)
                    else:
                        # This would need custom handling for other formats
                        continue
                    
                    # Apply change
                    if isinstance(coord, tuple):
                        self.data_table.update_cell_at(coord, new_val)
                    
                    # Track for reverse
                    reverse_changes[coord_str] = (current_val, new_val)
                    
                except Exception as e:
                    print(f"Error applying change {coord_str}: {e}")
                    continue
            
            # Refresh table
            self.data_table.refresh(layout=True)
            return True
            
        except Exception as e:
            print(f"Error applying delta snapshot: {e}")
            return False
    
    def _restore_cursor(self, cursor_pos: Tuple[int, int]) -> None:
        """Restore cursor position."""
        try:
            if hasattr(self.data_table, 'cursor_coordinate'):
                row, col = cursor_pos
                if (row < self.data_table.row_count and 
                    col < len(self.data_table.columns)):
                    self.data_table.cursor_coordinate = type(self.data_table.cursor_coordinate)(row, col)
        except:
            pass
    
    # ============================================
    # Undo/Redo Operations
    # ============================================
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return len(self.redo_stack) > 0
    
    def undo(self) -> Tuple[bool, str]:
        """
        Undo the last action.
        
        Returns:
            (success, action_description)
        """
        if not self.can_undo():
            return False, "Nothing to undo"
        
        try:
            # Get last action
            last_action = self.undo_stack.pop()
            
            # For delta snapshots, we need to apply reverse changes
            # For full snapshots, we need to load previous state
            if last_action.get('type') == 'delta':
                # For deltas, we need to find the previous full snapshot
                # or apply reverse changes
                prev_id = self._find_previous_full_snapshot()
                if prev_id:
                    success = self.restore_snapshot(prev_id)
                else:
                    # Create reverse delta and apply it
                    success = self._undo_delta_action(last_action['id'])
            else:
                # For full snapshots, load previous state
                if self.undo_stack:
                    prev_action = self.undo_stack[-1]
                    success = self.restore_snapshot(prev_action['id'])
                else:
                    # No previous state - clear table
                    success = self._clear_table()
            
            if success:
                # Move to redo stack
                self.redo_stack.append(last_action)
                return True, last_action.get('action', 'Undo')
            else:
                # Put it back if failed
                self.undo_stack.append(last_action)
                return False, "Failed to undo"
                
        except Exception as e:
            print(f"Error in undo: {e}")
            return False, str(e)
    
    def redo(self) -> Tuple[bool, str]:
        """
        Redo the last undone action.
        
        Returns:
            (success, action_description)
        """
        if not self.can_redo():
            return False, "Nothing to redo"
        
        try:
            # Get last undone action
            last_action = self.redo_stack.pop()
            
            # Restore that state
            success = self.restore_snapshot(last_action['id'])
            
            if success:
                # Move back to undo stack
                self.undo_stack.append(last_action)
                return True, last_action.get('action', 'Redo')
            else:
                # Put it back if failed
                self.redo_stack.append(last_action)
                return False, "Failed to redo"
                
        except Exception as e:
            print(f"Error in redo: {e}")
            return False, str(e)
    
    def _find_previous_full_snapshot(self) -> Optional[int]:
        """Find the previous full snapshot in the undo stack."""
        for i in range(len(self.undo_stack) - 1, -1, -1):
            if self.undo_stack[i].get('type') == 'full':
                return self.undo_stack[i]['id']
        return None
    
    def _undo_delta_action(self, delta_id: int) -> bool:
        """Special handling for undoing delta actions."""
        # Load delta data
        data = self.load_snapshot(delta_id)
        if not data:
            return False
        
        # Apply reverse changes
        changes = data.get('changes', {})
        for coord_str, (old_val, new_val) in changes.items():
            try:
                if ',' in coord_str:
                    row_str, col_str = coord_str.split(',')
                    row, col = int(row_str), int(col_str)
                    self.data_table.update_cell_at((row, col), old_val)
            except:
                continue
        
        self.data_table.refresh(layout=True)
        return True
    
    def _clear_table(self) -> bool:
        """Clear the table (for when there's no previous state)."""
        try:
            self.data_table.clear(columns=True)
            # Add minimal structure
            self.data_table.add_column("#", key="row_number", width=5)
            self.data_table.add_column("A", key="col_0")
            return True
        except:
            return False
    
    # ============================================
    # Change Tracking
    # ============================================
    
    def start_tracking_changes(self) -> None:
        """Start tracking cell changes for delta snapshots."""
        self.current_changes.clear()
    
    def track_cell_change(self, coord, old_value, new_value) -> None:
        """
        Track a single cell change.
        
        Args:
            coord: Cell coordinate (row, col) or identifier
            old_value: Value before change
            new_value: Value after change
        """
        self.current_changes[coord] = (old_value, new_value)
    
    def get_current_changes(self) -> Dict:
        """Get all tracked changes."""
        return self.current_changes.copy()
    
    # ============================================
    # History Management
    # ============================================
    
    def _cleanup_old_snapshots(self) -> None:
        """Remove old snapshots when history limit is exceeded."""
        while len(self.undo_stack) > self.max_history_size:
            if self.undo_stack:
                oldest = self.undo_stack.pop(0)
                self._delete_snapshot_file(oldest['id'])
    
    def clear_history(self) -> None:
        """Clear all undo/redo history."""
        # Delete all snapshot files
        for action in self.undo_stack + self.redo_stack:
            self._delete_snapshot_file(action['id'])
        
        # Clear stacks
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_changes.clear()
    
    def get_history_info(self) -> List[Dict]:
        """Get information about undo history."""
        history = []
        for i, action in enumerate(reversed(self.undo_stack)):
            history.append({
                'index': len(self.undo_stack) - i,
                'action': action.get('action', 'Unknown'),
                'timestamp': action.get('timestamp', 0),
                'type': action.get('type', 'full'),
                'id': action['id']
            })
        return history
    
    def get_last_action(self) -> Optional[str]:
        """Get description of last action."""
        if self.undo_stack:
            return self.undo_stack[-1].get('action')
        return None
