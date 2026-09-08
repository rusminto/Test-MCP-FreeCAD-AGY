import xmlrpc.client

proxy = xmlrpc.client.ServerProxy('http://127.0.0.1:9875')

code = '''
import FreeCAD, Part, FreeCADGui, math

doc_name = 'LG_AC_Remote'
try:
    FreeCAD.closeDocument(doc_name)
except Exception:
    pass

doc = FreeCAD.newDocument(doc_name)

# 1. Main body
def make_trapezoid_wire(w_f, w_b, z_b, y_pos):
    pts = [
        FreeCAD.Vector(-w_f/2.0, y_pos, 0.0),
        FreeCAD.Vector(w_f/2.0, y_pos, 0.0),
        FreeCAD.Vector(w_b/2.0, y_pos, z_b),
        FreeCAD.Vector(-w_b/2.0, y_pos, z_b),
        FreeCAD.Vector(-w_f/2.0, y_pos, 0.0)
    ]
    return Part.makePolygon(pts)

sections = [
    (52.0, 44.0, -22.0, -74.0),
    (52.0, 44.0, -21.8, -40.0),
    (52.0, 44.0, -20.2, -10.0),
    (51.6, 43.6, -17.2,  15.0),
    (51.2, 43.0, -15.0,  45.0),
    (50.8, 42.5, -13.8,  74.0),
]

wires = [make_trapezoid_wire(*s) for s in sections]
solid = Part.makeLoft(wires, True, False)

front_edges = [e for e in solid.Edges if e.Length > 100.0 and ((e.Vertexes[0].Point.z + e.Vertexes[1].Point.z)/2.0) > -5.0]
body_base = solid.makeFillet(4.8, front_edges)

back_edges = [e for e in body_base.Edges if e.Length > 100.0 and ((e.Vertexes[0].Point.z + e.Vertexes[1].Point.z)/2.0) < -8.0]
body_base = body_base.makeFillet(8.0, back_edges)

bot_edges = [e for e in body_base.Edges if abs(e.Vertexes[0].Point.y - (-74.0)) < 0.1 and abs(e.Vertexes[1].Point.y - (-74.0)) < 0.1]
body_base = body_base.makeFillet(4.0, bot_edges)

top_edges = [e for e in body_base.Edges if abs(e.Vertexes[0].Point.y - 74.0) < 0.1 and abs(e.Vertexes[1].Point.y - 74.0) < 0.1]
body_base = body_base.makeFillet(2.5, top_edges)

body = body_base

# 2. Top face IR details
sph = Part.makeSphere(1.0)
m_scale = FreeCAD.Matrix()
m_scale.scale(FreeCAD.Vector(6.8, 4.5, 3.6))
ellip_scoop = sph.transformGeometry(m_scale)
ellip_scoop.translate(FreeCAD.Vector(2.0, 73.8, -6.5))
body = body.cut(ellip_scoop)

ir_base_seat = Part.makeCylinder(3.2, 1.2, FreeCAD.Vector(2.0, 68.8, -6.5), FreeCAD.Vector(0, 1, 0))
ir_cyl = Part.makeCylinder(2.2, 2.0, FreeCAD.Vector(2.0, 69.5, -6.5), FreeCAD.Vector(0, 1, 0))
ir_dome = Part.makeSphere(2.2, FreeCAD.Vector(2.0, 71.2, -6.5))
ir_assembly = ir_base_seat.fuse(ir_cyl).fuse(ir_dome)

slot1 = Part.makeBox(1.1, 3.0, 7.0)
slot1.translate(FreeCAD.Vector(18.0, 72.0, -12.8))
slot2 = Part.makeBox(1.1, 3.0, 5.4)
slot2.translate(FreeCAD.Vector(15.3, 72.0, -12.8))
slot3 = Part.makeBox(1.1, 3.0, 3.8)
slot3.translate(FreeCAD.Vector(12.6, 72.0, -12.8))
slots_all = slot1.fuse(slot2).fuse(slot3)
body = body.cut(slots_all)

# 3. Helpers
def make_rounded_rect_btn(w, l, h, r, cx, cy, z_base=0.0):
    b = Part.makeBox(w, l, h)
    b.translate(FreeCAD.Vector(-w/2.0, -l/2.0, 0.0))
    v_e = [e for e in b.Edges if abs(e.Length - h) < 0.05]
    b = b.makeFillet(r, v_e)
    t_e = [e for e in b.Edges if abs(e.Vertexes[0].Point.z - h) < 0.05 and abs(e.Vertexes[1].Point.z - h) < 0.05]
    try:
        b = b.makeFillet(min(r*0.4, h*0.35, 0.5), t_e)
    except Exception:
        pass
    b.translate(FreeCAD.Vector(cx, cy, z_base))
    return b

def make_circle_btn(dia, h, cx, cy, z_base=0.0):
    cyl = Part.makeCylinder(dia/2.0, h, FreeCAD.Vector(cx, cy, z_base), FreeCAD.Vector(0, 0, 1))
    t_e = [e for e in cyl.Edges if abs(e.Vertexes[0].Point.z - (z_base + h)) < 0.05]
    try:
        cyl = cyl.makeFillet(0.5, t_e)
    except Exception:
        pass
    return cyl

def make_half_pill_out(w, l, h, is_left, cx, cy, z_base=0.0):
    r = l / 2.0
    if is_left:
        x_arc_c = -w/2.0 + r
        p_tr = FreeCAD.Vector(w/2.0, l/2.0, 0.0)
        p_br = FreeCAD.Vector(w/2.0, -l/2.0, 0.0)
        p_arc_bot = FreeCAD.Vector(x_arc_c, -l/2.0, 0.0)
        p_arc_mid = FreeCAD.Vector(-w/2.0, 0.0, 0.0)
        p_arc_top = FreeCAD.Vector(x_arc_c, l/2.0, 0.0)
        e_right = Part.makeLine(p_tr, p_br)
        e_bot = Part.makeLine(p_br, p_arc_bot)
        e_arc = Part.Arc(p_arc_bot, p_arc_mid, p_arc_top).toShape()
        e_top = Part.makeLine(p_arc_top, p_tr)
        wire = Part.Wire([e_right, e_bot, e_arc, e_top])
    else:
        x_arc_c = w/2.0 - r
        p_tl = FreeCAD.Vector(-w/2.0, l/2.0, 0.0)
        p_bl = FreeCAD.Vector(-w/2.0, -l/2.0, 0.0)
        p_arc_bot = FreeCAD.Vector(x_arc_c, -l/2.0, 0.0)
        p_arc_mid = FreeCAD.Vector(w/2.0, 0.0, 0.0)
        p_arc_top = FreeCAD.Vector(x_arc_c, l/2.0, 0.0)
        e_left = Part.makeLine(p_tl, p_bl)
        e_bot = Part.makeLine(p_bl, p_arc_bot)
        e_arc = Part.Arc(p_arc_bot, p_arc_mid, p_arc_top).toShape()
        e_top = Part.makeLine(p_arc_top, p_tl)
        wire = Part.Wire([e_left, e_bot, e_arc, e_top])
    
    face = Part.Face(wire)
    solid = face.extrude(FreeCAD.Vector(0, 0, h))
    solid.translate(FreeCAD.Vector(cx, cy, z_base))
    top_edges = [e for e in solid.Edges if abs(e.Vertexes[0].Point.z - (z_base + h)) < 0.05 and abs(e.Vertexes[1].Point.z - (z_base + h)) < 0.05]
    try:
        solid = solid.makeFillet(0.45, top_edges)
    except Exception:
        pass
    return solid

# 4. LCD
LCD_Y = 47.0
lcd_cutout = make_rounded_rect_btn(36.0, 35.0, 1.2, 3.5, 0.0, LCD_Y, z_base=-0.8)
body = body.cut(lcd_cutout)
lcd_glass = make_rounded_rect_btn(30.0, 26.5, 0.4, 1.5, 0.0, LCD_Y + 0.5, z_base=-0.6)

# 5. Buttons
CX = 13.0
R1_Y = 20.0
btn_r1_c1 = make_half_pill_out(9.6, 6.8, 1.8, True, -CX, R1_Y)
btn_power = make_rounded_rect_btn(11.0, 8.0, 2.2, 2.0, 0.0, R1_Y)
btn_r1_c3 = make_half_pill_out(9.6, 6.8, 1.8, False, CX, R1_Y)

R2_Y = 6.0
btn_r2_c1 = make_circle_btn(9.0, 1.8, -CX, R2_Y)
btn_r2_c2 = make_circle_btn(9.0, 1.8, 0.0, R2_Y)
btn_r2_c3 = make_circle_btn(9.0, 1.8, CX, R2_Y)

R3_Y = -8.5
btn_r3_c1 = make_circle_btn(9.0, 1.8, -CX, R3_Y)
btn_r3_c2 = make_circle_btn(9.0, 1.8, 0.0, R3_Y)
btn_r3_c3 = make_circle_btn(9.0, 1.8, CX, R3_Y)

R4_Y = -24.0
btn_r4_c1 = make_half_pill_out(9.6, 6.4, 1.6, True, -CX, R4_Y)
btn_r4_c2 = make_rounded_rect_btn(9.6, 6.4, 1.6, 1.6, 0.0, R4_Y)
btn_r4_c3 = make_half_pill_out(9.6, 6.4, 1.6, False, CX, R4_Y)

R5_Y = -39.0
btn_r5_c1 = make_half_pill_out(9.6, 6.4, 1.6, True, -CX, R5_Y)
btn_r5_c2 = make_rounded_rect_btn(9.6, 6.4, 1.6, 1.4, 0.0, R5_Y)
btn_r5_c3 = make_half_pill_out(9.6, 6.4, 1.6, False, CX, R5_Y)

R6_Y = -51.5
btn_r6_c1 = make_half_pill_out(9.6, 6.4, 1.6, True, -CX, R6_Y)
btn_r6_c2 = make_rounded_rect_btn(9.6, 6.4, 1.6, 1.4, 0.0, R6_Y)
btn_r6_c3 = make_half_pill_out(9.6, 6.4, 1.6, False, CX, R6_Y)

reset_cyl = Part.makeCylinder(0.8, 3.0, FreeCAD.Vector(CX + 0.5, -59.5, -2.0), FreeCAD.Vector(0, 0, 1))
body = body.cut(reset_cyl)

gray_buttons = (
    btn_r1_c1.fuse(btn_r1_c3)
    .fuse(btn_r2_c1).fuse(btn_r2_c2).fuse(btn_r2_c3)
    .fuse(btn_r3_c1).fuse(btn_r3_c2).fuse(btn_r3_c3)
    .fuse(btn_r4_c1).fuse(btn_r4_c2).fuse(btn_r4_c3)
    .fuse(btn_r5_c1).fuse(btn_r5_c2).fuse(btn_r5_c3)
    .fuse(btn_r6_c1).fuse(btn_r6_c2).fuse(btn_r6_c3)
)

# 6. BACK SIDE: HOUSING & BATTERY BAY
BAT_W = 31.0
BAT_L = 67.0
BAT_Y_START = -74.0
BAT_Y_END = -7.0

# 1. Label recess (shallow rectangular pocket, 0.6mm deep)
# At Y=28, back face is at Z ~ -16.2
label_pocket = Part.makeBox(16.0, 24.0, 2.0)
label_pocket.translate(FreeCAD.Vector(-8.0, 16.0, -16.8))
v_e = [e for e in label_pocket.Edges if abs(e.Length - 2.0) < 0.05]
label_pocket = label_pocket.makeFillet(3.5, v_e)
body = body.cut(label_pocket)

# 2. Door Seat Recess Cutout in Remote Enclosure (1.8mm depth for sliding cover)
door_seat_box = Part.makeBox(BAT_W, BAT_L + 0.5, 2.2)
door_seat_box.translate(FreeCAD.Vector(-BAT_W/2.0, -74.5, -22.5))
seat_cutout = body_base.common(door_seat_box)
body = body.cut(seat_cutout)

# 3. Deep Battery Cavity (2x AAA slots with center divider rib)
bat_bay = Part.makeBox(27.0, 54.0, 8.5)
bat_bay.translate(FreeCAD.Vector(-13.5, -68.0, -20.5))
v_e = [e for e in bat_bay.Edges if abs(e.Length - 8.5) < 0.05]
bat_bay = bat_bay.makeFillet(2.0, v_e)

divider = Part.makeBox(1.4, 48.0, 5.5)
divider.translate(FreeCAD.Vector(-0.7, -65.0, -20.5))
bay_with_divider = bat_bay.cut(divider)
body = body.cut(bay_with_divider)

# 4. Internal Latch Slot inside body ceiling (Z = -16.5 to -14.5, purely internal)
latch_slot = Part.makeBox(7.0, 4.0, 2.0)
latch_slot.translate(FreeCAD.Vector(-3.5, -9.5, -16.5))
body = body.cut(latch_slot)

# 5. Continuous Shallow Spherical Thumb Scoop Cutter (Radius 5.5mm, Depth ~0.9mm)
# Back surface at (0, -7.0) is at Z = -19.84.
# Sphere of radius 17.5 centered at (0, -7.0, -36.44) reaches peak Z = -18.94 (0.9mm indentation)
# It spans X in [-5.5, 5.5], Y in [-12.5, -1.5].
R_sph = 17.5
Z_center = -19.84 + 0.90 - R_sph # -36.44
thumb_cutter = Part.makeSphere(R_sph, FreeCAD.Vector(0.0, BAT_Y_END, Z_center))

# Top half of scoop (Y >= BAT_Y_END = -7.0) cut into body
top_box = Part.makeBox(30.0, 15.0, 10.0)
top_box.translate(FreeCAD.Vector(-15.0, BAT_Y_END, -25.0))
top_scoop = thumb_cutter.common(top_box)
body = body.cut(top_scoop)

# 6. Two raised alignment nibs flanking the top half-circle
nib1 = Part.makeSphere(0.7)
nib1.translate(FreeCAD.Vector(-7.5, BAT_Y_END + 1.2, -19.6))
nib2 = Part.makeSphere(0.7)
nib2.translate(FreeCAD.Vector(7.5, BAT_Y_END + 1.2, -19.6))
body = body.fuse(nib1).fuse(nib2)

# 7. Metal Battery Contacts
spring_cyl = Part.makeCylinder(3.2, 3.5, FreeCAD.Vector(-6.5, -67.5, -16.0), FreeCAD.Vector(0, 1, 0))
plate_box = Part.makeBox(6.5, 1.2, 6.5)
plate_box.translate(FreeCAD.Vector(3.2, -67.8, -19.0))
terminals = spring_cyl.fuse(plate_box)

# 7. BATTERY COVER WITH BOTTOM HALF-CIRCLE & SLIDE ARROW
cover_box = Part.makeBox(BAT_W - 0.2, BAT_L, 1.8)
cover_box.translate(FreeCAD.Vector(-(BAT_W - 0.2)/2.0, -74.0, -22.3))
cover_shell = body_base.common(cover_box)

# Bottom half of scoop (Y <= BAT_Y_END = -7.0) cut into cover
bot_box = Part.makeBox(30.0, 15.0, 10.0)
bot_box.translate(FreeCAD.Vector(-15.0, BAT_Y_END - 15.0, -25.0))
bot_scoop = thumb_cutter.common(bot_box)
cover_shell = cover_shell.cut(bot_scoop)

# Internal Latch Hook Tab (UNDERNEATH ONLY, Z = -16.0 to -14.8, completely internal)
hook_tongue = Part.makeBox(5.0, 3.5, 1.2)
hook_tongue.translate(FreeCAD.Vector(-2.5, BAT_Y_END - 1.0, -16.0))
hook_barb = Part.makeBox(5.0, 1.0, 0.7)
hook_barb.translate(FreeCAD.Vector(-2.5, BAT_Y_END + 1.5, -15.5))
hook_full = hook_tongue.fuse(hook_barb)

# Underside battery ribs
rib1 = Part.makeBox(1.2, 34.0, 2.0)
rib1.translate(FreeCAD.Vector(-6.5, -57.0, -20.2))
rib2 = Part.makeBox(1.2, 34.0, 2.0)
rib2.translate(FreeCAD.Vector(5.3, -57.0, -20.2))

# Engraved slide arrow '▼' on the bottom half-circle
p1 = FreeCAD.Vector(-1.8, BAT_Y_END - 2.0, -18.7)
p2 = FreeCAD.Vector( 1.8, BAT_Y_END - 2.0, -18.7)
p3 = FreeCAD.Vector( 0.0, BAT_Y_END - 4.5, -18.7)
arrow_wire = Part.makePolygon([p1, p2, p3, p1])
arrow_face = Part.Face(arrow_wire)
arrow_cut = arrow_face.extrude(FreeCAD.Vector(0, 0, -1.0))

# Tiny grip line above arrow
grip_line = Part.makeBox(3.6, 0.4, 0.3)
grip_line.translate(FreeCAD.Vector(-1.8, BAT_Y_END - 1.2, -19.2))

# Dual Support Feet on cover exterior
foot_l = Part.makeBox(2.8, 5.5, 1.4)
foot_l.translate(FreeCAD.Vector(-11.5, -71.5, -23.4))
v_e = [e for e in foot_l.Edges if abs(e.Length - 1.4) < 0.05]
try:
    foot_l = foot_l.makeFillet(0.6, v_e)
except Exception:
    pass

foot_r = Part.makeBox(2.8, 5.5, 1.4)
foot_r.translate(FreeCAD.Vector(8.7, -71.5, -23.4))
v_e = [e for e in foot_r.Edges if abs(e.Length - 1.4) < 0.05]
try:
    foot_r = foot_r.makeFillet(0.6, v_e)
except Exception:
    pass

battery_cover_assembly = (
    cover_shell
    .fuse(hook_full)
    .fuse(rib1).fuse(rib2)
    .fuse(foot_l).fuse(foot_r)
    .fuse(grip_line)
    .cut(arrow_cut)
)

body_obj = doc.addObject('Part::Feature', 'Remote_Enclosure')
body_obj.Shape = body

cover_obj = doc.addObject('Part::Feature', 'Battery_Cover')
cover_obj.Shape = battery_cover_assembly

terminals_obj = doc.addObject('Part::Feature', 'Battery_Terminals')
terminals_obj.Shape = terminals

power_obj = doc.addObject('Part::Feature', 'Power_Button_Orange')
power_obj.Shape = btn_power

gray_obj = doc.addObject('Part::Feature', 'Keypad_Buttons_Gray')
gray_obj.Shape = gray_buttons

lcd_obj = doc.addObject('Part::Feature', 'LCD_Display_Screen')
lcd_obj.Shape = lcd_glass

ir_obj = doc.addObject('Part::Feature', 'IR_Transmitter_Module')
ir_obj.Shape = ir_assembly

doc.recompute()

# Styling
if FreeCADGui.ActiveDocument:
    gui_body = FreeCADGui.ActiveDocument.getObject('Remote_Enclosure')
    gui_cover = FreeCADGui.ActiveDocument.getObject('Battery_Cover')
    gui_power = FreeCADGui.ActiveDocument.getObject('Power_Button_Orange')
    gui_gray = FreeCADGui.ActiveDocument.getObject('Keypad_Buttons_Gray')
    gui_lcd = FreeCADGui.ActiveDocument.getObject('LCD_Display_Screen')
    gui_ir = FreeCADGui.ActiveDocument.getObject('IR_Transmitter_Module')
    gui_term = FreeCADGui.ActiveDocument.getObject('Battery_Terminals')

    gui_body.ShapeColor = (0.94, 0.94, 0.93)
    gui_cover.ShapeColor = (0.94, 0.94, 0.93)
    gui_power.ShapeColor = (0.95, 0.40, 0.12)
    gui_gray.ShapeColor = (0.84, 0.85, 0.86)
    gui_lcd.ShapeColor = (0.12, 0.20, 0.15)
    gui_ir.ShapeColor = (0.18, 0.18, 0.20)
    gui_term.ShapeColor = (0.75, 0.75, 0.78)

    view = FreeCADGui.ActiveDocument.ActiveView
    art_dir = '/home/rusminto/.gemini/antigravity-cli/brain/fcf4ce68-241d-4056-86d0-409fb647a1a4'
    
    # 1. Back view closed (camera facing back, looking at +Z)
    gui_cover.Visibility = True
    view.setCameraOrientation(FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 180))
    view.fitAll()
    view.saveImage(f'{art_dir}/back_closed_test.png', 1200, 1600, 'Current')
    
    # 2. Back view close-up on the circle dish
    view.setCameraOrientation(FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 180))
    view.fitAll()
    view.zoomIn()
    view.zoomIn()
    view.saveImage(f'{art_dir}/back_dish_closeup.png', 1200, 1200, 'Current')
    
    # 3. Iso view closed
    view.setCameraOrientation(FreeCAD.Rotation(0.24, -0.74, 0.60, 0.18))
    view.fitAll()
    view.saveImage(f'{art_dir}/iso_closed_test.png', 1200, 1600, 'Current')

doc.saveAs('/tmp/freecad/LG_AC_Remote.FCStd')
print('TEST COMPLETE')
'''

res = proxy.execute(code)
print('Execution result:', res)
