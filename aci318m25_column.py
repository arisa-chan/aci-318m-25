# -*- coding: utf-8 -*-

"""
ACI 318M-25 Column Design Library
Building Code Requirements for Structural Concrete - Column Design

Based on:
- ACI CODE-318M-25 International System of Units
- Chapter 10: Axial Force and Combined Bending and Axial Force
- Chapter 21: Special Provisions for Seismic Design
- Chapter 25: Development and Splices of Reinforcement

@author: Enhanced by AI Assistant  
@date: 2024
@version: 1.1 (Iterative Design Engine Update)
"""

import math
from typing import Dict, Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade, MaterialProperties

class ColumnType(Enum):
    """Types of columns for design"""
    TIED = "tied"              # Tied columns with rectangular ties
    SPIRAL = "spiral"          # Spiral columns with spiral reinforcement
    COMPOSITE = "composite"    # Composite columns with structural steel

class ColumnShape(Enum):
    """Column cross-sectional shapes"""
    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"
    L_SHAPED = "l_shaped"
    T_SHAPED = "t_shaped"

class LoadCondition(Enum):
    """Load conditions for column design"""
    AXIAL_ONLY = "axial_only"
    UNIAXIAL_BENDING = "uniaxial_bending"
    BIAXIAL_BENDING = "biaxial_bending"

class SeismicDesignCategory(Enum):
    """Seismic Design Categories (SDC) - ACI 318M-25"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"

class FrameSystem(Enum):
    """Seismic frame system types - ACI 318M-25"""
    ORDINARY = "ordinary"          # Ordinary Moment Frame (OMF)
    INTERMEDIATE = "intermediate"  # Intermediate Moment Frame (IMF)
    SPECIAL = "special"            # Special Moment Frame (SMF)

@dataclass
class ColumnGeometry:
    """Column geometry properties"""
    width: float                            # Column width or diameter (mm)
    depth: float                            # Column depth (mm) - equals width for circular
    height: float                           # Center-to-center column height (mm)
    clear_height: float                     # Clear height of the column lu (mm) - Critical for plastic hinge (lo)
    cover: float                            # Concrete cover (mm)
    shape: ColumnShape                      # Cross-sectional shape
    column_type: ColumnType                 # Type of column
    effective_length: float                 # Effective length for buckling (mm)
    
    # New Seismic Parameters
    sdc: SeismicDesignCategory = SeismicDesignCategory.A
    frame_system: FrameSystem = FrameSystem.ORDINARY

@dataclass
class ColumnLoads:
    """Column load conditions"""
    axial_force: float                      # Factored axial force Pu (kN) - compression positive
    moment_x: float                         # Factored moment about x-axis Mux (kN⋅m)
    moment_y: float                         # Factored moment about y-axis Muy (kN⋅m)
    shear_x: float                          # Factored shear in x-direction Vux (kN)
    shear_y: float                          # Factored shear in y-direction Vuy (kN)
    load_condition: LoadCondition
    
    # New Optional Seismic Parameters for Capacity Design (SDC D, E, F)
    sum_beam_mpr_top: Optional[float] = None  # Sum of probable flexural strengths of beams at top joint (kN⋅m)
    sum_beam_mpr_bot: Optional[float] = None  # Sum of probable flexural strengths of beams at bot joint (kN⋅m)

    # New Optional Seismic Parameters for Strong-Column/Weak-Beam Check (SDC D, E, F)
    sum_beam_mnb_top: Optional[float] = None  # Sum of nominal flexural strengths of beams at top joint (kN⋅m)
    sum_beam_mnb_bot: Optional[float] = None  # Sum of nominal flexural strengths of beams at bot joint (kN⋅m)

@dataclass
class ColumnReinforcement:
    """Column reinforcement design"""
    longitudinal_bars: List[str]    # Longitudinal bar sizes
    longitudinal_area: float        # Total longitudinal steel area (mm²)
    tie_bars: str                   # Tie bar size for tied columns
    tie_spacing: float              # Tie spacing (mm)
    tie_legs_x: int
    tie_legs_y: int
    spiral_bar: str                 # Spiral bar size for spiral columns
    spiral_pitch: float             # Spiral pitch (mm)
    confinement_ratio: float        # Volumetric ratio of confinement steel

@dataclass
class ColumnCapacity:
    """Column capacity results"""
    axial_capacity: float           # Nominal axial capacity Pn (kN)
    moment_capacity_x: float        # Moment capacity about x-axis Mnx (kN⋅m)
    moment_capacity_y: float        # Moment capacity about y-axis Mny (kN⋅m)
    shear_capacity_x: float         # Design shear capacity φVnx (kN)
    shear_capacity_y: float         # Design shear capacity φVny (kN)
    interaction_ratio: float        # P-M interaction ratio
    slenderness_effects: bool       # Whether slenderness effects considered

@dataclass
class ColumnAnalysisResult:
    """Complete column analysis results"""
    capacity: ColumnCapacity
    reinforcement: ColumnReinforcement
    utilization_ratio: float       # Governing (Max) Demand/Capacity ratio
    shear_utilization_x: float     # Shear D/C ratio in X direction
    shear_utilization_y: float     # Shear D/C ratio in Y direction
    stability_index: float         # Stability index for sway analysis
    design_notes: List[str]        # Design notes and warnings

class ACI318M25ColumnDesign:
    """
    ACI 318M-25 Column Design Library
    
    Comprehensive column design according to ACI 318M-25:
    - Axial and combined loading (Chapter 10)
    - Slenderness effects (Chapter 6)
    - Seismic provisions (Chapter 18)
    - Confinement design
    - P-M interaction analysis
    """
    
    def __init__(self):
        """Initialize column design calculator"""
        self.aci = ACI318M25()
        
        # Strength reduction factors φ - ACI 318M-25 Section 21.2
        self.phi_factors = {
            'compression_tied': 0.65,
            'compression_spiral': 0.75,
            'flexure': 0.90,
            'shear': 0.75
        }
        
        # Minimum and maximum reinforcement ratios - ACI 318M-25 Section 10.6
        self.reinforcement_limits = {
            'min_ratio': 0.01,      # Minimum ρg = 0.01
            'max_ratio': 0.08,      # Maximum ρg = 0.08 (0.06 for lap splices)
            'min_bars': 4,          # Minimum number of longitudinal bars
            'min_bar_size': 'D16'   # Minimum bar size
        }
        
        # Tie and spiral requirements
        self.confinement_requirements = {
            'min_tie_size': 'D10',
            'max_tie_spacing_factor': 16,  # 16 times longitudinal bar diameter
            'min_spiral_ratio': 0.45,      # Minimum spiral reinforcement ratio factor
            'spiral_clear_spacing': 25     # Minimum clear spacing between spiral turns (mm)
        }

    def generate_bar_layout(self, geometry: ColumnGeometry, 
                            longitudinal_bars: List[str], 
                            assumed_tie: str = 'D10') -> List[Tuple[float, float, float]]:
        """
        Generates precise (x, y) coordinates and areas for each longitudinal bar.
        Returns a list of tuples: [(x, y, area), ...] relative to the geometric center.
        """
        if not longitudinal_bars:
            return []
            
        N = len(longitudinal_bars)
        db = self.aci.get_bar_diameter(longitudinal_bars[0])
        area = self.aci.get_bar_area(longitudinal_bars[0])
        dt = self.aci.get_bar_diameter(assumed_tie)
        c = geometry.cover
        
        layout = []
        
        if geometry.shape == ColumnShape.CIRCULAR:
            # Radius to the center of the longitudinal bars
            Rc = geometry.width / 2.0 - c - dt - db / 2.0
            for i in range(N):
                theta = i * (2 * math.pi / N)
                x = Rc * math.cos(theta)
                y = Rc * math.sin(theta)
                layout.append((x, y, area))
                
        elif geometry.shape == ColumnShape.RECTANGULAR:
            # Core boundaries for bar centers
            x_max = geometry.width / 2.0 - c - dt - db / 2.0
            y_max = geometry.depth / 2.0 - c - dt - db / 2.0
            
            # 1. Place 4 bars in the corners
            layout.extend([
                (x_max, y_max, area), (-x_max, y_max, area),
                (-x_max, -y_max, area), (x_max, -y_max, area)
            ])
            
            # 2. Distribute remaining bars (N - 4) proportionally to the faces
            if N > 4:
                rem = N - 4
                ratio = geometry.width / (geometry.width + geometry.depth)
                # Ensure even numbers to maintain symmetry across axes
                nx_inter = 2 * int(round(rem * ratio / 2.0)) 
                ny_inter = rem - nx_inter
                
                nx_face = nx_inter // 2  # Bars per top/bottom face
                ny_face = ny_inter // 2  # Bars per left/right face
                
                # Top/Bottom faces
                if nx_face > 0:
                    spacing_x = (2 * x_max) / (nx_face + 1)
                    for i in range(1, nx_face + 1):
                        x = x_max - i * spacing_x
                        layout.append((x, y_max, area))
                        layout.append((x, -y_max, area))
                        
                # Left/Right faces
                if ny_face > 0:
                    spacing_y = (2 * y_max) / (ny_face + 1)
                    for i in range(1, ny_face + 1):
                        y = y_max - i * spacing_y
                        layout.append((x_max, y, area))
                        layout.append((-x_max, y, area))
                
        return layout

    def check_seismic_geometric_limits(self, geometry: ColumnGeometry) -> List[str]:
        """
        Check dimensional limits for Special Moment Frame (SMF) columns
        ACI 318M-25 Section 18.7.2.1
        """
        warnings = []
        
        # These limits only apply to Special Moment Frames
        if geometry.frame_system == FrameSystem.SPECIAL:
            min_dim = min(geometry.width, geometry.depth)
            max_dim = max(geometry.width, geometry.depth)
            
            # 1. Shortest cross-sectional dimension >= 300 mm
            if min_dim < 300.0:
                warnings.append(
                    f"SMF Violation: Minimum column dimension ({min_dim:.0f} mm) must be >= 300 mm."
                )
                
            # 2. Ratio of shortest to perpendicular dimension >= 0.4
            if max_dim > 0:
                aspect_ratio = min_dim / max_dim
                if aspect_ratio < 0.4:
                    warnings.append(
                        f"SMF Violation: Cross-sectional aspect ratio ({aspect_ratio:.2f}) must be >= 0.4."
                    )
                    
        return warnings
    
    def calculate_probable_moment_capacity(self, geometry: ColumnGeometry,
                                           material_props: MaterialProperties,
                                           bar_layout: List[Tuple[float, float, float]],
                                           axial_load: float) -> float:
        """
        Estimate probable flexural strength (Mpr) for SMF capacity design using 3D Strain-Compatibility.
        ACI 318M-25 Section 18.7.6
        Uses steel stress of 1.25fy and strength reduction factor phi = 1.0.
        """
        fc_prime = material_props.fc_prime
        fy_pr = 1.25 * material_props.fy  # Probable yield strength
        Es = 200000.0
        ecu = 0.003
        
        P_target = abs(axial_load)
        
        if geometry.shape == ColumnShape.RECTANGULAR:
            hx, hy = geometry.depth, geometry.width
            h = max(hx, hy)
            b = min(hx, hy)
            is_x = (hx >= hy)
        else:
            h = b = geometry.width
            is_x = True

        if fc_prime <= 28:
            beta1 = 0.85
        elif fc_prime <= 55:
            beta1 = 0.85 - 0.05 * (fc_prime - 28) / 7.0
        else:
            beta1 = 0.65

        steel_area = sum(a for _, _, a in bar_layout)
        Ag = geometry.width * geometry.depth if geometry.shape == ColumnShape.RECTANGULAR else math.pi * (geometry.width/2)**2
        Po = 0.85 * fc_prime * (Ag - steel_area) + fy_pr * steel_area
        Pn_max = Po / 1000.0

        if P_target > Pn_max:
            return 0.001

        curve_Pn = []
        curve_Mn = []
        is_circular = geometry.shape == ColumnShape.CIRCULAR
        c_values = [h * x for x in [10.0, 5.0, 2.0, 1.5, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.01]]
        
        for c in c_values:
            Pn = 0.0
            Mn = 0.0
            
            a = min(beta1 * c, h)
            if a > 0:
                if not is_circular:
                    Cc = (0.85 * fc_prime * a * b) / 1000.0
                    y_c = h / 2.0 - a / 2.0
                else:
                    theta = 2 * math.acos(max(-1.0, min(1.0, 1.0 - 2 * a / h)))
                    area_c = (h / 2.0)**2 / 2.0 * (theta - math.sin(theta))
                    Cc = (0.85 * fc_prime * area_c) / 1000.0
                    y_c = (2 * (h / 2.0) * math.sin(theta/2)**3) / (3 * (theta - math.sin(theta))) if theta > 0 else 0
                Pn += Cc
                Mn += Cc * (y_c / 1000.0)

            for x_bar, y_bar, a_bar in bar_layout:
                d_i = h / 2.0 - y_bar if is_x else h / 2.0 - x_bar
                strain = ecu * (c - d_i) / c
                stress = max(-fy_pr, min(fy_pr, strain * Es))
                
                if d_i < a:
                    stress -= 0.85 * fc_prime
                    
                Fs = a_bar * stress
                Pn += Fs / 1000.0
                Mn += (Fs / 1000.0) * (h / 2.0 - d_i) / 1000.0

            curve_Pn.append(Pn)
            curve_Mn.append(Mn)

        for i in range(len(curve_Pn) - 1):
            p1, p2 = curve_Pn[i], curve_Pn[i+1]
            m1, m2 = curve_Mn[i], curve_Mn[i+1]
            if min(p1, p2) <= P_target <= max(p1, p2):
                if p1 == p2: return max(m1, m2)
                return m1 + (m2 - m1) * (P_target - p1) / (p2 - p1)
                
        return 0.001


    def calculate_nominal_moment_capacity(self, geometry: ColumnGeometry,
                                          material_props: MaterialProperties,
                                          bar_layout: List[Tuple[float, float, float]],
                                          axial_load: float) -> float:
        """
        Estimate nominal flexural strength (Mnc) for Strong-Column/Weak-Beam check using 3D Strain-Compatibility.
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        Es = 200000.0
        ecu = 0.003
        
        P_target = abs(axial_load)
        
        if geometry.shape == ColumnShape.RECTANGULAR:
            hx, hy = geometry.depth, geometry.width
            h = max(hx, hy)
            b = min(hx, hy)
            is_x = (hx >= hy)
        else:
            h = b = geometry.width
            is_x = True

        if fc_prime <= 28:
            beta1 = 0.85
        elif fc_prime <= 55:
            beta1 = 0.85 - 0.05 * (fc_prime - 28) / 7.0
        else:
            beta1 = 0.65

        steel_area = sum(a for _, _, a in bar_layout)
        Ag = geometry.width * geometry.depth if geometry.shape == ColumnShape.RECTANGULAR else math.pi * (geometry.width/2)**2
        Po = 0.85 * fc_prime * (Ag - steel_area) + fy * steel_area
        Pn_max = Po / 1000.0

        if P_target > Pn_max:
            return 0.001

        curve_Pn = []
        curve_Mn = []
        is_circular = geometry.shape == ColumnShape.CIRCULAR
        c_values = [h * x for x in [10.0, 5.0, 2.0, 1.5, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.01]]
        
        for c in c_values:
            Pn = 0.0
            Mn = 0.0
            
            a = min(beta1 * c, h)
            if a > 0:
                if not is_circular:
                    Cc = (0.85 * fc_prime * a * b) / 1000.0
                    y_c = h / 2.0 - a / 2.0
                else:
                    theta = 2 * math.acos(max(-1.0, min(1.0, 1.0 - 2 * a / h)))
                    area_c = (h / 2.0)**2 / 2.0 * (theta - math.sin(theta))
                    Cc = (0.85 * fc_prime * area_c) / 1000.0
                    y_c = (2 * (h / 2.0) * math.sin(theta/2)**3) / (3 * (theta - math.sin(theta))) if theta > 0 else 0
                Pn += Cc
                Mn += Cc * (y_c / 1000.0)

            for x_bar, y_bar, a_bar in bar_layout:
                d_i = h / 2.0 - y_bar if is_x else h / 2.0 - x_bar
                strain = ecu * (c - d_i) / c
                stress = max(-fy, min(fy, strain * Es))
                
                if d_i < a:
                    stress -= 0.85 * fc_prime
                    
                Fs = a_bar * stress
                Pn += Fs / 1000.0
                Mn += (Fs / 1000.0) * (h / 2.0 - d_i) / 1000.0

            curve_Pn.append(Pn)
            curve_Mn.append(Mn)

        for i in range(len(curve_Pn) - 1):
            p1, p2 = curve_Pn[i], curve_Pn[i+1]
            m1, m2 = curve_Mn[i], curve_Mn[i+1]
            if min(p1, p2) <= P_target <= max(p1, p2):
                if p1 == p2: return max(m1, m2)
                return m1 + (m2 - m1) * (P_target - p1) / (p2 - p1)
                
        return 0.001
    
    def calculate_required_longitudinal_steel(self, loads: ColumnLoads, 
                                            geometry: ColumnGeometry,
                                            material_props: MaterialProperties) -> float:
        """
        Calculate an initial baseline guess for required longitudinal steel area
        """
        if geometry.shape == ColumnShape.RECTANGULAR:
            Ag = geometry.width * geometry.depth
        else:
            Ag = math.pi * (geometry.width / 2) ** 2
        
        As_min = self.reinforcement_limits['min_ratio'] * Ag
        As_required = As_min
        
        if loads.load_condition != LoadCondition.AXIAL_ONLY:
            # FIX: Unit mismatch (Moment in kN-m, axial in kN, width in mm)
            # Converted moment to kN-mm for proper ratio comparison
            moment_ratio = abs(loads.moment_x * 1000) / (loads.axial_force * geometry.width / 6) if loads.axial_force > 0 else 2.0
            if moment_ratio > 1.0:
                As_additional = self._calculate_additional_steel_for_moment(
                    loads, geometry, material_props
                )
                As_required = max(As_required, As_additional)
        
        if geometry.frame_system == FrameSystem.SPECIAL:
            max_ratio = 0.06
        else:
            max_ratio = self.reinforcement_limits['max_ratio']
            
        As_max = max_ratio * Ag
        As_required = min(As_required, As_max)
        
        return As_required
    
    def design_tie_reinforcement(self, geometry: ColumnGeometry, 
                               longitudinal_bars: List[str],
                               loads: ColumnLoads,
                               material_props: MaterialProperties) -> Tuple[str, float, int, int]:
        """
        Design tie reinforcement for tied columns checking confinement, seismic rules, and shear
        """
        if longitudinal_bars:
            long_bar_size = longitudinal_bars[0]
            long_bar_diameter = self.aci.get_bar_diameter(long_bar_size)
        else:
            long_bar_diameter = 20.0
            
        tie_size = 'D10' if long_bar_diameter <= 32.0 else 'D12'
        tie_diameter = self.aci.get_bar_diameter(tie_size)
        
        tie_legs_x = 2
        tie_legs_y = 2
        
        if geometry.shape == ColumnShape.RECTANGULAR and len(longitudinal_bars) >= 4:
            num_bars = len(longitudinal_bars)
            nx = max(2, int(round((geometry.width / (geometry.width + geometry.depth)) * (num_bars / 2.0))) + 1)
            ny = max(2, int((num_bars + 4 - 2 * nx) / 2))
            
            if nx > 1:
                clear_x = (geometry.width - 2 * geometry.cover - 2 * tie_diameter - long_bar_diameter) / (nx - 1) - long_bar_diameter
                tie_legs_y = nx if clear_x > 150.0 else math.ceil(nx / 2.0) + (1 if nx % 2 == 0 else 0)
            if ny > 1:
                clear_y = (geometry.depth - 2 * geometry.cover - 2 * tie_diameter - long_bar_diameter) / (ny - 1) - long_bar_diameter
                tie_legs_x = ny if clear_y > 150.0 else math.ceil(ny / 2.0) + (1 if ny % 2 == 0 else 0)

        # SEISMIC CONFINEMENT (SMF)
        if geometry.frame_system == FrameSystem.SPECIAL:
            min_col_dim = min(geometry.width, geometry.depth)
            
            hx_approx = min_col_dim / min(tie_legs_x, tie_legs_y)
            sx = 100.0 + (350.0 - hx_approx) / 3.0
            sx = max(100.0, min(sx, 150.0))
            
            spacing_confinement = min(
                min_col_dim / 4.0,
                6.0 * long_bar_diameter,
                sx
            )
            
            fc_prime = material_props.fc_prime
            fyt = material_props.fy
            Ag = geometry.width * geometry.depth
            
            bc_x = geometry.depth - 2 * geometry.cover
            bc_y = geometry.width - 2 * geometry.cover
            Ach = bc_x * bc_y
            
            Ash_req_x1 = 0.3 * (spacing_confinement * bc_x * fc_prime / fyt) * (Ag / Ach - 1.0)
            Ash_req_x2 = 0.09 * spacing_confinement * bc_x * fc_prime / fyt
            Ash_req_x = max(Ash_req_x1, Ash_req_x2)
            
            Ash_req_y1 = 0.3 * (spacing_confinement * bc_y * fc_prime / fyt) * (Ag / Ach - 1.0)
            Ash_req_y2 = 0.09 * spacing_confinement * bc_y * fc_prime / fyt
            Ash_req_y = max(Ash_req_y1, Ash_req_y2)
            
            A_tie = self.aci.get_bar_area(tie_size)
            while (tie_legs_x * A_tie < Ash_req_x) or (tie_legs_y * A_tie < Ash_req_y):
                if tie_size == 'D10':
                    tie_size = 'D12'
                elif tie_size == 'D12':
                    tie_size = 'D16'
                else:
                    tie_legs_x += 1
                    tie_legs_y += 1
                A_tie = self.aci.get_bar_area(tie_size)

        else:
            spacing_confinement = min(
                16 * long_bar_diameter,
                48 * tie_diameter,
                min(geometry.width, geometry.depth)
            )

        # SHEAR REQUIREMENTS
        fc_prime = material_props.fc_prime
        fy_tie = material_props.fy
        phi_v = self.phi_factors['shear']
        A_tie_leg = self.aci.get_bar_area(tie_size)
        
        dx = geometry.width - geometry.cover - tie_diameter - (long_bar_diameter / 2)
        dy = geometry.depth - geometry.cover - tie_diameter - (long_bar_diameter / 2)
        
        # Shear in X direction
        Vu_x = abs(loads.shear_x) * 1000
        Av_x = tie_legs_x * A_tie_leg
        
        Vc_x = 0.17 * math.sqrt(fc_prime) * geometry.depth * dx
        Vs_req_x = max(0.0, (Vu_x / phi_v) - Vc_x)
        
        s_shear_x = float('inf')
        if Vs_req_x > 0:
            s_shear_x = (Av_x * fy_tie * dx) / Vs_req_x
            
        Vs_max_x = 0.33 * math.sqrt(fc_prime) * geometry.depth * dx
        max_s_shear_x = dx / 4.0 if Vs_req_x > Vs_max_x else dx / 2.0

        # Shear in Y direction
        Vu_y = abs(loads.shear_y) * 1000
        Av_y = tie_legs_y * A_tie_leg
        
        Vc_y = 0.17 * math.sqrt(fc_prime) * geometry.width * dy
        Vs_req_y = max(0.0, (Vu_y / phi_v) - Vc_y)
        
        s_shear_y = float('inf')
        if Vs_req_y > 0:
            s_shear_y = (Av_y * fy_tie * dy) / Vs_req_y
            
        Vs_max_y = 0.33 * math.sqrt(fc_prime) * geometry.width * dy
        max_s_shear_y = dy / 4.0 if Vs_req_y > Vs_max_y else dy / 2.0

        # GOVERNING SPACING
        s_final = min(spacing_confinement, s_shear_x, s_shear_y, max_s_shear_x, max_s_shear_y)
        s_final = math.floor(s_final / 10.0) * 10.0
        s_final = max(s_final, 50.0)
        
        return tie_size, s_final, tie_legs_x, tie_legs_y
    
    def design_spiral_reinforcement(self, geometry: ColumnGeometry,
                                  material_props: MaterialProperties) -> Tuple[str, float, float]:
        """
        Design spiral reinforcement for spiral columns
        ACI 318M-25 Section 25.7.3
        """
        if geometry.shape != ColumnShape.CIRCULAR:
            raise ValueError("Spiral reinforcement only applicable to circular columns")
        
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        
        dc = geometry.width - 2 * geometry.cover
        Ac = math.pi * (dc / 2) ** 2 
        Ag = math.pi * (geometry.width / 2) ** 2
        
        rho_s = 0.45 * (Ag / Ac - 1.0) * (fc_prime / fy)
        
        rho_s_min = self.confinement_requirements['min_spiral_ratio'] * (fc_prime / fy)
        rho_s = max(rho_s, rho_s_min)
        
        spiral_bar = 'D10'
        As_spiral = self.aci.get_bar_area(spiral_bar)
        
        s_required = 4 * As_spiral / (dc * rho_s)
        
        min_clear_spacing = self.confinement_requirements['spiral_clear_spacing']
        spiral_diameter = self.aci.get_bar_diameter(spiral_bar)
        s_min = min_clear_spacing + spiral_diameter
        
        if s_required < s_min:
            spiral_bar = 'D12'
            As_spiral = self.aci.get_bar_area(spiral_bar)
            s_required = 4 * As_spiral / (dc * rho_s)
            spiral_diameter = self.aci.get_bar_diameter(spiral_bar)
            s_min = min_clear_spacing + spiral_diameter
        
        spiral_pitch = max(s_required, s_min)
        s_max = 75.0 + spiral_diameter
        spiral_pitch = min(spiral_pitch, s_max)
        
        return spiral_bar, spiral_pitch, rho_s
    
    def calculate_axial_capacity(self, geometry: ColumnGeometry,
                               material_props: MaterialProperties,
                               steel_area: float) -> float:
        """
        Calculate maximum allowable nominal axial capacity (Pn,max)
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        
        if geometry.shape == ColumnShape.RECTANGULAR:
            Ag = geometry.width * geometry.depth
        elif geometry.shape == ColumnShape.CIRCULAR:
            Ag = math.pi * (geometry.width / 2) ** 2
        else:
            Ag = geometry.width * geometry.depth
        
        Po = 0.85 * fc_prime * (Ag - steel_area) + fy * steel_area
        
        if geometry.column_type == ColumnType.TIED:
            Pn_max = 0.80 * Po
        else:
            Pn_max = 0.85 * Po
        
        return Pn_max / 1000
    
    def check_slenderness_effects(self, geometry: ColumnGeometry,
                                loads: ColumnLoads) -> Tuple[bool, float]:
        """
        Check if slenderness effects need to be considered
        """
        k = 1.0 
        
        if geometry.shape == ColumnShape.RECTANGULAR:
            r = geometry.depth / (2 * math.sqrt(3))
        elif geometry.shape == ColumnShape.CIRCULAR:
            r = geometry.width / 4 
        else:
            r = min(geometry.width, geometry.depth) / (2 * math.sqrt(3))
        
        kl_r = k * geometry.effective_length / r
        
        if loads.load_condition == LoadCondition.AXIAL_ONLY:
            limit = 22.0
        else:
            M1 = min(abs(loads.moment_x), abs(loads.moment_y))
            M2 = max(abs(loads.moment_x), abs(loads.moment_y))
            M1_M2 = M1 / M2 if M2 > 0 else 0.0
            
            limit_calc = 34.0 - 12.0 * M1_M2
            limit = max(22.0, min(limit_calc, 40.0))
        
        slenderness_required = kl_r > limit
        
        if slenderness_required:
            magnification_factor = 1.0 + 0.1 * (kl_r - limit) / limit
        else:
            magnification_factor = 1.0
        
        return slenderness_required, magnification_factor
    
    def calculate_pm_interaction(self, geometry: ColumnGeometry,
                               material_props: MaterialProperties,
                               bar_layout: List[Tuple[float, float, float]],
                               loads: ColumnLoads) -> float:
        """
        Calculate P-M interaction ratio using rigorous 3D Bar-by-Bar Strain-Compatibility.
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        Es = 200000.0  
        ecu = 0.003   
        
        Pu = abs(loads.axial_force)
        Mux = abs(loads.moment_x)
        Muy = abs(loads.moment_y)
        
        if geometry.shape == ColumnShape.RECTANGULAR:
            Ag = geometry.width * geometry.depth
            hx, hy = geometry.depth, geometry.width
        else:
            Ag = math.pi * (geometry.width / 2) ** 2
            hx = hy = geometry.width

        if fc_prime <= 28:
            beta1 = 0.85
        elif fc_prime <= 55:
            beta1 = 0.85 - 0.05 * (fc_prime - 28) / 7.0
        else:
            beta1 = 0.65
            
        phi_c = self.phi_factors['compression_tied'] if geometry.column_type == ColumnType.TIED else self.phi_factors['compression_spiral']
        phi_f = self.phi_factors['flexure']
        
        steel_area = sum(area for _, _, area in bar_layout)
        Pn_max = self.calculate_axial_capacity(geometry, material_props, steel_area)
        
        axial_ratio = Pu / (phi_c * Pn_max) if Pn_max > 0 else float('inf')
        if axial_ratio >= 1.0 or (Mux < 0.01 and Muy < 0.01):
            return axial_ratio

        def compute_capacity_at_axis(h, b, is_circular, is_x_axis):
            curve_Pn = []
            curve_phi_Mn = []
            
            c_values = [h * x for x in [10.0, 5.0, 2.0, 1.5, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.01]]
            
            for c in c_values:
                Pn = 0.0
                Mn = 0.0
                
                a = min(beta1 * c, h)
                if a > 0:
                    if not is_circular:
                        Cc = (0.85 * fc_prime * a * b) / 1000.0  
                        y_c = h / 2.0 - a / 2.0
                    else:
                        theta = 2 * math.acos(max(-1.0, min(1.0, 1.0 - 2 * a / h)))
                        area_c = (h / 2.0)**2 / 2.0 * (theta - math.sin(theta))
                        Cc = (0.85 * fc_prime * area_c) / 1000.0  
                        y_c = (2 * (h / 2.0) * math.sin(theta/2)**3) / (3 * (theta - math.sin(theta))) if theta > 0 else 0
                    
                    Pn += Cc
                    Mn += Cc * (y_c / 1000.0) 

                extreme_tension_strain = 0.0
                max_di = 0.0
                
                for x_bar, y_bar, a_bar in bar_layout:
                    if is_x_axis:
                        d_i = h / 2.0 - y_bar  
                    else:
                        d_i = h / 2.0 - x_bar 
                        
                    strain = ecu * (c - d_i) / c
                    stress = max(-fy, min(fy, strain * Es))
                    
                    if d_i < a:
                        stress -= 0.85 * fc_prime
                        
                    Fs = a_bar * stress
                    Pn += Fs / 1000.0 
                    Mn += (Fs / 1000.0) * (h / 2.0 - d_i) / 1000.0 
                    
                    if d_i > max_di:
                        max_di = d_i
                        extreme_tension_strain = strain

                et = abs(extreme_tension_strain)
                ey = fy / Es
                if et <= ey:
                    phi = phi_c
                elif et >= 0.005:
                    phi = phi_f
                else:
                    phi = phi_c + (phi_f - phi_c) * (et - ey) / (0.005 - ey)

                Pn = min(Pn, Pn_max)
                curve_Pn.append(Pn * phi)
                curve_phi_Mn.append(Mn * phi)
                
            return curve_Pn, curve_phi_Mn

        is_circ = geometry.shape == ColumnShape.CIRCULAR
        Pn_curve_x, phi_Mnx_curve = compute_capacity_at_axis(hx, hy, is_circ, is_x_axis=True)
        Pn_curve_y, phi_Mny_curve = compute_capacity_at_axis(hy, hx, is_circ, is_x_axis=False)

        def get_moment_at_Pu(P_target, P_curve, M_curve):
            for i in range(len(P_curve) - 1):
                p1, p2 = P_curve[i], P_curve[i+1]
                m1, m2 = M_curve[i], M_curve[i+1]
                if min(p1, p2) <= P_target <= max(p1, p2):
                    if p1 == p2:
                        return max(m1, m2)
                    return m1 + (m2 - m1) * (P_target - p1) / (p2 - p1)
            return 0.001

        phi_Mnx = get_moment_at_Pu(Pu, Pn_curve_x, phi_Mnx_curve)
        phi_Mny = get_moment_at_Pu(Pu, Pn_curve_y, phi_Mny_curve)
        
        alpha = 1.15 if geometry.shape == ColumnShape.RECTANGULAR else 1.5
        ratio_x = (Mux / phi_Mnx) if phi_Mnx > 0 else 0
        ratio_y = (Muy / phi_Mny) if phi_Mny > 0 else 0
        
        interaction_ratio = (ratio_x**alpha + ratio_y**alpha)**(1.0/alpha)
        
        return max(interaction_ratio, axial_ratio)
    
    def _calculate_additional_steel_for_moment(self, loads: ColumnLoads,
                                             geometry: ColumnGeometry,
                                             material_props: MaterialProperties) -> float:
        """Calculate additional steel needed for moment resistance"""
        fy = material_props.fy
        
        if geometry.shape == ColumnShape.RECTANGULAR:
            lever_arm = 0.8 * geometry.depth
            As_moment = abs(loads.moment_x) * 1e6 / (fy * lever_arm)
        else:
            lever_arm = 0.6 * geometry.width
            As_moment = max(abs(loads.moment_x), abs(loads.moment_y)) * 1e6 / (fy * lever_arm)
        
        return As_moment
    
    def select_longitudinal_reinforcement(self, As_required: float, geometry: ColumnGeometry, 
                                          aggregate_size: float = 25.0, assumed_tie: str = 'D10') -> List[str]:
        """
        Select longitudinal reinforcement bars ensuring ACI 318M-25 spacing limits.
        """
        bar_data = [
            ('D16', 201.06), ('D20', 314.16), ('D25', 490.87), 
            ('D28', 615.75), ('D32', 804.25), ('D36', 1017.88),
            ('D40', 1256.64), ('D50', 1963.50)
        ]
        
        min_bars = 4 if geometry.shape == ColumnShape.RECTANGULAR else 6
        
        d_tie = self.aci.get_bar_diameter(assumed_tie)
        cover = geometry.cover
        
        selected_bars = []
        
        for bar_size, area in bar_data:
            num_bars = max(min_bars, math.ceil(As_required / area))
            
            if geometry.shape == ColumnShape.RECTANGULAR and num_bars % 2 != 0:
                num_bars += 1
                
            db = self.aci.get_bar_diameter(bar_size)
            
            min_clear_spacing = max(40.0, 1.5 * db, (4.0/3.0) * aggregate_size)
            
            if geometry.shape == ColumnShape.CIRCULAR:
                d_core = geometry.width - 2 * cover - 2 * d_tie - db
                perimeter = math.pi * d_core
            else:
                w_core = geometry.width - 2 * cover - 2 * d_tie - db
                d_core = geometry.depth - 2 * cover - 2 * d_tie - db
                perimeter = 2 * (w_core + d_core)
            
            avg_clear_spacing = (perimeter - (num_bars * db)) / num_bars
            
            if avg_clear_spacing >= min_clear_spacing:
                selected_bars = [bar_size] * num_bars
                break
        
        if not selected_bars:
            largest_bar, largest_area = bar_data[-1]
            num_bars = max(min_bars, math.ceil(As_required / largest_area))
            if geometry.shape == ColumnShape.RECTANGULAR and num_bars % 2 != 0:
                num_bars += 1
            selected_bars = [largest_bar] * num_bars
            
        return selected_bars
    
    def calculate_shear_capacity(self, geometry: ColumnGeometry, 
                                 material_props: MaterialProperties,
                                 transverse_bar: str, spacing: float,
                                 legs_x: int, legs_y: int,
                                 longitudinal_bars: List[str]) -> Tuple[float, float]:
        """
        Calculate design shear capacities (φVnx, φVny)
        """
        if not transverse_bar or spacing <= 0:
            return 0.0, 0.0
            
        fc_prime = material_props.fc_prime
        fy_tie = material_props.fy
        phi_v = self.phi_factors['shear']
        
        transverse_area = self.aci.get_bar_area(transverse_bar)
        tie_diameter = self.aci.get_bar_diameter(transverse_bar)
        
        if longitudinal_bars:
            long_bar_diameter = self.aci.get_bar_diameter(longitudinal_bars[0])
        else:
            long_bar_diameter = 20.0 
            
        dx = geometry.width - geometry.cover - tie_diameter - (long_bar_diameter / 2)
        dy = geometry.depth - geometry.cover - tie_diameter - (long_bar_diameter / 2)
        
        Vc_x = 0.17 * math.sqrt(fc_prime) * geometry.depth * dx
        Vc_y = 0.17 * math.sqrt(fc_prime) * geometry.width * dy
        
        Vs_x = (legs_x * transverse_area * fy_tie * dx) / spacing
        Vs_y = (legs_y * transverse_area * fy_tie * dy) / spacing
        
        Vs_max_x = 0.66 * math.sqrt(fc_prime) * geometry.depth * dx
        Vs_max_y = 0.66 * math.sqrt(fc_prime) * geometry.width * dy
        
        Vs_x = min(Vs_x, Vs_max_x)
        Vs_y = min(Vs_y, Vs_max_y)
        
        phi_Vnx = phi_v * (Vc_x + Vs_x) / 1000.0
        phi_Vny = phi_v * (Vc_y + Vs_y) / 1000.0
        
        return phi_Vnx, phi_Vny
    
    def perform_complete_column_design(self, loads: ColumnLoads,
                                     geometry: ColumnGeometry,
                                     material_props: MaterialProperties) -> ColumnAnalysisResult:
        """
        Perform complete iterative column design analysis
        Auto-increments longitudinal steel area until utilization <= 1.0
        """
        base_design_notes = []
        
        # --- Check Seismic Geometric Limits ---
        seismic_warnings = self.check_seismic_geometric_limits(geometry)
        if seismic_warnings:
            base_design_notes.extend(seismic_warnings)
        
        # --- Determine Area and Limits ---
        if geometry.shape == ColumnShape.RECTANGULAR:
            Ag = geometry.width * geometry.depth
        else:
            Ag = math.pi * (geometry.width / 2) ** 2
            
        min_rho = self.reinforcement_limits['min_ratio']
        max_rho = 0.06 if geometry.frame_system == FrameSystem.SPECIAL else self.reinforcement_limits['max_ratio']
        
        # Base initial guess on simplified static checks to save iteration time
        As_guess = self.calculate_required_longitudinal_steel(loads, geometry, material_props)
        start_rho = max(min_rho, min(As_guess / Ag, max_rho))
        
        # Round down to nearest 0.5% (e.g. 0.010, 0.015, 0.020)
        start_rho = math.floor(start_rho * 200) / 200.0
        start_rho = max(min_rho, start_rho)
        
        current_rho = start_rho
        best_result = None
        last_result = None
        
        # Iteration Loop: Step up rho by 0.5% each time if it fails
        while current_rho <= max_rho + 1e-5:
            As_target = current_rho * Ag
            current_notes = list(base_design_notes)
            
            # 1. Select Bars based on current target area
            longitudinal_bars = self.select_longitudinal_reinforcement(As_target, geometry)
            As_provided = sum(self.aci.get_bar_area(bar) for bar in longitudinal_bars)
            bar_layout = self.generate_bar_layout(geometry, longitudinal_bars, assumed_tie='D10')
            
            # 2. Design confinement and shear reinforcement
            if geometry.column_type == ColumnType.TIED:
                tie_size, tie_spacing, tie_legs_x, tie_legs_y = self.design_tie_reinforcement(
                    geometry, longitudinal_bars, loads, material_props
                )
                spiral_bar, spiral_pitch, volumetric_ratio = "", 0.0, 0.0
                
                transverse_bar = tie_size
                trans_spacing = tie_spacing
                legs_x, legs_y = tie_legs_x, tie_legs_y

                if geometry.frame_system == FrameSystem.SPECIAL:
                    max_col_dim = max(geometry.width, geometry.depth)
                    lu = getattr(geometry, 'clear_height', geometry.height - 600) 
                    lo = max(max_col_dim, lu / 6.0, 450.0)
                    s_outside = min(6.0 * self.aci.get_bar_diameter(longitudinal_bars[0]), 150.0)
                    
                    current_notes.append(f"SMF Detailing: Plastic hinge length (lo) is {lo:.0f} mm from each joint face.")
                    current_notes.append(f"SMF Detailing: Use {tie_size} hoops @ {tie_spacing:.0f} mm within lo, and @ {s_outside:.0f} mm elsewhere.")
                else:
                    current_notes.append(f"Ties detailed with {tie_legs_x} legs parallel to X-axis and {tie_legs_y} legs parallel to Y-axis.")
            else:
                spiral_bar, spiral_pitch, volumetric_ratio = self.design_spiral_reinforcement(
                    geometry, material_props
                )
                tie_size, tie_spacing = "", 0.0
                tie_legs_x, tie_legs_y = 0, 0
                
                transverse_bar = spiral_bar
                trans_spacing = spiral_pitch
                legs_x, legs_y = 2, 2 
            
            # 3. Calculate Shear Capacities
            phi_Vnx, phi_Vny = self.calculate_shear_capacity(
                geometry, material_props, transverse_bar, trans_spacing, legs_x, legs_y, longitudinal_bars
            )
            
            # 4. CAPACITY DESIGN FOR SHEAR (Ve)
            Ve_x = abs(loads.shear_x)
            Ve_y = abs(loads.shear_y)

            if geometry.frame_system == FrameSystem.SPECIAL:
                lu_m = getattr(geometry, 'clear_height', geometry.height - 600) / 1000.0
                Mpr_c = self.calculate_probable_moment_capacity(geometry, material_props, bar_layout, loads.axial_force)
                Ve_col = (2.0 * Mpr_c) / lu_m if lu_m > 0 else Ve_x
                
                if loads.sum_beam_mpr_top is not None and loads.sum_beam_mpr_bot is not None:
                    Ve_beam = (loads.sum_beam_mpr_top + loads.sum_beam_mpr_bot) / lu_m if lu_m > 0 else Ve_col
                    Ve_req = min(Ve_col, Ve_beam)
                    current_notes.append(f"SMF Capacity Design: Ve = {Ve_req:.1f} kN (Governed by beam yielding).")
                else:
                    Ve_req = Ve_col
                    current_notes.append(f"SMF Capacity Design: Ve = {Ve_req:.1f} kN (Governed by column Mpr = {Mpr_c:.1f} kN-m).")

                Ve_x = max(Ve_x, Ve_req)
                Ve_y = max(Ve_y, Ve_req)
                
                if (Ve_req > 0.5 * max(phi_Vnx, phi_Vny)) and (loads.axial_force * 1000 < (Ag * material_props.fc_prime / 20)):
                    current_notes.append("SMF Detailing: Vc taken as 0 per ACI 18.7.6.2.1 (Low axial load + high seismic shear).")

            shear_util_x = Ve_x / phi_Vnx if phi_Vnx > 0 else 0.0
            shear_util_y = Ve_y / phi_Vny if phi_Vny > 0 else 0.0
            
            # 5. Check slenderness effects
            slenderness_required, magnification_factor = self.check_slenderness_effects(geometry, loads)
            
            axial_capacity = self.calculate_axial_capacity(geometry, material_props, As_provided)
            
            # 6. P-M interaction analysis
            interaction_ratio = self.calculate_pm_interaction(
                geometry, material_props, bar_layout, loads
            )
            
            if slenderness_required:
                adjusted_loads = ColumnLoads(
                    axial_force=loads.axial_force,
                    moment_x=loads.moment_x * magnification_factor,
                    moment_y=loads.moment_y * magnification_factor,
                    shear_x=loads.shear_x,
                    shear_y=loads.shear_y,
                    load_condition=loads.load_condition
                )
                interaction_ratio = self.calculate_pm_interaction(
                    geometry, material_props, bar_layout, adjusted_loads
                )
                
            governing_utilization = max(interaction_ratio, shear_util_x, shear_util_y)
            
            # 7. Add contextual design notes for this specific iteration
            if slenderness_required:
                current_notes.append(f"Slenderness effects considered (λ = {magnification_factor:.2f})")
            
            if As_provided > As_target * 1.5 and current_rho == min_rho:
                current_notes.append("Consider reducing section size (minimum steel controls heavily).")
            
            if interaction_ratio > 1.0:
                current_notes.append("Section inadequate in P-M interaction - increasing steel...")
                
            if shear_util_x > 1.0 or shear_util_y > 1.0:
                current_notes.append("Section inadequate in shear - decreasing tie spacing or increasing size...")

            provided_ratio = As_provided / Ag
            if geometry.frame_system == FrameSystem.SPECIAL:
                if provided_ratio > 0.06:
                    current_notes.append(f"SMF Violation: Provided longitudinal reinforcement ratio ({provided_ratio:.3f}) exceeds the 0.06 maximum limit.")
                current_notes.append("SMF Detailing: Lap splices are only permitted within the center half of the column length (ACI 18.7.4.3).")
                current_notes.append("SMF Detailing: Lap splices must be enclosed within transverse reinforcement (hoops).")

                Mnc_col = self.calculate_nominal_moment_capacity(geometry, material_props, bar_layout, loads.axial_force)
                
                if getattr(loads, 'sum_beam_mnb_top', None) is not None:
                    joint_ratio_top = (2.0 * Mnc_col) / loads.sum_beam_mnb_top if loads.sum_beam_mnb_top > 0 else 9.99
                    if joint_ratio_top < 1.2:
                        current_notes.append(f"SMF Violation (Top Joint): Column/Beam strength ratio is {joint_ratio_top:.2f}. Must be >= 1.2.")
                    else:
                        current_notes.append(f"SMF SC/WB (Top): PASS with ratio {joint_ratio_top:.2f} >= 1.2.")

                if getattr(loads, 'sum_beam_mnb_bot', None) is not None:
                    joint_ratio_bot = (2.0 * Mnc_col) / loads.sum_beam_mnb_bot if loads.sum_beam_mnb_bot > 0 else 9.99
                    if joint_ratio_bot < 1.2:
                        current_notes.append(f"SMF Violation (Bot Joint): Column/Beam strength ratio is {joint_ratio_bot:.2f}. Must be >= 1.2.")
                    else:
                        current_notes.append(f"SMF SC/WB (Bot): PASS with ratio {joint_ratio_bot:.2f} >= 1.2.")
                        
                if getattr(loads, 'sum_beam_mnb_top', None) is None:
                    current_notes.append(f"SMF Note: Column nominal moment Mnc = {Mnc_col:.1f} kN-m. Provide beam Mnb to verify Strong-Column/Weak-Beam.")
            
            # Construct Iteration Result
            reinforcement = ColumnReinforcement(
                longitudinal_bars=longitudinal_bars,
                longitudinal_area=As_provided,
                tie_bars=tie_size,
                tie_legs_x=tie_legs_x,
                tie_legs_y=tie_legs_y,
                tie_spacing=tie_spacing,
                spiral_bar=spiral_bar,
                spiral_pitch=spiral_pitch,
                confinement_ratio=volumetric_ratio
            )
            
            capacity = ColumnCapacity(
                axial_capacity=axial_capacity,
                moment_capacity_x=0.0,
                moment_capacity_y=0.0,
                shear_capacity_x=phi_Vnx,
                shear_capacity_y=phi_Vny,
                interaction_ratio=interaction_ratio,
                slenderness_effects=slenderness_required
            )
            
            last_result = ColumnAnalysisResult(
                capacity=capacity,
                reinforcement=reinforcement,
                utilization_ratio=governing_utilization,
                shear_utilization_x=shear_util_x,
                shear_utilization_y=shear_util_y,
                stability_index=0.0,
                design_notes=current_notes
            )
            
            # --- EVALUATE SUCCESS ---
            if governing_utilization <= 1.0:
                best_result = last_result
                break  # Design passes, exit loop
                
            # Step up reinforcement for next iteration
            current_rho += 0.005
            
        # 8. Return final result
        if best_result is not None:
            return best_result
            
        # If we maxed out the steel and still failed, return the final iteration with a critical warning
        last_result.design_notes.append("CRITICAL: Section inadequate even with maximum reinforcement limit. Increase column dimensions or concrete strength.")
        return last_result