"""Defines editor-specific functions

YOU SHOULD ALMOST ALWAYS LOAD THIS FILE

This script defines a number of python functions and GPS actions that can
be used inside GPS editors. These can be used to move the cursor around or
edit the text.
They are often programmed so that they emulate the Emacs editor, but they
are independent of the Emacs mode and do not override any key shortcut. As
a result you can define your own shortcuts for the actions defined in this
package.
See also emacs.xml
"""

###########################################################################
# Customization variables
# These variables can be changed in the initialization commands associated
# with this script (see /Tools/Scripts)

transient_mark_mode = False
## If set to False, then the region is never unselected when the clipboard is
## modified by a Cut/Copy/Paste operation. This is broadly similar to the Emacs
## mode with the same name, although will behave differently in some cases


############################################################################
## No user customization below this line
############################################################################

import GPS
import string, traceback
import navigation_utils

def on_gps_started (hook_name):
  if transient_mark_mode:
    GPS.Hook ("clipboard_changed").add (on_clipboard_changed)

  GPS.parse_xml ("""
   <action name="subprogram box" output="none" category="Editor">
      <description>Search backward for the first subprogram or package declaration. Before the start of this declaration, insert a comment box containing the name of the subprogram. This provides helpful separations between subprograms, and is similar to the style used in the GNAT compiler or GPS themselves</description>
      <filter_and>
         <filter id="Source editor" />
         <filter language="ada" />
      </filter_and>
      <shell lang="python">text_utils.add_subprogram_box()</shell>
   </action>

   <action name="kill line" output="none" category="Editor">
      <description>This is similar to Emacs' kill-line function. It deletes the end of the line after the cursor's current column. If the cursor is at the end of the line, it deletes the newline character and therefore joins the current line and the next.
The text that is deleted is copied to the clipboard. If you call this action multiple times from the same location, all deleted text is merged into a single clipboard, so that a single Paste will put it all back.
When this command is executed after a repeat_next command, the whole line is deleted to provide a more intuitive behavior.</description>
      <filter id="Source editor" />
      <shell lang="python">if $repeat == 1: text_utils.kill_line (None, $remaining+1)</shell>
   </action>

   <action name="open line" output="none" category="Editor">
      <description>Insert a new line, but leaves the cursor at its current place</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.open_line()</shell>
   </action>

   <action name="kill forward" output="none" category="Editor">
      <description>Deletes the character just after the cursor</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.delete_forward()</shell>
   </action>

   <action name="transpose chars" output="none" category="Editor">
      <description>Swap the two characters around the cursor</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.transpose_chars()</shell>
   </action>

   <action name="Transpose lines" output="none" category="Editor">
      <description>Swap the current line and the following one</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.transpose_lines()</shell>
   </action>

   <action name="goto beginning of line" output="none" category="Editor">
      <description>Move the cursor to the beginning of the current line</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.goto_beginning_of_line()</shell>
   </action>

   <action name="goto end of line" output="none" category="Editor">
      <description>Move the cursor to the end of the current line</description>
      <filter id="Source editor" />
      <shell lang="python" >text_utils.goto_end_of_line()</shell>
   </action>

   <action name="goto beginning of buffer" output="none" category="Editor">
      <description>Move the cursor to the beginning of the buffer</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.beginning_of_buffer()</shell>
   </action>

   <action name="goto end of buffer" output="none" category="Editor">
      <description>Move the cursor to the end of the buffer</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.end_of_buffer()</shell>
   </action>

   <action name="set mark command" output="none" category="Editor">
      <description>This is similar to Emacs's behavior: a mark is put at the current cursor position. You can then move the cursor elsewhere, and delete the text between this mark and the new cursor position. See also the action "Cancel mark command"</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.set_mark_command()</shell>
   </action>

   <action name="Cancel mark command" output="none" category="Editor">
      <description>Remove the emacs-emulation mark in the current editor. See also the action "Set mark command"</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.cancel_mark_command ()</shell>
   </action>

   <action name="kill region" output="none" category="Editor">
      <description>Delete the area of text between the mark set by "set mark command" and the current cursor position. This emulates Emacs' behavior.</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.kill_region()</shell>
   </action>

   <action name="kill ring save"  output="none" category="Editor">
      <filter id="Source editor" />
      <shell lang="python">text_utils.kill_ring_save()</shell>
   </action>

   <action name="delete horizontal space" output="none" category="Editor">
      <description>Delete all white spaces on the current line before and after the cursor</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.delete_horizontal_space()</shell>
   </action>

   <action name="Join line" output="none" category="Editor">
      <description>Join the current line and the following one. They are separated by a single space, and the cursor is left on that space</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.join_line()</shell>
   </action>

   <action name="Upper case word" output="none" category="Editor">
      <description>Upper case the current word (starting at the current character)</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.upper_case_word ()</shell>
   </action>

   <action name="Lower case word" output="none" category="Editor">
      <description>Lower case the current word (starting at the current character)</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.lower_case_word ()</shell>
   </action>

   <action name="Capitalize word" output="none" category="Editor">
      <description>Capitalize the current word (starting at the current character)</description>
      <filter id="Source editor" />
      <shell lang="python">text_utils.capitalize_case_word ()</shell>
   </action>

""")

## The blocks for which we want to display boxes
subprogram_box_blocks={}
for b in ["CAT_PROCEDURE", "CAT_FUNCTION", "CAT_ENTRY",
          "CAT_PROTECTED", "CAT_TASK", "CAT_PACKAGE"]:
  subprogram_box_blocks[b]=1

def add_subprogram_box():
   """ Insert in the current editor a box just before the current subprogram
       starts """

   buffer  = GPS.EditorBuffer.get ()
   loc     = buffer.current_view().cursor()
   initial = loc.create_mark()
   min     = buffer.beginning_of_buffer()

   if loc.block_type() == "CAT_UNKNOWN":
      return

   while (not subprogram_box_blocks.has_key (loc.block_type())) and (loc > min):
      loc = loc.block_start() - 1

   if loc > min:
      name = loc.block_name()
      loc = loc.block_start().beginning_of_line();
      dashes = '-' * (len (name) + 6)
      box = dashes + "\n" + "-- " + name + " --\n" + dashes + "\n\n"

      # Start an undo group so that the whole process can be undone with a
      # single click
      buffer.start_undo_group()
      buffer.insert (loc, box)
      buffer.indent (loc, loc.forward_line (3))
      buffer.current_view().goto (initial.location())
      buffer.finish_undo_group()

def delete_forward():
   """Delete the character just after the cursor in the current editor"""
   buffer = GPS.EditorBuffer.get()
   cursor = buffer.current_view().cursor()
   buffer.delete (cursor, cursor)

def kill_line (location = None, count=1):
   """ Kills the end of the line on which LOCATION is.
       If LOCATION is unspecified, the current cursor location in the current
       editor is used.
       If the line is empty or contains only white spaces, the whole line is
       deleted.
       This is a better emulation of Emacs's behavior than the one provided by
       default by gtk+, which doesn't handle whitespaces correctly.
       When called several times from the same line, entries are appended in
       the clipboard.
       Count is the number of lines to delete. If greater than 1, then the
       whole lines are deleted, including newline characters."""

   if not location:
      location = GPS.EditorBuffer.get ().current_view ().cursor ()
   buffer = location.buffer ()
   start  = location

   append          = GPS.last_command() == "kill-line"
   GPS.set_last_command ("kill-line")

   # In case the current location points to a line terminator we just cut it
   if count == 1 and start.get_char() == "\n":
      buffer.cut (start, start, append)
   else:
      bol = start
      for line in range (1, count + 1):
         end       = bol.end_of_line ()
         str       = buffer.get_chars (start, end)
         strip_str = str.rstrip ()
         if count == 1 \
          and len (str) > 0 \
          and str [len (str) - 1] == '\n' and strip_str != "":
            end = end.forward_char (-1)
         bol = end+1
      buffer.cut (start, end, append)

################################################
## Moving the cursor
################################################

def beginning_of_buffer():
   """Move the cursor to the beginning of the buffer"""
   buffer = GPS.EditorBuffer.get()
   buffer.current_view().goto (buffer.beginning_of_buffer())

def end_of_buffer():
   """Move the cursor to the end of the buffer"""
   buffer = GPS.EditorBuffer.get()
   buffer.current_view().goto (buffer.end_of_buffer())

def goto_beginning_of_line():
   """Goto the beginning of line"""
   view = GPS.EditorBuffer.get().current_view()
   view.goto (view.cursor().beginning_of_line())

def end_of_line(file, line):
   """Goto to the end of the line in file"""
   buffer = GPS.EditorBuffer.get (GPS.File (file))
   loc  = GPS.EditorLocation (buffer, line, 1)
   buffer.current_view().goto (loc.end_of_line() - 1)

def goto_end_of_line():
   """Goto the end of line"""
   view = GPS.EditorBuffer.get().current_view()
   view.goto (view.cursor().end_of_line())

def is_space (char):
   return char == ' ' or char == '\t'

def delete_horizontal_space(backward=1, forward=1):
   """Delete all spaces and tabs around the cursor in the current editor.
The two parameters can be used to control in what directions white spaces are
searched for"""
   buffer = GPS.EditorBuffer.get()
   start = buffer.current_view().cursor()
   end = start
   if forward:
      max = end.end_of_line()
      while is_space (end.get_char()) and end < max:
        end = end + 1
      end = end - 1
   if backward:
      max = start.beginning_of_line()
      start = start - 1
      while is_space (start.get_char()) and start >= max:
        start = start - 1
      start = start + 1
   if start <= end:
      buffer.delete (start, end)

def transpose_chars():
   """Transpose characters around cursor, moving forward one character."""
   buffer = GPS.EditorBuffer.get()
   cursor = buffer.current_view().cursor()
   if cursor > buffer.beginning_of_buffer():
      c = cursor.get_char ()
      buffer.start_undo_group ()
      buffer.delete (cursor, cursor)
      buffer.insert (cursor - 1, c)
      buffer.current_view().goto (cursor + 1)
      buffer.finish_undo_group ()

def transpose_lines (location = None):
   """Transpose the line at LOCATION (or current line) and the following one"""
   if not location:
      location = GPS.EditorBuffer.get().current_view ().cursor ()
   buffer = location.buffer ()
   if location.line () < buffer.lines_count ():
      buffer.start_undo_group ()
      start = location.beginning_of_line ()
      end   = location.end_of_line ()
      text  = buffer.get_chars (start, end)
      buffer.delete (start, end)
      buffer.insert (start.end_of_line () + 1, text)
      buffer.finish_undo_group ()

def open_line():
   """Insert a newline and leave cursor before it."""
   buffer = GPS.EditorBuffer.get()
   cursor = buffer.current_view().cursor()
   buffer.insert (cursor, "\n")
   buffer.current_view().goto (cursor)

def join_line ():
   """Join the current line and the following one, separated by a single
      space, and leaves the cursor on the space"""
   buffer = GPS.EditorBuffer.get()
   eol = buffer.current_view().cursor().end_of_line()
   buffer.start_undo_group ()
   buffer.current_view().goto (eol)
   buffer.delete (eol, eol)  ## Newline character
   delete_horizontal_space (backward=0, forward=1)
   if not is_space (eol.forward_char (-1).get_char ()):
      buffer.insert (eol, "XXX")
   buffer.finish_undo_group ()

def apply_func_to_word (func, location=None):
   """Apply a function to the current word (starting at the current character).
      FUNC takes one argument, the text it replaces, and should return the
      replacement text"""
   if not location:
      location = GPS.EditorBuffer.get ().current_view().cursor()
   buffer = location.buffer()
   buffer.start_undo_group ()
   end = location.forward_word()
   text = func (buffer.get_chars (location, end))
   buffer.delete (location, end)
   buffer.insert (location, text)
   buffer.finish_undo_group ()

def upper_case_word (location=None):
   """Upper case the current word (starting at the current character)"""
   apply_func_to_word (str.upper, location)

def lower_case_word (location=None):
   """Lower case the current word (starting at the current character)"""
   apply_func_to_word (str.lower, location)

def capitalize_case_word (location=None):
   """Capitalize the current word (starting at the current character)"""
   apply_func_to_word (str.capitalize, location)

class BlockIterator:
   """An iterator for the various sections of an editor.
      Each step in the iteration returns a tuple (start, end) of EditorLocation
      instances for the section.
      The constructor parameter overlay_name can be one of:
          - "":          The whole buffer is returned
          - "selection": The current selection in the buffer is returned
          - "word":      The current word in the buffer is returned
          - overlay name: All sections for which this overlay applies are
                         returned. The name could be one of "comment",
                         "keywords", "string" or "character"
      Example of use:
          buffer = EditorBuffer.get()
          for start, end in BlockIterator (buffer, "comments"):
             ...
   """
   def __init__ (self, buffer, overlay_name):
      self.mark    = buffer.beginning_of_buffer ().create_mark()
      if overlay_name != "" \
       and overlay_name != "selection" \
       and overlay_name != "word":
         self.overlay = buffer.create_overlay (overlay_name)
         self.in_comment = \
           buffer.beginning_of_buffer().has_overlay (self.overlay)
      else:
         self.overlay = None
         self.overlay_name = overlay_name
   def __iter__ (self):
      return self
   def next (self):
      loc = self.mark.location ()
      if not self.overlay:
        if loc < loc.buffer().end_of_buffer():
           self.mark.move (loc.buffer().end_of_buffer())
           if self.overlay_name == "selection":
              return (loc.buffer().selection_start(),
                      loc.buffer().selection_end())
           elif self.overlay_name == "word":
              cursor = loc.buffer().current_view().cursor()
              start = cursor
              while not start.starts_word(): start = start - 1
              while not cursor.ends_word() : cursor = cursor + 1
              return (start, cursor)
           else:
              return (loc.buffer().beginning_of_buffer(),
                      loc.buffer().end_of_buffer())
      else:
        # Find beginning of next section
        if not loc.has_overlay (self.overlay):
           loc = loc.forward_overlay (self.overlay)

        if loc >= loc.buffer().end_of_buffer():
           raise StopIteration

        loc2 = loc.forward_overlay (self.overlay)
        self.mark.move (loc2 + 1)
        return (loc, loc2 - 1)

class WordIterator:
   """An iterator for all words in a block. Each iteration returns a
      tuple (start, end) of EditorLocation instances.
      Example of use:
        buffer = EditorBuffer.get()
        for blockStart, blockEnd in BlockIterator (buffer, "comments"):
           for wordStart, wordEnd in WordIterator (blockStart, blockEnd):
              ...
   """
   def __init__ (self, start, end):
      self.mark = start.create_mark()
      self.end  = end
   def __iter__ (self):
      return self
   def starts_at (self, loc):
      self.mark.move (loc)
   def next (self):
      loc = self.mark.location ()
      while loc < self.end:
         loc2 = loc.forward_word ()
         if loc.get_char().isalpha():
            # Use a mark, in case the buffer is modified
            self.mark.move (loc2 + 1)
            return (loc, loc2 - 1)
         else:
            loc = loc + 1
      raise StopIteration

class LineIterator:
   """An iterator for all lines in a block. Each iteration returns a
      tuple (start, end) of EditorLocation instances."""
   def __init__ (self, start, end):
      self.mark = start.create_mark()
      self.end  = end.create_mark()
   def __iter__ (self):
      return self
   def next (self):
      loc = self.mark.location()
      if loc >= self.end.location():
        raise StopIteration
      loc2 = loc.end_of_line()
      if loc2 >= self.end.location():
        self.mark.move (self.end.location() + 1)
        return (loc, self.end.location())
      else:
        self.mark.move (loc2 + 1)
        return (loc, loc2)

### Emulating Emacs selection:
### In Emacs, one sets the mark first, then when the cursor is moved the
### selection is extended appropriately. This is rather tricky to emulate
### in gtk+.
### There are two implementations: when pygtk is available, we simply
### temporarily override the key bindings so that the selection is always
### extended. This avoids all flickering, has no run-time cost, and is
### certainly the nicest. Not quite perfect though, since other functions
### that move the cursor will not extend the selection, only the basic
### key bindings defined for a gkt.TextView do.
### However, if pygtk is not available, we emulate it by monitoring all
### location changes. The slow down is almost invisible, but since the
### selection is first cancelled by gtk+ when the cursor is moved, and we
### then reselect it, there is some flickering

try:
   import gtk, gobject
   has_pygtk = 1

   HOME      = 65360
   LEFT      = 65361
   UP        = 65362
   RIGHT     = 65363
   DOWN      = 65364
   PAGE_UP   = 65365
   PAGE_DOWN = 65366
   END       = 65367

   KP_HOME      = 65429
   KP_LEFT      = 65430
   KP_UP        = 65431
   KP_RIGHT     = 65432
   KP_DOWN      = 65433
   KP_PAGE_UP   = 65434
   KP_PAGE_DOWN = 65435
   KP_END       = 65436

   def override (key, modifier, movement, step, select):
       gtk.binding_entry_remove (gtk.TextView, key, modifier)
       gtk.binding_entry_add_signal (gtk.TextView, key, modifier,
                                     "move_cursor",
                                     gobject.TYPE_ENUM, movement,
                                     gobject.TYPE_INT,  step,
                                     gobject.TYPE_BOOLEAN, select)

   def override_key_bindings (select):
       """Override the default TextView keybinding to either always force
          the extension the selection, or not"""
       override (RIGHT,    0, gtk.MOVEMENT_VISUAL_POSITIONS, 1, select)
       override (KP_RIGHT, 0, gtk.MOVEMENT_VISUAL_POSITIONS, 1, select)
       override (LEFT,     0, gtk.MOVEMENT_VISUAL_POSITIONS, -1, select)
       override (KP_LEFT,  0, gtk.MOVEMENT_VISUAL_POSITIONS, -1, select)

       override (RIGHT,    gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_WORDS, 1, select)
       override (KP_RIGHT, gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_WORDS, 1, select)
       override (LEFT,     gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_WORDS, -1, select)
       override (KP_LEFT,  gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_WORDS, -1, select)

       override (UP,       0, gtk.MOVEMENT_DISPLAY_LINES, -1, select)
       override (KP_UP,    0, gtk.MOVEMENT_DISPLAY_LINES, -1, select)
       override (DOWN,     0, gtk.MOVEMENT_DISPLAY_LINES, 1, select)
       override (KP_DOWN,  0, gtk.MOVEMENT_DISPLAY_LINES, 1, select)

       override (UP,      gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_PARAGRAPHS, -1, select)
       override (KP_UP,   gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_PARAGRAPHS, -1, select)
       override (DOWN,    gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_PARAGRAPHS, 1, select)
       override (KP_DOWN, gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_PARAGRAPHS, 1, select)

       override (HOME,    0, gtk.MOVEMENT_DISPLAY_LINE_ENDS, -1, select)
       override (KP_HOME, 0, gtk.MOVEMENT_DISPLAY_LINE_ENDS, -1, select)
       override (END,     0, gtk.MOVEMENT_DISPLAY_LINE_ENDS, 1, select)
       override (KP_END,  0, gtk.MOVEMENT_DISPLAY_LINE_ENDS, 1, select)

       override (HOME,    gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_BUFFER_ENDS, -1, select)
       override (KP_HOME, gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_BUFFER_ENDS, -1, select)
       override (END,     gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_BUFFER_ENDS, 1, select)
       override (KP_END,  gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_BUFFER_ENDS, 1, select)

       override (PAGE_UP,      0, gtk.MOVEMENT_PAGES, -1, select)
       override (KP_PAGE_UP,   0, gtk.MOVEMENT_PAGES, -1, select)
       override (PAGE_DOWN,    0, gtk.MOVEMENT_PAGES, 1, select)
       override (KP_PAGE_DOWN, 0, gtk.MOVEMENT_PAGES, 1, select)

       override (PAGE_UP,      gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_HORIZONTAL_PAGES, -1, select)
       override (KP_PAGE_UP,   gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_HORIZONTAL_PAGES, -1, select)
       override (PAGE_DOWN,    gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_HORIZONTAL_PAGES, 1, select)
       override (KP_PAGE_DOWN, gtk.gdk.CONTROL_MASK, gtk.MOVEMENT_HORIZONTAL_PAGES, 1, select)

except ImportError:
   has_pygtk = 0
   def on_location_changed (hook, file, line, column):
      try:
         buffer = GPS.EditorBuffer.get (file)
         mark   = buffer.get_mark ("emacs_selection_bound")
         buffer.select (mark.location(), buffer.current_view().cursor())
      except:
         pass  ## no such mark

def set_mark_command (location = None):
    """Set mark at LOCATION (or current cursor if LOCATION is unspecified)"""
    if not location:
       location = GPS.EditorBuffer.get ().current_view ().cursor ()
    if has_pygtk:
        location.create_mark ("selection_bound")
        override_key_bindings (select = True)
    else:
        location.create_mark ("emacs_selection_bound")
        GPS.Hook ("location_changed").add (on_location_changed)

def cancel_mark_command (buffer = None):
    """Cancel the mark in BUFFER"""
    if not buffer:
       buffer = GPS.EditorBuffer.get ()
    try:
       buffer.unselect ()
       if has_pygtk:
          override_key_bindings (select = False)
       else:
          buffer.get_mark ("emacs_selection_bound").delete ()
          GPS.Hook ("location_changed").remove (on_location_changed)
    except:
       pass  ## No such mark

def on_clipboard_changed (hook):
    """Called when the contents of the clipboard has changed"""
    cancel_mark_command ()

GPS.Hook ("gps_started").add (on_gps_started)
