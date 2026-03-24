# %%
import math
import re
import FreeSimpleGUI as sg
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade
from aci318m25_beam import (
    ACI318M25BeamDesign, BeamGeometry, BeamType, 
    SeismicDesignCategory, FrameSystem
)

def get_bar_diameter(bar_str):
    """Helper to extract integer diameter from a string like 'D20' or '20M'"""
    if not bar_str or bar_str == 'None': 
        return 10
    match = re.search(r'\d+', bar_str)
    return int(match.group()) if match else 10

def draw_cross_section(graph, beam, reinf):
    """Draws the beam concrete, stirrups, flexural bars, and torsion side-bars"""
    graph.erase()
    if not beam or not reinf: 
        return
    
    W = beam.width
    H = beam.height
    cover = beam.cover
    
    # Scale to fit 1000x1000 logical canvas with a 10% margin
    scale = 800 / max(W, H)
    scaled_W = W * scale
    scaled_H = H * scale
    
    # Center coordinates
    cx, cy = 500, 500
    xl = cx - scaled_W / 2
    xr = cx + scaled_W / 2
    yb = cy - scaled_H / 2
    yt = cy + scaled_H / 2
    
    # 1. Draw Concrete
    graph.draw_rectangle((xl, yt), (xr, yb), fill_color='#E8E8E8', line_color='black', line_width=2)
    
    # 2. Draw Stirrup
    d_tie = get_bar_diameter(reinf.stirrups)
    if reinf.stirrups and reinf.stirrups != 'None':
        c_s = cover * scale
        graph.draw_rectangle((xl + c_s, yt - c_s), (xr - c_s, yb + c_s), fill_color=None, line_color='blue', line_width=3)
    
    # Helper to draw layered flexural bars
    def draw_bar_layers(bar_list, is_top=False):
        if not bar_list: return 0
        d_bar = get_bar_diameter(bar_list[0])
        num_bars = len(bar_list)
        
        avail_w = W - 2 * cover - 2 * d_tie
        min_spc = max(25.0, d_bar)
        
        max_per_layer = max(2, math.floor((avail_w + min_spc) / (d_bar + min_spc)))
        
        bars_drawn = 0
        layer = 0
        color = 'darkgreen' if is_top else 'red'
        last_y_center = 0
        
        while bars_drawn < num_bars:
            bars_in_this_layer = min(max_per_layer, num_bars - bars_drawn)
            
            # Y-coordinate calculation
            offset = cover + d_tie + (d_bar / 2) + layer * (d_bar + 25.0)
            y_center = (yt - offset * scale) if is_top else (yb + offset * scale)
            last_y_center = y_center
            
            # X-coordinate distribution
            if bars_in_this_layer == 1:
                x_centers = [cx]
            else:
                step = (avail_w - d_bar) / (bars_in_this_layer - 1) * scale
                start_x = xl + (cover + d_tie + d_bar / 2) * scale
                x_centers = [start_x + i * step for i in range(bars_in_this_layer)]
            
            for x in x_centers:
                r = (d_bar / 2) * scale
                graph.draw_circle((x, y_center), r, fill_color=color, line_color='black')
            
            bars_drawn += bars_in_this_layer
            layer += 1
            
        return last_y_center # Return the innermost boundary for torsion bar placement

    # 3. Draw Main Tension Bars (Bottom - Red)
    inner_bottom_y = draw_bar_layers(reinf.main_bars, is_top=False)
    if inner_bottom_y == 0: inner_bottom_y = yb + (cover + d_tie + 20) * scale
    
    # 4. Draw Compression Bars (Top - Green)
    inner_top_y = draw_bar_layers(reinf.compression_bars, is_top=True)
    if inner_top_y == 0: inner_top_y = yt - (cover + d_tie + 20) * scale

    # 5. Draw Torsion Longitudinal Bars (Sides - Orange)
    if reinf.torsion_required and reinf.torsion_longitudinal_area > 0:
        # Assume D16 bars for side skin reinforcement visualization (Area approx 201 mm²)
        d_tbar = 16
        a_tbar = 201.06
        # Distribute Al to the two vertical side faces
        num_side_bars_total = max(2, math.ceil(reinf.torsion_longitudinal_area / a_tbar))
        if num_side_bars_total % 2 != 0: 
            num_side_bars_total += 1 # Ensure symmetry
            
        num_per_side = num_side_bars_total // 2
        
        # Prevent extreme visual clutter if Al is massively huge
        num_per_side = min(num_per_side, 8) 
        
        r_tbar = (d_tbar / 2) * scale
        x_left = xl + (cover + d_tie + d_tbar / 2) * scale
        x_right = xr - (cover + d_tie + d_tbar / 2) * scale
        
        # Space them evenly between the flexural layers
        if num_per_side > 0:
            step_y = (inner_top_y - inner_bottom_y) / (num_per_side + 1)
            for i in range(1, num_per_side + 1):
                y_pos = inner_bottom_y + i * step_y
                graph.draw_circle((x_left, y_pos), r_tbar, fill_color='darkorange', line_color='black')
                graph.draw_circle((x_right, y_pos), r_tbar, fill_color='darkorange', line_color='black')


def create_gui():
    sg.theme('LightGrey1')

    # Data mappings for dropdowns
    concrete_keys = [e.name for e in ConcreteStrengthClass]
    steel_keys = [e.name for e in ReinforcementGrade]
    beam_type_keys = [e.name for e in BeamType]
    sdc_keys = [e.name for e in SeismicDesignCategory]
    frame_keys = [e.name for e in FrameSystem]

    # --- LEFT COLUMN (Inputs) ---
    material_frame = sg.Frame('Material Properties', [
        [sg.Text('Concrete Class:', size=(14, 1)), sg.Combo(concrete_keys, default_value='FC28', key='-FC-', size=(12, 1))],
        [sg.Text('Steel Grade:', size=(14, 1)), sg.Combo(steel_keys, default_value='GRADE420', key='-FY-', size=(12, 1))]
    ])

    geometry_frame = sg.Frame('Beam Geometry (mm)', [
        [sg.Text('Length:', size=(8, 1)), sg.Input('6000', key='-L-', size=(8, 1)),
         sg.Text('Width:', size=(6, 1)), sg.Input('300', key='-W-', size=(8, 1))],
        [sg.Text('Height:', size=(8, 1)), sg.Input('600', key='-H-', size=(8, 1)),
         sg.Text('Eff. d:', size=(6, 1)), sg.Input('535', key='-D-', size=(8, 1))],
        [sg.Text('Cover:', size=(8, 1)), sg.Input('40', key='-COVER-', size=(8, 1)),
         sg.Text('Cl. Span:', size=(6, 1)), sg.Input('5600', key='-CLEAR-', size=(8, 1))]
    ])

    seismic_frame = sg.Frame('System & Seismic Parameters', [
        [sg.Text('Beam Type:', size=(14, 1)), sg.Combo(beam_type_keys, default_value='RECTANGULAR', key='-BTYPE-', size=(15, 1))],
        [sg.Text('Seismic Category:', size=(14, 1)), sg.Combo(sdc_keys, default_value='D', key='-SDC-', size=(15, 1))],
        [sg.Text('Frame System:', size=(14, 1)), sg.Combo(frame_keys, default_value='SPECIAL', key='-FRAME-', size=(15, 1))]
    ])

    loads_frame = sg.Frame('Design Loads', [
        [sg.Text('Mu (kN⋅m):', size=(12, 1)), sg.Input('200', key='-MU-', size=(8, 1)),
         sg.Text('Vu (kN):', size=(8, 1)), sg.Input('200', key='-VU-', size=(8, 1))],
        [sg.Text('Srv. Mu (kN⋅m):', size=(12, 1)), sg.Input('300', key='-SMU-', size=(8, 1)),
         sg.Text('Tu (kN⋅m):', size=(8, 1)), sg.Input('35', key='-TU-', size=(8, 1))], # Defaulted Tu to 35 to show off torsion
        [sg.Text('Grav. Shear (kN):', size=(12, 1)), sg.Input('100', key='-GSHEAR-', size=(8, 1))]
    ])

    left_column = [
        [material_frame],
        [geometry_frame],
        [seismic_frame],
        [loads_frame],
        [sg.Button('Calculate Design', size=(18, 2), button_color='darkblue', font=('Helvetica', 10, 'bold')), sg.Button('Exit', size=(10, 2))]
    ]

    # --- RIGHT COLUMN (Outputs & Visualization) ---
    output_frame = sg.Frame('Results & Reinforcement', [
        [sg.Multiline(size=(55, 14), key='-OUTPUT-', disabled=True, font='Courier 10')]
    ])

    graph_elem = sg.Graph(
        canvas_size=(380, 380), 
        graph_bottom_left=(0, 0), 
        graph_top_right=(1000, 1000), 
        background_color='white', 
        key='-GRAPH-'
    )

    visual_frame = sg.Frame('Cross-Section Visualization', [
        [graph_elem],
        [sg.Text("■ Tension (Bot)", text_color='red', background_color='white'),
         sg.Text("■ Comp. (Top)", text_color='darkgreen', background_color='white'),
         sg.Text("■ Stirrups", text_color='blue', background_color='white'),
         sg.Text("■ Torsion (Sides)", text_color='darkorange', background_color='white')]
    ], background_color='white')

    right_column = [
        [output_frame],
        [visual_frame]
    ]

    # --- MAIN LAYOUT ---
    layout = [
        [sg.Text('ACI 318M-25 Beam Designer (Flexure, Shear, Torsion, Seismic)', font=('Helvetica', 14, 'bold'))],
        [sg.Column(left_column, vertical_alignment='top'), sg.Column(right_column, vertical_alignment='top')]
    ]

    window = sg.Window('ACI 318M-25 Beam Designer', layout, finalize=True)
    
    # Initialize Core Classes
    aci = ACI318M25()
    beam_design = ACI318M25BeamDesign()

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Exit'):
            break

        if event == 'Calculate Design':
            try:
                # 1. Fetch Materials
                material = aci.get_material_properties(
                    concrete_class=ConcreteStrengthClass[values['-FC-']],
                    steel_grade=ReinforcementGrade[values['-FY-']]
                )

                # 2. Build Geometry Object
                beam = BeamGeometry(
                    length=float(values['-L-']),
                    width=float(values['-W-']),
                    height=float(values['-H-']),
                    effective_depth=float(values['-D-']),
                    cover=float(values['-COVER-']),
                    flange_width=0,
                    flange_thickness=0,
                    clear_span=float(values['-CLEAR-']),
                    sdc=SeismicDesignCategory[values['-SDC-']],
                    frame_system=FrameSystem[values['-FRAME-']],
                    beam_type=BeamType[values['-BTYPE-']]
                )

                # 3. Perform Analysis
                results = beam_design.perform_complete_beam_design(
                    mu=float(values['-MU-']),
                    vu=float(values['-VU-']),
                    beam_geometry=beam,
                    material_props=material,
                    service_moment=float(values['-SMU-']),
                    tu=float(values['-TU-']),
                    gravity_shear=float(values['-GSHEAR-'])
                )

                # 4. Format and display textual results
                reinf = results.reinforcement
                output_text = "=== REINFORCEMENT DESIGN ===\n"
                output_text += f"Main Tension Bars:   {len(reinf.main_bars)} x {reinf.main_bars[0] if reinf.main_bars else 'N/A'}\n"
                output_text += f"Main Tension Area:   {reinf.main_area:.1f} mm²\n"
                
                if reinf.compression_bars:
                    output_text += f"Compression Bars:    {len(reinf.compression_bars)} x {reinf.compression_bars[0]}\n"
                    output_text += f"Compression Area:    {reinf.compression_area:.1f} mm²\n"
                else:
                    output_text += "Compression Bars:    None required\n"
                
                output_text += f"\n=== SHEAR, TORSION & SEISMIC ===\n"
                output_text += f"Stirrup Size:        {reinf.stirrups}\n"
                if beam.frame_system == FrameSystem.SPECIAL:
                    output_text += f"Hinge Zone Spacing:  {reinf.stirrup_spacing_hinge:.0f} mm (len: {reinf.hinge_length:.0f} mm)\n"
                    output_text += f"Mid-Span Spacing:    {reinf.stirrup_spacing:.0f} mm\n"
                else:
                    output_text += f"Stirrup Spacing:     {reinf.stirrup_spacing:.0f} mm\n"
                
                if reinf.torsion_required:
                    output_text += f"Torsion Long. Steel: {reinf.torsion_longitudinal_area:.1f} mm² (Al distributed)\n"

                output_text += "\n=== DESIGN CAPACITIES ===\n"
                output_text += f"Demand/Capacity:     {results.utilization_ratio:.2f} (Max)\n"
                output_text += f"Moment Capacity:     {results.moment_capacity:.1f} kN⋅m\n"
                output_text += f"Probable Moment:     {results.probable_moment:.1f} kN⋅m\n"
                output_text += f"Design Shear Ve:     {results.capacity_shear_ve:.1f} kN\n"
                if reinf.torsion_required:
                    output_text += f"Torsion Capacity Tn: {results.torsion_capacity:.1f} kN⋅m\n"

                output_text += "\n=== DESIGN NOTES & WARNINGS ===\n"
                if results.design_notes:
                    for note in results.design_notes:
                        output_text += f"- {note}\n"
                else:
                    output_text += "No warnings.\n"

                window['-OUTPUT-'].update(output_text)
                
                # 5. Draw the visualization
                draw_cross_section(window['-GRAPH-'], beam, reinf)

            except ValueError as e:
                sg.popup_error(f"Input Error: Please ensure all numeric fields contain valid numbers.\n\nDetails: {str(e)}")
            except Exception as e:
                sg.popup_error(f"Design Error: {str(e)}")

    window.close()

if __name__ == '__main__':
    create_gui()