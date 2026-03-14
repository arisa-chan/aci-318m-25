import FreeSimpleGUIQt as sg
import math

# Import your custom ACI backend libraries
from aci318m25 import *
from aci318m25_column import *

# Define the visual theme
sg.theme('LightGrey1')

# --- 1. Left Side: Inputs and Outputs ---

# Group A: Material & Seismic 
# Using Dropdowns to strictly match the Enums in your aci318m25.py file
material_layout = [
    [sg.Text("f'c (MPa):", size=(10, 1)), 
     sg.Combo(['14', '17', '21', '28', '35', '42', '50', '55', '70', '80', '100'], default_value='28', key="-FC-", readonly=True, size=(6, 1)),
     sg.Text("fy/fyt (MPa):", size=(12, 1)), 
     sg.Combo(['280', '420', '520', '550'], default_value='420', key="-FY-", readonly=True, size=(6, 1))]
]

seismic_layout = [
    [sg.Text("Category:", size=(10, 1)), 
     sg.Combo(['A', 'B', 'C', 'D', 'E', 'F'], default_value='D', key="-SDC-", readonly=True, size=(6, 1)),
     sg.Text("System:", size=(8, 1)), 
     sg.Combo(['ORDINARY', 'INTERMEDIATE', 'SPECIAL'], default_value='SPECIAL', key="-FRAME-", readonly=True, size=(12, 1))]
]

# Group B: Geometry
geometry_layout = [
    [sg.Text("Width (mm):", size=(16, 1)), sg.InputText("400", key="-WIDTH-", size=(8, 1)),
     sg.Text("Depth (mm):", size=(16, 1)), sg.InputText("600", key="-DEPTH-", size=(8, 1))],
    [sg.Text("Floor-to-Floor (mm):", size=(16, 1)), sg.InputText("3200", key="-H_FF-", size=(8, 1)),
     sg.Text("Floor-to-Soffit (mm):", size=(16, 1)), sg.InputText("2700", key="-H_SOFFIT-", size=(8, 1))],
    [sg.Text("Clear Cover (mm):", size=(16, 1)), sg.InputText("40", key="-COVER-", size=(8, 1)),
     sg.Text("k-factor:", size=(16, 1)), sg.InputText("1.0", key="-K_FACTOR-", size=(8, 1))]
]

# Group C: Loads
loads_layout = [
    [sg.Text("Pu (kN):", size=(8, 1)), sg.InputText("3960", key="-PU-", size=(8, 1)),
     sg.Text("Mux (kN-m):", size=(10, 1)), sg.InputText("507.4", key="-MUX-", size=(8, 1)),
     sg.Text("Muy (kN-m):", size=(10, 1)), sg.InputText("0", key="-MUY-", size=(8, 1))],
    [sg.Text("Vux (kN):", size=(8, 1)), sg.InputText("151", key="-VUX-", size=(8, 1)),
     sg.Text("Vuy (kN):", size=(10, 1)), sg.InputText("0", key="-VUY-", size=(8, 1))]
]

# Group D: Results & Reinforcement Outputs (Set to Read-Only)
results_layout = [
    [sg.Text("Main bars (X face):", size=(18, 1)), sg.InputText("", key="-NBX-", size=(6, 1), readonly=True),
     sg.Text("Main bars (Y face):", size=(18, 1)), sg.InputText("", key="-NBY-", size=(6, 1), readonly=True)],
    [sg.Text("Main bar dia (mm):", size=(18, 1)), sg.InputText("", key="-DMAIN-", size=(6, 1), readonly=True),
     sg.Text("Tie dia (mm):", size=(18, 1)), sg.InputText("", key="-DTIE-", size=(6, 1), readonly=True)],
    [sg.Text("Tie legs (X dir):", size=(18, 1)), sg.InputText("", key="-TLEGX-", size=(6, 1), readonly=True),
     sg.Text("Tie legs (Y dir):", size=(18, 1)), sg.InputText("", key="-TLEGY-", size=(6, 1), readonly=True)],
    [sg.Text("Tie spacing confine:", size=(22, 1)), sg.InputText("", key="-SCONF-", size=(6, 1), readonly=True),
     sg.Text("Midheight:", size=(14, 1)), sg.InputText("", key="-SMID-", size=(6, 1), readonly=True)],
    [sg.Text("Overall DCR:", size=(18, 1)), sg.InputText("", key="-DCR-", size=(6, 1), readonly=True, text_color="blue")]
]

# Assemble the Left Panel
left_column = [
    [sg.Frame("Material Properties", material_layout)],
    [sg.Frame("Seismic & Frame Information", seismic_layout)],
    [sg.Frame("Column Geometry", geometry_layout)],
    [sg.Frame("Factored Column Loads", loads_layout)],
    [sg.Frame("Calculated Reinforcement", results_layout)],
    [sg.Button("Run ACI 318 Design", size=(20, 2)), sg.Button("Exit", size=(10, 2))]
]

# --- 2. Right Side: Graphical Visualization ---
graph_layout = [
    [sg.Text("Cross-Section Visualizer", font=("Helvetica", 14, "bold"), justification="center")],
    [sg.Graph(canvas_size=(500, 500), graph_bottom_left=(0, 0), graph_top_right=(500, 500), 
              background_color='white', key='-CANVAS-')]
]

# --- 3. Main Window Layout ---
layout = [
    [sg.Text("ACI 318M-25 Advanced Column Designer", font=("Helvetica", 18, "bold"))],
    [sg.Column(left_column, vertical_alignment='top'), 
     sg.VSeparator(), 
     sg.Column(graph_layout, vertical_alignment='top')]
]

window = sg.Window("Structural Engineering App", layout, finalize=True)
graph = window['-CANVAS-']

def draw_section(values):
    graph.erase() 
    try:
        w = float(values['-WIDTH-'])
        d = float(values['-DEPTH-'])
        cover = float(values['-COVER-'])
        nbx = int(values['-NBX-'])
        nby = int(values['-NBY-'])
        d_main = float(values['-DMAIN-'])
        d_tie = float(values['-DTIE-'])
        tlegx = int(values['-TLEGX-'])
        tlegy = int(values['-TLEGY-'])
        
        scale = 400 / max(w, d)
        sw, sd, scover = w * scale, d * scale, cover * scale
        sd_main, sd_tie = d_main * scale, d_tie * scale
        cx, cy = 250, 250 
        
        # Concrete Outline
        conc_left, conc_right = cx - sw/2, cx + sw/2
        conc_top, conc_bottom = cy + sd/2, cy - sd/2
        graph.draw_rectangle((conc_left, conc_top), (conc_right, conc_bottom), fill_color='#E8E8E8', line_color='black', line_width=2)
        
        # Outer Tie
        tie_left, tie_right = conc_left + scover, conc_right - scover
        tie_top, tie_bottom = conc_top - scover, conc_bottom + scover
        graph.draw_rectangle((tie_left, tie_top), (tie_right, tie_bottom), fill_color=None, line_color='blue', line_width=2)
        
        # Inner Ties
        eff_cover = scover + sd_tie + (sd_main / 2)
        bar_left, bar_right = conc_left + eff_cover, conc_right - eff_cover
        bar_top, bar_bottom = conc_top - eff_cover, conc_bottom + eff_cover
        
        dx = (bar_right - bar_left) / (nbx - 1) if nbx > 1 else 0
        dy = (bar_top - bar_bottom) / (nby - 1) if nby > 1 else 0
        
        if tlegx > 2 and nbx > 2:
            legs_to_draw = min(tlegx - 2, nbx - 2)
            step = (nbx - 1) / (legs_to_draw + 1)
            for i in range(1, legs_to_draw + 1):
                x_pos = bar_left + int(round(i * step)) * dx
                graph.draw_line((x_pos, tie_top), (x_pos, tie_bottom), color='blue', width=1)
                
        if tlegy > 2 and nby > 2:
            legs_to_draw = min(tlegy - 2, nby - 2)
            step = (nby - 1) / (legs_to_draw + 1)
            for i in range(1, legs_to_draw + 1):
                y_pos = bar_bottom + int(round(i * step)) * dy
                graph.draw_line((tie_left, y_pos), (tie_right, y_pos), color='blue', width=1)

        # Main Rebar
        radius = max(sd_main / 2, 3) 
        for i in range(nbx):
            x = bar_left + i * dx
            graph.draw_circle((x, bar_top), radius, fill_color='red', line_color='darkred')
            graph.draw_circle((x, bar_bottom), radius, fill_color='red', line_color='darkred')
            
        for j in range(1, nby - 1):
            y = bar_bottom + j * dy
            graph.draw_circle((bar_left, y), radius, fill_color='red', line_color='darkred')
            graph.draw_circle((bar_right, y), radius, fill_color='red', line_color='darkred')

    except Exception:
        pass # Silently pass if inputs aren't ready yet

# --- 4. Event Loop ---
while True:
    event, values = window.read()
    
    if event == sg.WIN_CLOSED or event == "Exit":
        break
        
    if event == "Run ACI 318 Design":
        try:
            # 1. Initialize Backend
            aci = ACI318M25()
            column_design = ACI318M25ColumnDesign()

            # 2. Map Material Enums
            fc_enum = getattr(ConcreteStrengthClass, f"FC{values['-FC-']}")
            fy_enum = getattr(ReinforcementGrade, f"GRADE{values['-FY-']}")
            material = aci.get_material_properties(concrete_class=fc_enum, steel_grade=fy_enum)

            # 3. Create Geometry Object
            w = float(values['-WIDTH-'])
            d = float(values['-DEPTH-'])
            column = ColumnGeometry(
                width=w,
                depth=d,
                height=float(values['-H_FF-']),
                clear_height=float(values['-H_SOFFIT-']),
                cover=float(values['-COVER-']),
                shape=ColumnShape.RECTANGULAR,
                column_type=ColumnType.TIED,
                effective_length=float(values['-K_FACTOR-']) * float(values['-H_FF-']),
                sdc=SeismicDesignCategory[values['-SDC-']],
                frame_system=FrameSystem[values['-FRAME-']]
            )

            # 4. Create Loads Object
            mux, muy = float(values['-MUX-']), float(values['-MUY-'])
            load_cond = LoadCondition.BIAXIAL_BENDING if (mux > 0 and muy > 0) else LoadCondition.UNIAXIAL_BENDING
            loads = ColumnLoads(
                axial_force=float(values['-PU-']),
                moment_x=mux,
                moment_y=muy,
                shear_x=float(values['-VUX-']),
                shear_y=float(values['-VUY-']),
                load_condition=load_cond
            )

            # 5. Execute Core Design Routine
            result = column_design.perform_complete_column_design(loads=loads, geometry=column, material_props=material)

            # 6. Extract Results and calculate face distributions
            num_bars = len(result.reinforcement.longitudinal_bars)
            d_main = result.reinforcement.longitudinal_bars[0].replace('D', '')
            d_tie = result.reinforcement.tie_bars.replace('D', '')
            
            # Recreate face distribution logic to inform the drawer
            nx = max(2, int(round((w / (w + d)) * (num_bars / 2.0))) + 1)
            ny = max(2, int((num_bars + 4 - 2 * nx) / 2))

            # 7. Update GUI Fields
            window['-NBX-'].update(nx)
            window['-NBY-'].update(ny)
            window['-DMAIN-'].update(d_main)
            window['-DTIE-'].update(d_tie)
            window['-TLEGX-'].update(result.reinforcement.tie_legs_x)
            window['-TLEGY-'].update(result.reinforcement.tie_legs_y)
            window['-SCONF-'].update(result.reinforcement.tie_spacing)
            window['-SMID-'].update(result.reinforcement.tie_spacing) # Using same for now
            window['-DCR-'].update(f"{result.utilization_ratio:.2f}")

            # 8. Update Dictionary and Trigger Visualizer
            values.update({
                '-NBX-': nx, '-NBY-': ny, 
                '-DMAIN-': d_main, '-DTIE-': d_tie, 
                '-TLEGX-': result.reinforcement.tie_legs_x, 
                '-TLEGY-': result.reinforcement.tie_legs_y
            })
            draw_section(values)
            
            # 9. Pop up the backend design notes
            notes_str = "\n".join(f"• {note}" for note in result.design_notes)
            sg.popup_scrolled("Analysis Complete!\n\nDesign Notes & Warnings:", notes_str, title="Results")

        except Exception as e:
            sg.popup_error(f"Design Error. Please check your inputs.\nDetails: {e}")

window.close()