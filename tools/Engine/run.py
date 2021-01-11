# SIMPLIFIED ENGINE MODEL v1
import numpy
from tixi import tixiwrapper

# ----------------------------------------------------------------------------------------------------------------------
# PRE-PROCESSING (INPUTS)

# CPACS
INFILE = './ToolInput/toolInput.xml'

tixi_h = tixiwrapper.Tixi()
tixi_h.open(INFILE)

# Selected Mission Segments
path = '/cpacs/toolspecific/SimplifiedEngineModel/Inputs/SelectedPhases'
Dim_vettore = tixi_h.getVectorSize(path)
Phases = tixi_h.getFloatVector(path, Dim_vettore)

# Subsystems mechanical power off-takes for hydraulics (COMPLETE VECTOR --> EXTRACT NEEDED VALUES)
path = '/cpacs/toolspecific/ASTRID/L1/Global/powerOffTake/maxPower/mechanical_power/mechanical_power_hydr'
Dim_vettore = tixi_h.getVectorSize(path)
Hydraulics_Mechanic_Power_FULL = tixi_h.getFloatVector(path, Dim_vettore)  # [W]
Hydraulics_Mechanic_Power_FULL = numpy.array(Hydraulics_Mechanic_Power_FULL)

# Subsystems mechanical power off-takes for electrics (COMPLETE VECTOR --> EXTRACT NEEDED VALUES)
path = '/cpacs/toolspecific/ASTRID/L1/Global/powerOffTake/maxPower/mechanical_power/mechanical_power_electr'
Dim_vettore = tixi_h.getVectorSize(path)
Electrics_Mechanic_Power_FULL = tixi_h.getFloatVector(path, Dim_vettore)  # [W]
Electrics_Mechanic_Power_FULL = numpy.array(Electrics_Mechanic_Power_FULL)

# Subsystems bleed air off-takes (COMPLETE VECTOR --> EXTRACT NEEDED VALUES)
path = '/cpacs/toolspecific/ASTRID/L1/Global/powerOffTake/maxPower/pneumatic/pneumatic_airflow'
Dim_vettore = tixi_h.getVectorSize(path)
Bleed_Air_FULL = tixi_h.getFloatVector(path, Dim_vettore)  # [kg/s]
Bleed_Air_FULL = numpy.array(Bleed_Air_FULL)

# Number of engines
N_engines = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedEngineModel/Inputs/NumberEngines')

# Clean (i.e. without power off-takes) engine SFC
path = '/cpacs/toolspecific/SimplifiedEngineModel/Inputs/SFCclean'
Dim_vettore = tixi_h.getVectorSize(path)
SFC_clean = tixi_h.getFloatVector(path, Dim_vettore)  # [lb/lbf/h]
SFC_clean = numpy.array(SFC_clean)

# Aircraft Speed
path = '/cpacs/toolspecific/SimplifiedEngineModel/Inputs/AircraftSpeed'
Dim_vettore = tixi_h.getVectorSize(path)
V0 = tixi_h.getFloatVector(path, Dim_vettore)  # [m/s]
V0 = numpy.array(V0)

# Aircraft Altitude
path = '/cpacs/toolspecific/SimplifiedEngineModel/Inputs/AircraftAltitude'
Dim_vettore = tixi_h.getVectorSize(path)
Altitude = tixi_h.getFloatVector(path, Dim_vettore)  # [m]
Altitude = numpy.array(Altitude)

# Single engine net thrust (THIS RESULT SHALL DERIVE FROM THE WORKFLOW)
path = '/cpacs/toolspecific/SimplifiedPerformanceModel/Outputs/SingleEngineNetThrust'
Dim_vettore = tixi_h.getVectorSize(path)
T = tixi_h.getFloatVector(path, Dim_vettore)  # [kN]
T = numpy.array(T)

# Engine By-Pass Ratio
BPR = tixi_h.getDoubleElement('/cpacs/vehicles/engines/engine/analysis/bpr00')

# Fan efficiency multiplied per Low pressure turbine efficiency
n_f_lpt = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedEngineModel/Inputs/n_f_lpt')

# Engine specific thrust
ST = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedEngineModel/Inputs/EngineSpecificThrust')

# Total air enthalpy increase
Delta_h_b = tixi_h.getDoubleElement('/cpacs/toolspecific/SimplifiedEngineModel/Inputs/TotAirEnthalpyIncrease')

print("[INFO]: all inputs have been correctly collected")

# ----------------------------------------------------------------------------------------------------------------------
# PROCESSING
try:
    Hydraulics_Mechanic_Power = numpy.zeros(len(Phases))
    for i in range(len(Phases)):
        Hydraulics_Mechanic_Power[i] = Hydraulics_Mechanic_Power_FULL[int(Phases[i] - 1)]  # [W]
except:
    Hydraulics_Mechanic_Power = 0

try:
    Electrics_Mechanic_Power = numpy.zeros(len(Phases))
    for i in range(len(Phases)):
        Electrics_Mechanic_Power[i] = Electrics_Mechanic_Power_FULL[int(Phases[i] - 1)]  # [W]
except:
    Electrics_Mechanic_Power = 0

Ppo = (Hydraulics_Mechanic_Power + Electrics_Mechanic_Power) / 1000 / N_engines  # [kW]

try:
    m_dot_bleed = numpy.zeros(len(Phases))
    for i in range(len(Phases)):
        m_dot_bleed = Bleed_Air_FULL[int(Phases[i] - 1)] / N_engines  # [kg/s]
except:
    m_dot_bleed = 0

# Giannakakis' methodology

# 1) Evaluation of the transmission efficiency
n_tr = (1 + BPR) / (1 + (BPR / n_f_lpt))
print("n_tr: %f", n_tr)

# 2) Evaluation of the propulsive efficiency
# if Mach is given instead of V
# Mach=[0.25, 0.75, 0.78, 0.6, 0.2]
# Temp=(15+273.15)-(0.0065*Altitude)
# c=numpy.sqrt(1.4*287*Temp)
# V0=Mach*c
n_pr = 1 / (1 + ST / (2 * V0))
print("n_pr: %f", n_pr)

# 3) Evaluation of core efficiency degradation due to power off-takes
BAD_pot = 1 - ((Ppo * (n_tr * n_pr)) / (T * V0))  # Ratio of core efficiency with/out power off-takes
print("BAD_pot: %f", BAD_pot)

# 4) Evaluation of core efficiency degradation due to bleed air off-takes
beta = m_dot_bleed * ST * (BPR + 1) / (T * 1000)  # relative bleed-air flow
BAD_baot = 1 - ((2 * m_dot_bleed * Delta_h_b * (BPR + 1)) / ((1 - beta) * T * ((BPR / n_f_lpt) + 1) * (
            2 * V0 + ST)))  # Ratio of core efficiency with/out bleed-air off-takes
print("BAD_baot: %f", BAD_baot)

# 5) Evaluation of entire engine degradation (unvaried BPR)
BAD_engine = -(V0 / ST) + ((V0 / ST) * numpy.sqrt(1 + (2 * ST / V0) * (BAD_pot * BAD_baot) * (1 + ST / 2. / V0)))
print("BAD_engine: %f", BAD_engine)

# 6) Evaluaiton of corrected SFC
SFCnew = numpy.real(numpy.abs(SFC_clean / BAD_engine))
print("SFCnew: %f", SFCnew)

# VARIATION OF SFC DUE TO BPR - VALID ONLY FOR E-190 CLASS AIRCRAFT
SFCnew = SFCnew * (1 - 0.0935 * (BPR / 12 - 1))
print("SFCnewBPR: %f", SFCnew)

# ESTIMATION OF ENGINE MASS AND DIMENSIONS BASED ON BPR
if tixi_h.checkElement('/cpacs/toolspecific/HybridTool/Outputs/ICEpower') == 1:
    P_engine = tixi_h.getDoubleElement('/cpacs/toolspecific/HybridTool/Outputs/ICEpower')  # [kW]
    M_engine = P_engine / 1.758  # 3.85                        # [kg] Engine dry mass - Valid only for tbprop like atr
    print("----------------->M_engine: %f", M_engine)
else:
    M_engine = 16.5 * numpy.max(T) + 301.4  # [kg] Engine dry mass - Valid for all turbofan engines
D_engine_meanBPR = 1.6597 * ((M_engine * 2.2046) ** 0.4383) * 0.0254 * 1.137  # [m] Engine max outer diameter without
                                                                    # BPR effect - VALID ONLY FOR E-190 CLASS AIRCRAFT
D_engine = D_engine_meanBPR * (1 + 0.3506 * (BPR / 12 - 1))  # [m] Engine max outer diameter with BPR effect -
                                                                    # VALID ONLY FOR E-190 CLASS AIRCRAFT
M_engine = M_engine * (
            1 + 0.3361 * (BPR / 12 - 1))  # [kg] Engine dry mass (function of BPR) - VALID ONLY FOR E-190 CLASS AIRCRAFT
L_engine = 0.1432 * BPR + 3.3677  # [m] Engine overall length

print("D_engine: %f", D_engine)
print("M_engine: %f", M_engine)
print("L_engine: %f", L_engine)

# -----------------------------------------------------------------------------------------------------------------------
## POST-PROCESSING
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedEngineModel') == 0:
    tixi_h.createElement('/cpacs/toolspecific', 'SimplifiedEngineModel')

if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs') == 0:
    tixi_h.createElement('/cpacs/toolspecific/SimplifiedEngineModel', 'Outputs')

# SFC
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs/SFCnew') == 1:
    tixi_h.removeElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs/SFCnew')
tixi_h.addFloatVector('/cpacs/toolspecific/SimplifiedEngineModel/Outputs', 'SFCnew', SFCnew, len(SFCnew), '%f')

# Engine length
# if tixi_h.checkElement('/cpacs/vehicles/engines/engine[1]/geometry/length')==0:
#     tixi_h.addDoubleElement('/cpacs/vehicles/engines/engine[1]/geometry','length',L_engine, '%f')
# else:
#     tixi_h.updateDoubleElement('/cpacs/vehicles/engines/engine[1]/geometry/length',L_engine,'%f')

# Fan diameter
if tixi_h.checkElement('/cpacs/vehicles/engines/engine[1]/geometry') == 0:
    tixi_h.createElement('/cpacs/vehicles/engines/engine[1]', 'geometry')
if tixi_h.checkElement('/cpacs/vehicles/engines/engine[1]/geometry/diameter') == 0:
    tixi_h.addDoubleElement('/cpacs/vehicles/engines/engine[1]/geometry', 'diameter', D_engine, '%f')
else:
    tixi_h.updateDoubleElement('/cpacs/vehicles/engines/engine[1]/geometry/diameter', D_engine, '%f')

# Engine dry mass
if tixi_h.checkElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs/EngineDryMass') == 0:
    tixi_h.addDoubleElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs', 'EngineDryMass', M_engine, '%f')
else:
    tixi_h.updateDoubleElement('/cpacs/toolspecific/SimplifiedEngineModel/Outputs/EngineDryMass', M_engine, '%f')

print("[INFO]: all outputs have been correctly saved")

file_out = INFILE = './ToolOutput/ToolOutput.xml'
tixi_h.saveDocument(file_out)
tixi_h.close()
