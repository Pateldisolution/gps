-----------------------------------------------------------------------
--                   GVD - The GNU Visual Debugger                   --
--                                                                   --
--                      Copyright (C) 2000-2002                      --
--                              ACT-Europe                           --
--                                                                   --
-- GVD is free  software;  you can redistribute it and/or modify  it --
-- under the terms of the GNU General Public License as published by --
-- the Free Software Foundation; either version 2 of the License, or --
-- (at your option) any later version.                               --
--                                                                   --
-- This program is  distributed in the hope that it will be  useful, --
-- but  WITHOUT ANY WARRANTY;  without even the  implied warranty of --
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU --
-- General Public License for more details. You should have received --
-- a copy of the GNU General Public License along with this library; --
-- if not,  write to the  Free Software Foundation, Inc.,  59 Temple --
-- Place - Suite 330, Boston, MA 02111-1307, USA.                    --
-----------------------------------------------------------------------

with Glib;
with Gtk.Widget; use Gtk.Widget;
with Gtk.Handlers; use Gtk.Handlers;
with Gdk.Pixmap;
with Gdk.Window;
with Gdk.Rectangle;
with Gtk.Main;
with Gdk.Event;
with Gtk.Window;

--  This package provides tooltips-like functionality. It differs from
--  the original Gtk.Tooltips package in that the drawing function is
--  left to the end user.
--  The drawing function is called after the timeout period, which means
--  that dynamic tooltips can be implemented with this package.
--
--  The generic part enables the user to carry a user-defined object
--  to the drawing function.
--
--  ??? Right now, both the user data and the widget on which the tooltips
--  are set are carried to the drawing function.
--  This was done because the widget is needed by the actual drawing
--  routines in most cases, although it is not entirely useful, since a
--  user could insert a pointer to that widget within his data type.
--
--  (For an example showing the use of that package, please see
--  GVD.Text_Box.Source_Editor.Builtin)

generic
   type User_Type (<>) is private;
   type Widget_Type is new Gtk.Widget.Gtk_Widget_Record with private;
   with procedure Draw_Tooltip
     (Widget : access Widget_Type'Class;
      Data   : in out User_Type;
      Pixmap : out Gdk.Pixmap.Gdk_Pixmap;
      Width  : out Glib.Gint;
      Height : out Glib.Gint;
      Area   : out Gdk.Rectangle.Gdk_Rectangle) is <>;
   --  Subprogram called every time a tooltip needs to be drawn.
   --  Width and Height should either contain the size of the pixmap on exit,
   --  or (0, 0) if no tooltip could be displayed.
   --  It is the responsability of this function to get the coordinates of
   --  the pointer, using Gdk.Window.Get_Pointer.
   --  Area indicates the area of effectiveness of the tooltip : if the user
   --  moves the mouse within this area after the tooltip is displayed, then
   --  the tooltip is hidden, and will not be displayed again as long as the
   --  user stays within this area. The X, Y coordinates of the rectangle
   --  should be relative to Widget.

package GVD.Tooltips is

   Default_Timeout : constant Glib.Guint32 := 600;
   --  The delay before a tooltip is displayed, in milliseconds)

   type Tooltips_Record is private;

   type Tooltips is access Tooltips_Record;

   procedure Set_Timeout
     (Tooltip : in out Tooltips;
      T       : in Glib.Guint32);
   --  Set a new delay for the tooltips.

   procedure New_Tooltip
     (Widget  : access Widget_Type'Class;
      Data    : in User_Type;
      Tooltip : out Tooltips);
   --  Create tooltips information for the widget.
   --  The widget must have a window.

   procedure Set_Data
     (Tooltip : in out Tooltips;
      Data    : in User_Type);
   --  Set the data associated with the tooltip.

   function Get_Data (Tooltip : in Tooltips) return User_Type;
   --  Return the data associated with the tooltip.

   procedure Destroy_Tooltip (Tooltip : in out Tooltips);
   --  Free memory allocated to the tooltip.

private

   type Widget_Type_Access is access all Widget_Type'Class;

   type User_Type_Access is access User_Type;

   type Tooltips_Record is record
      Timeout : Glib.Guint32 := Default_Timeout;
      --  The delay before draw function is called.

      Active : Boolean := False;
      --  States whether tooltips should be displayed when drawing
      --  is complete.

      Parent_Window : Gdk.Window.Gdk_Window;
      --  The window which contains the tooltip.

      Display_Window : Gtk.Window.Gtk_Window;
      --  The window in which the tooltip will be displayed.

      Handler_Id : Gtk.Main.Timeout_Handler_Id;
      --  Reference in case handler should be blocked.

      Data : User_Type_Access;
      --  User data.

      Widget : Widget_Type_Access;
      --  The widget on which the tooltip is set.

      X, Y : Glib.Gint;
      --  The mouse coordinates associated with the last call to Draw_Tooltip.

      Area : Gdk.Rectangle.Gdk_Rectangle;
      --  The area of efficiency for the tooltip.
      --  (See Draw_Tooltip specification for details).
   end record;

   package Tooltip_Handler is new Gtk.Handlers.User_Return_Callback
     (Widget_Type => Widget_Type,
      Return_Type => Boolean,
      User_Type   => Tooltips);

   function Mouse_Event_Cb
     (Widget  : access Widget_Type'Class;
      Event   : Gdk.Event.Gdk_Event;
      Tooltip :  Tooltips) return Boolean;
   --  Callback for all mouse events that will disable the tooltip
   --  e.g: focus_in/focus_out/motion_notify/button_clicked

end GVD.Tooltips;
