------------------------------------------------------------------------------
--                                  G P S                                   --
--                                                                          --
--                     Copyright (C) 2009-2012, AdaCore                     --
--                                                                          --
-- This is free software;  you can redistribute it  and/or modify it  under --
-- terms of the  GNU General Public License as published  by the Free Soft- --
-- ware  Foundation;  either version 3,  or (at your option) any later ver- --
-- sion.  This software is distributed in the hope  that it will be useful, --
-- but WITHOUT ANY WARRANTY;  without even the implied warranty of MERCHAN- --
-- TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public --
-- License for  more details.  You should have  received  a copy of the GNU --
-- General  Public  License  distributed  with  this  software;   see  file --
-- COPYING3.  If not, go to http://www.gnu.org/licenses for a complete copy --
-- of the license.                                                          --
------------------------------------------------------------------------------

with GNAT.Strings;
with Interfaces.C.Strings;

with Glib.Object;
with Gtkada.Handlers;          use Gtkada.Handlers;
with Gtk.Check_Button;         use Gtk.Check_Button;
with Gtk.Editable;
with Gtk.Enums;                use Gtk.Enums;
with Gtk.GEntry;               use Gtk.GEntry;
with Gtk.Separator_Tool_Item;  use Gtk.Separator_Tool_Item;
with Gtk.Handlers;
with Gtk.Toggle_Button;
with Gtk.Widget;

with GPS.Kernel;      use GPS.Kernel;
with GPS.Intl;        use GPS.Intl;
with GPS.Stock_Icons; use GPS.Stock_Icons;
with Histories;       use Histories;

package body GPS.Location_View_Filter_Panel is

   use type GNAT.Strings.String_Access;

   Hist_Is_Regexp  : constant History_Key := "locations-filter-is-regexp";
   Hist_Hide_Match : constant History_Key := "locations-filter-hide-matches";

   Class_Record : Glib.Object.Ada_GObject_Class :=
      Glib.Object.Uninitialized_Class;

   Signals : constant Interfaces.C.Strings.chars_ptr_array (1 .. 3) :=
     (1 => Interfaces.C.Strings.New_String (String (Signal_Apply_Filter)),
      2 => Interfaces.C.Strings.New_String (String (Signal_Cancel_Filter)),
      3 => Interfaces.C.Strings.New_String
            (String (Signal_Visibility_Toggled)));

   Signals_Parameters : constant
     Glib.Object.Signal_Parameter_Types (1 .. 3, 1 .. 1) :=
       (1 => (others => Glib.GType_None),
        2 => (others => Glib.GType_None),
        3 => (others => Glib.GType_None));

   procedure Apply_Filter
     (Self : not null access Locations_Filter_Panel_Record'Class);

   procedure On_Pattern_Changed
     (Object : access Gtk.GEntry.Gtk_Entry_Record'Class;
      Self   : Locations_Filter_Panel);
   --  Called on pattern entry change

   procedure On_Hide_Matched_Toggle
     (Object : access Gtk.Check_Button.Gtk_Check_Button_Record'Class;
      Self   : Locations_Filter_Panel);
   --  Called on hide matched toggle

   procedure On_Regexp_Toggle
     (Object : access Gtk.Check_Button.Gtk_Check_Button_Record'Class;
      Self   : Locations_Filter_Panel);
   --  Called on regexp toggle

   procedure On_Clear_Entry
     (Object : access Gtk.Widget.Gtk_Widget_Record'Class);
   --  Clear the contents of the entry

   package Gtk_Entry_Callbacks is
     new Gtk.Handlers.User_Callback
          (Gtk.GEntry.Gtk_Entry_Record, Locations_Filter_Panel);

   package Gtk_Check_Button_Callbacks is
     new Gtk.Handlers.User_Callback
          (Gtk.Check_Button.Gtk_Check_Button_Record, Locations_Filter_Panel);

   package Locations_Filter_Panel_Callbacks is
     new Gtk.Handlers.Callback (Locations_Filter_Panel_Record);

   ------------------
   -- Apply_Filter --
   ------------------

   procedure Apply_Filter
     (Self : not null access Locations_Filter_Panel_Record'Class)
   is
      Pattern : constant String := Self.Pattern.Get_Text;
   begin
      if Pattern = "" then
         Locations_Filter_Panel_Callbacks.Emit_By_Name
           (Self, Signal_Cancel_Filter);
      else
         Locations_Filter_Panel_Callbacks.Emit_By_Name
           (Self, Signal_Apply_Filter);
      end if;
   end Apply_Filter;

   ----------------------
   -- Get_Hide_Matched --
   ----------------------

   function Get_Hide_Matched
     (Self : not null access Locations_Filter_Panel_Record'Class)
      return Boolean is
   begin
      return Get_History (Get_History (Self.Kernel).all, Hist_Hide_Match);
   end Get_Hide_Matched;

   -------------------
   -- Get_Is_Regexp --
   -------------------

   function Get_Is_Regexp
     (Self : not null access Locations_Filter_Panel_Record'Class)
      return Boolean is
   begin
      return Get_History (Get_History (Self.Kernel).all, Hist_Is_Regexp);
   end Get_Is_Regexp;

   -----------------
   -- Get_Pattern --
   -----------------

   function Get_Pattern
     (Self : not null access Locations_Filter_Panel_Record'Class)
      return String
   is
   begin
      return Self.Pattern.Get_Text;
   end Get_Pattern;

   -----------------------
   -- Create_And_Append --
   -----------------------

   function Create_And_Append
     (Kernel  : GPS.Kernel.Kernel_Handle;
      Toolbar : not null access Gtk.Toolbar.Gtk_Toolbar_Record'Class)
      return Locations_Filter_Panel
   is
      Panel  : constant Locations_Filter_Panel :=
        new Locations_Filter_Panel_Record;
      Item   : Gtk.Tool_Item.Gtk_Tool_Item;
      Regexp : Gtk_Check_Button;
      Hide   : Gtk_Check_Button;
      Sep    : Gtk_Separator_Tool_Item;
   begin
      Gtk.Tool_Item.Initialize (Panel);
      Glib.Object.Initialize_Class_Record
        (Panel,
         Signals,
         Class_Record,
         "GPSLocationViewFilterPanel",
         Signals_Parameters);

      Panel.Kernel := Kernel;

      Gtk_New (Sep);
      Toolbar.Insert (Sep);

      --  Pattern entry

      Gtk.GEntry.Gtk_New (Panel.Pattern);
      Panel.Pattern.Set_Icon_From_Stock
        (Gtk_Entry_Icon_Secondary, GPS_Clear_Entry);
      Panel.Pattern.Set_Icon_Activatable (Gtk_Entry_Icon_Secondary, True);
      Panel.Pattern.Set_Icon_Tooltip_Text
        (Gtk_Entry_Icon_Secondary, -"Clear the pattern");
      Panel.Pattern.Set_Placeholder_Text (-"filter");
      Panel.Pattern.Set_Tooltip_Text
        (-"The text pattern or regular expression");
      Gtk_Entry_Callbacks.Connect
        (Panel.Pattern,
         Gtk.Editable.Signal_Changed,
         Gtk_Entry_Callbacks.To_Marshaller (On_Pattern_Changed'Access),
         Panel);
      Widget_Callback.Connect
        (Panel.Pattern, Gtk.GEntry.Signal_Icon_Press, On_Clear_Entry'Access);

      Panel.Add (Panel.Pattern);
      Toolbar.Insert (Panel);

      --  Regexp check button

      Gtk_New (Regexp, Label => -"Regexp");
      Associate (Get_History (Kernel).all, Hist_Is_Regexp, Regexp,
                 Default => True);
      Regexp.Set_Tooltip_Text
        (-"Whether filter is a regular expression");
      Gtk_Check_Button_Callbacks.Connect
        (Regexp,
         Gtk.Toggle_Button.Signal_Toggled,
         Gtk_Check_Button_Callbacks.To_Marshaller
           (On_Regexp_Toggle'Access),
         Panel);

      Gtk.Tool_Item.Gtk_New (Item);
      Item.Add (Regexp);
      Toolbar.Insert (Item);

      --  Hide matched check button

      Gtk_New (Hide, Label => -"Hide matches");
      Associate (Get_History (Kernel).all, Hist_Hide_Match, Hide,
                 Default => False);
      Hide.Set_Tooltip_Text (-"Revert filter: hide matching items");
      Gtk_Check_Button_Callbacks.Connect
        (Hide,
         Gtk.Toggle_Button.Signal_Toggled,
         Gtk_Check_Button_Callbacks.To_Marshaller
           (On_Hide_Matched_Toggle'Access),
         Panel);

      Gtk.Tool_Item.Gtk_New (Item);
      Item.Add (Hide);
      Toolbar.Insert (Item);

      return Panel;
   end Create_And_Append;

   --------------------
   -- On_Clear_Entry --
   --------------------

   procedure On_Clear_Entry
     (Object : access Gtk.Widget.Gtk_Widget_Record'Class)
   is
   begin
      Gtk_GEntry (Object).Set_Text ("");
   end On_Clear_Entry;

   ----------------------------
   -- On_Hide_Matched_Toggle --
   ----------------------------

   procedure On_Hide_Matched_Toggle
     (Object : access Gtk.Check_Button.Gtk_Check_Button_Record'Class;
      Self   : Locations_Filter_Panel)
   is
      pragma Unreferenced (Object);

   begin
      if Self.Pattern.Get_Text /= "" then
         Locations_Filter_Panel_Callbacks.Emit_By_Name
           (Self, Signal_Visibility_Toggled);
      end if;
   end On_Hide_Matched_Toggle;

   ----------------------
   -- On_Regexp_Toggle --
   ----------------------

   procedure On_Regexp_Toggle
     (Object : access Gtk.Check_Button.Gtk_Check_Button_Record'Class;
      Self   : Locations_Filter_Panel)
   is
      pragma Unreferenced (Object);
   begin
      Self.Apply_Filter;
   end On_Regexp_Toggle;

   ------------------------
   -- On_Pattern_Changed --
   ------------------------

   procedure On_Pattern_Changed
     (Object : access Gtk.GEntry.Gtk_Entry_Record'Class;
      Self   : Locations_Filter_Panel)
   is
      pragma Unreferenced (Object);
   begin
      Self.Apply_Filter;
   end On_Pattern_Changed;

end GPS.Location_View_Filter_Panel;
